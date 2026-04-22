"""Thin wrapper around Vertex AI Vector Search.

Phase-1 reality: Vertex AI Vector Search IAM + deployed-index setup can block
a 48-hour sprint. This module exposes the two calls the detector needs and has
an in-memory FAISS-style fallback so we can run end-to-end locally while the
GCP-side infra is being wired. `index_mode=GCP` is the submission path;
`index_mode=LOCAL` is the dev-loop and mock-demo fallback.
"""

from __future__ import annotations

import math
import os
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Hit:
    clip_id: str
    cosine: float


_LOCK = threading.Lock()
_LOCAL_INDEX: dict[str, np.ndarray] = {}  # clip_id -> (N, D) frame embeddings
_LOCAL_PHASHES: dict[str, list[str]] = {}


def _mode() -> str:
    return os.environ.get("AEGIS_INDEX_MODE", "LOCAL")


def upsert_clip(clip_id: str, frame_embeddings: list[list[float]], frame_phashes: list[str]) -> None:
    if _mode() == "LOCAL":
        with _LOCK:
            _LOCAL_INDEX[clip_id] = np.asarray(frame_embeddings, dtype=np.float32)
            _LOCAL_PHASHES[clip_id] = frame_phashes
        return
    _upsert_gcp(clip_id, frame_embeddings, frame_phashes)


def query_top_k(candidate_embeddings: list[list[float]], k: int = 5) -> list[Hit]:
    if _mode() == "LOCAL":
        return _query_local(candidate_embeddings, k)
    return _query_gcp(candidate_embeddings, k)


def get_clip_phashes(clip_id: str) -> list[str]:
    if _mode() == "LOCAL":
        return _LOCAL_PHASHES.get(clip_id, [])
    return _get_phashes_gcp(clip_id)


# ---------- LOCAL (FAISS-style) ----------

def _query_local(candidate_embeddings: list[list[float]], k: int) -> list[Hit]:
    if not _LOCAL_INDEX:
        return []
    q = np.asarray(candidate_embeddings, dtype=np.float32)
    q = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-9)
    scores: list[tuple[str, float]] = []
    for clip_id, emb in _LOCAL_INDEX.items():
        e = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)
        sim = (q @ e.T).max()  # best frame-to-frame
        scores.append((clip_id, float(sim)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [Hit(clip_id=cid, cosine=s) for cid, s in scores[:k]]


# ---------- GCP (Vertex AI Vector Search) ----------

def _upsert_gcp(clip_id: str, frame_embeddings: list[list[float]], frame_phashes: list[str]) -> None:
    """Upsert one datapoint per frame, prefixed by clip_id.

    Firestore holds the phash list under clips/{clip_id}.phash_per_frame.
    """
    from google.cloud import aiplatform_v1

    index_id = os.environ["VERTEX_VECTOR_INDEX_ID"]
    project = os.environ["VERTEX_AI_PROJECT"]
    location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")

    client = aiplatform_v1.IndexServiceClient(
        client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
    )

    datapoints = [
        aiplatform_v1.IndexDatapoint(
            datapoint_id=f"{clip_id}:{i}",
            feature_vector=vec,
        )
        for i, vec in enumerate(frame_embeddings)
    ]
    client.upsert_datapoints(
        request=aiplatform_v1.UpsertDatapointsRequest(
            index=f"projects/{project}/locations/{location}/indexes/{index_id}",
            datapoints=datapoints,
        )
    )


def _query_gcp(candidate_embeddings: list[list[float]], k: int) -> list[Hit]:
    from google.cloud import aiplatform_v1

    endpoint_id = os.environ["VERTEX_VECTOR_ENDPOINT_ID"]
    deployed_index = os.environ["VERTEX_VECTOR_DEPLOYED_INDEX_ID"]
    project = os.environ["VERTEX_AI_PROJECT"]
    location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")

    client = aiplatform_v1.MatchServiceClient(
        client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
    )

    best_per_clip: dict[str, float] = {}
    for vec in candidate_embeddings:
        resp = client.find_neighbors(
            request=aiplatform_v1.FindNeighborsRequest(
                index_endpoint=f"projects/{project}/locations/{location}/indexEndpoints/{endpoint_id}",
                deployed_index_id=deployed_index,
                queries=[
                    aiplatform_v1.FindNeighborsRequest.Query(
                        datapoint=aiplatform_v1.IndexDatapoint(feature_vector=vec),
                        neighbor_count=k,
                    )
                ],
            )
        )
        for nn in resp.nearest_neighbors[0].neighbors:
            clip_id = nn.datapoint.datapoint_id.split(":", 1)[0]
            cosine = _distance_to_cosine(nn.distance)
            if cosine > best_per_clip.get(clip_id, -1.0):
                best_per_clip[clip_id] = cosine

    return [
        Hit(clip_id=cid, cosine=cos)
        for cid, cos in sorted(best_per_clip.items(), key=lambda x: x[1], reverse=True)[:k]
    ]


def _distance_to_cosine(distance: float) -> float:
    """Vector Search returns cosine distance by default when the index is configured as such."""
    return 1.0 - distance


def _get_phashes_gcp(clip_id: str) -> list[str]:
    from google.cloud import firestore

    client = firestore.Client()
    doc = client.collection("clips").document(clip_id).get()
    return list(doc.to_dict().get("phash_per_frame", [])) if doc.exists else []
