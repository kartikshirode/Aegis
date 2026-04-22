"""Ingestion: sign + fingerprint + index a rights-holder's original clip.

Pipeline for POST /ingest:
  1. Accept upload, persist to Cloud Storage.
  2. Extract 8 keyframes with ffmpeg.
  3. Compute pHash per keyframe.
  4. Compute Vertex AI multimodal embedding per keyframe.
  5. Upsert embeddings into Vertex AI Vector Search.
  6. Write a C2PA manifest via c2patool and sign with Cloud KMS.
  7. Persist the Clip record to Firestore.

Steps 4-6 require live GCP credentials; Phase 1 fallbacks noted inline.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image

from backend.schema import Clip, RightsHolderContact

KEYFRAME_POSITIONS = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]


def extract_keyframes(video_path: Path, out_dir: Path) -> list[Path]:
    """Extract 8 keyframes at fixed proportional positions via ffmpeg.

    Uses ffprobe to read duration, then emits one frame per position. Deterministic.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = _ffprobe_duration(video_path)
    frames: list[Path] = []
    for i, pos in enumerate(KEYFRAME_POSITIONS):
        t = pos * duration
        out = out_dir / f"frame_{i:02d}.jpg"
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-y", "-loglevel", "error",
                "-ss", f"{t:.3f}", "-i", str(video_path),
                "-frames:v", "1", "-q:v", "2", str(out),
            ],
            check=True,
        )
        frames.append(out)
    return frames


def _ffprobe_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def compute_phashes(frames: list[Path]) -> list[str]:
    hashes: list[str] = []
    for f in frames:
        with Image.open(f) as img:
            hashes.append(str(imagehash.phash(img)))
    return hashes


def compute_embeddings(frames: list[Path]) -> list[list[float]]:
    """Vertex AI multimodal embeddings per frame.

    Phase-1 fallback: when VERTEX_AI_PROJECT is unset, returns a deterministic
    mock 1408-dim vector *derived from the frame's perceptual hash* so that
    visually similar frames produce similar vectors. This keeps the LOCAL
    integration test and the LOCAL benchmark honest — a re-encode of the same
    frame yields a pHash close in Hamming distance, which in turn yields a
    high cosine similarity.

    Numbers produced in LOCAL mode are still NOT substitutes for real
    Vertex AI embedding numbers in a submission. See docs/benchmarks.md:
    the real-numbers run requires VERTEX_AI_PROJECT.
    """
    project = os.environ.get("VERTEX_AI_PROJECT")
    if not project:
        return [_mock_embedding(f) for f in frames]

    # Real path. Imports are local to avoid a hard dep when running in mock mode.
    from vertexai.vision_models import Image as VAIImage, MultiModalEmbeddingModel

    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
    vectors: list[list[float]] = []
    for f in frames:
        image = VAIImage.load_from_file(str(f))
        emb = model.get_embeddings(image=image, dimension=1408)
        vectors.append(list(emb.image_embedding))
    return vectors


def _mock_embedding(frame: Path, dim: int = 1408) -> list[float]:
    """Similarity-preserving mock.

    Strategy: compute a 64-bit pHash (phash) and a 64-bit difference-hash (dhash).
    Concatenate to get 128 bits per frame. Map each bit to ±1, then tile to
    `dim`. Two frames that differ in k bits produce vectors whose cosine
    similarity ≈ 1 − 2k/128 — so a re-encode that shifts ~4 bits yields ≈ 0.94,
    a mirror that shifts ~30 bits yields ≈ 0.53, and an unrelated image that
    differs in ~64 bits yields ≈ 0. This tracks real pHash behaviour and
    therefore exercises the Stage-1 escalation path honestly in LOCAL mode.
    """
    with Image.open(frame) as img:
        p_bits = imagehash.phash(img).hash.flatten()
        d_bits = imagehash.dhash(img).hash.flatten()
    bits = np.concatenate([p_bits.astype(np.int8), d_bits.astype(np.int8)])  # shape (128,)
    signed = (bits * 2 - 1).astype(np.float32)                               # {+1, -1}
    # Note on dimensionality: the effective information content is 128 bits
    # (64 pHash + 64 dHash). Tiling to `dim` is a no-op for cosine similarity
    # — we do it only so the mock matches the declared Vertex dimension and
    # the index code can be wired identically in LOCAL and GCP modes.
    reps = (dim + signed.size - 1) // signed.size
    tiled = np.tile(signed, reps)[:dim]
    norm = float(np.linalg.norm(tiled)) or 1.0
    return (tiled / norm).tolist()


def sign_c2pa_manifest(
    video_path: Path,
    *,
    title: str,
    rights_holder: str,
    event: str,
    athletes: list[str],
    manifest_out: Path,
) -> None:
    """Sign a C2PA manifest using the c2patool binary.

    Phase-1 fallback: if c2patool is unavailable, writes an unsigned manifest JSON
    with a prominent `unsigned: true` marker. The signed path is the submission path.
    """
    manifest = {
        "claim_generator": "aegis/0.1",
        "title": title,
        "format": "video/mp4",
        "assertions": [
            {"label": "aegis.sport.v1", "data": {
                "rights_holder": rights_holder,
                "event": event,
                "athletes": athletes,
            }},
            {"label": "stds.schema-org.CreativeWork", "data": {
                "@context": "https://schema.org",
                "@type": "CreativeWork",
                "author": rights_holder,
            }},
        ],
    }
    manifest_out.parent.mkdir(parents=True, exist_ok=True)

    import json

    if not _has_c2patool():
        manifest_out.write_text(json.dumps({**manifest, "unsigned": True}, indent=2))
        return

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(manifest, tf)
        manifest_path = tf.name

    subprocess.run(
        ["c2patool", str(video_path), "--manifest", manifest_path, "--output", str(manifest_out)],
        check=True,
    )


def _has_c2patool() -> bool:
    try:
        subprocess.run(["c2patool", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def ingest(
    video_path: Path,
    *,
    title: str,
    sport: str,
    event: str,
    rights_holder: str,
    rights_holder_contact: RightsHolderContact,
    athletes: list[str],
    workdir: Path,
) -> tuple[Clip, list[list[float]]]:
    """Full ingest: extract keyframes, fingerprint, embed, sign.

    Returns (Clip, embeddings). The caller is responsible for upserting the
    embeddings into the vector index — this function does not touch the index,
    because production Vector Search upserts are an I/O + cost concern the API
    layer should own.
    """
    clip_id = str(uuid.uuid4())
    frames = extract_keyframes(video_path, workdir / clip_id / "frames")
    phashes = compute_phashes(frames)
    embeddings = compute_embeddings(frames)

    manifest_out = workdir / clip_id / "manifest.c2pa.json"
    sign_c2pa_manifest(
        video_path,
        title=title, rights_holder=rights_holder, event=event,
        athletes=athletes, manifest_out=manifest_out,
    )

    clip = Clip(
        clip_id=clip_id,
        title=title,
        sport=sport,
        event=event,
        first_published=datetime.now(timezone.utc),
        rights_holder=rights_holder,
        rights_holder_contact=rights_holder_contact,
        athletes=athletes,
        c2pa_manifest_url=f"file://{manifest_out}",  # swap for https URL in prod
        storage_uri=str(video_path),
        phash_per_frame=phashes,
        embedding_index_id=clip_id,
    )
    return clip, embeddings
