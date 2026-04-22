"""Tamper-evident daily Merkle log with Cloud KMS anchor.

Every provenance claim (ingest) and every filed takedown becomes one leaf.
At end of day (or on demand in tests/demos), we build a Merkle tree, compute
the root, and sign the root with Cloud KMS. The signed root is the public
receipt published at GET /verify/{detection_id}.

Leaf shape:
    leaf = SHA-256(kind || ":" || id || ":" || canonical_json_bytes)

where `kind` is one of {"clip", "verdict", "notice"} and canonical_json_bytes
is the UTF-8 encoding of a JSON object emitted with sort_keys=True and
separators=(",", ":").

Tree construction (deterministic):
- Leaves are ordered by leaf hex (lexicographic).
- Internal node = SHA-256(left || right). Odd layers duplicate the last node.

Verification:
- Given a leaf and an inclusion proof (sibling hashes up to the root),
  anyone can reconstruct the root and compare against the published, signed root.
- The signature is verified against the public half of the Cloud KMS key,
  which we expose at GET /verify/kms-pubkey.

LOCAL mode: a deterministic HMAC with a dev key stands in for KMS sign/verify
so tests run without GCP. Never used in submission.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

LeafKind = Literal["clip", "verdict", "notice"]


@dataclass(frozen=True)
class Leaf:
    id: str
    kind: LeafKind
    payload: dict
    leaf_hex: str


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _leaf_hash(kind: LeafKind, id_: str, payload: dict) -> str:
    m = hashlib.sha256()
    m.update(kind.encode("utf-8"))
    m.update(b":")
    m.update(id_.encode("utf-8"))
    m.update(b":")
    m.update(_canonical(payload))
    return m.hexdigest()


def build_leaf_for_clip(clip_id: str, clip_payload: dict) -> Leaf:
    return Leaf(id=clip_id, kind="clip", payload=clip_payload,
                leaf_hex=_leaf_hash("clip", clip_id, clip_payload))


def build_leaf_for_verdict(detection_id: str, verdict_payload: dict) -> Leaf:
    return Leaf(id=detection_id, kind="verdict", payload=verdict_payload,
                leaf_hex=_leaf_hash("verdict", detection_id, verdict_payload))


def build_leaf_for_notice(notice_id: str, notice_payload: dict) -> Leaf:
    return Leaf(id=notice_id, kind="notice", payload=notice_payload,
                leaf_hex=_leaf_hash("notice", notice_id, notice_payload))


# ---------- Merkle tree ----------

class MerkleTree:
    def __init__(self, leaves: list[Leaf]) -> None:
        if not leaves:
            raise ValueError("MerkleTree needs ≥ 1 leaf")
        self.leaves = sorted(leaves, key=lambda l: l.leaf_hex)
        self.levels: list[list[str]] = [[l.leaf_hex for l in self.leaves]]
        while len(self.levels[-1]) > 1:
            prev = self.levels[-1]
            nxt: list[str] = []
            for i in range(0, len(prev), 2):
                left = prev[i]
                right = prev[i + 1] if i + 1 < len(prev) else prev[i]
                nxt.append(_h_concat(left, right))
            self.levels.append(nxt)

    @property
    def root(self) -> str:
        return self.levels[-1][0]

    def inclusion_proof(self, leaf_hex: str) -> list[tuple[Literal["L", "R"], str]]:
        """Return list of (side, sibling_hex) from leaf level up to the root."""
        idx = self.levels[0].index(leaf_hex)
        proof: list[tuple[Literal["L", "R"], str]] = []
        for level in self.levels[:-1]:
            if idx % 2 == 0:
                sib_idx = idx + 1 if idx + 1 < len(level) else idx
                proof.append(("R", level[sib_idx]))
            else:
                proof.append(("L", level[idx - 1]))
            idx //= 2
        return proof


def verify_inclusion(leaf_hex: str, proof: list[tuple[str, str]], root: str) -> bool:
    acc = leaf_hex
    for side, sib in proof:
        acc = _h_concat(sib, acc) if side == "L" else _h_concat(acc, sib)
    return acc == root


def _h_concat(left: str, right: str) -> str:
    m = hashlib.sha256()
    m.update(bytes.fromhex(left))
    m.update(bytes.fromhex(right))
    return m.hexdigest()


# ---------- Cloud KMS anchor ----------

def anchor_root(merkle_root_hex: str) -> tuple[str, str]:
    """Sign the root. Returns (kms_key_version, kms_signature_b64).

    LOCAL fallback: HMAC-SHA-256 with a deterministic dev key. Not cryptographically
    sound as a public-signature scheme, but sufficient for the integration test.
    GCP path uses Cloud KMS asymmetric sign.
    """
    mode = os.environ.get("AEGIS_KMS_MODE", "LOCAL")
    if mode == "LOCAL":
        key = os.environ.get("AEGIS_LOCAL_HMAC_KEY", "aegis-local-dev-key").encode()
        sig = hmac.new(key, bytes.fromhex(merkle_root_hex), hashlib.sha256).digest()
        return "local-hmac-v1", base64.b64encode(sig).decode("ascii")
    return _anchor_gcp(merkle_root_hex)


def verify_anchor(merkle_root_hex: str, kms_key_version: str, kms_signature_b64: str) -> bool:
    mode = os.environ.get("AEGIS_KMS_MODE", "LOCAL")
    if mode == "LOCAL":
        key = os.environ.get("AEGIS_LOCAL_HMAC_KEY", "aegis-local-dev-key").encode()
        expected = hmac.new(key, bytes.fromhex(merkle_root_hex), hashlib.sha256).digest()
        return hmac.compare_digest(expected, base64.b64decode(kms_signature_b64))
    return _verify_gcp(merkle_root_hex, kms_key_version, kms_signature_b64)


def _anchor_gcp(merkle_root_hex: str) -> tuple[str, str]:
    from google.cloud import kms

    key_name = os.environ["AEGIS_KMS_KEY"]  # e.g. projects/.../cryptoKeyVersions/1
    client = kms.KeyManagementServiceClient()
    digest = {"sha256": bytes.fromhex(merkle_root_hex)}
    resp = client.asymmetric_sign(request={"name": key_name, "digest": digest})
    return key_name.rsplit("/", 2)[-1] if False else key_name, base64.b64encode(resp.signature).decode("ascii")


def _verify_gcp(merkle_root_hex: str, kms_key_version: str, kms_signature_b64: str) -> bool:
    """Verify via Cloud KMS public key.

    For Phase-1 this is a best-effort: the public key is fetched and used to
    verify an RSA-SSA-PSS signature over the SHA-256 of the root. If the
    `cryptography` library is not available we return False rather than pretend.
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from google.cloud import kms
    except ImportError:
        return False

    client = kms.KeyManagementServiceClient()
    pub = client.get_public_key(request={"name": kms_key_version})
    pubkey = serialization.load_pem_public_key(pub.pem.encode("utf-8"))
    try:
        pubkey.verify(  # type: ignore[call-arg]
            base64.b64decode(kms_signature_b64),
            bytes.fromhex(merkle_root_hex),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


# ---------- Daily anchor job ----------

def anchor_batch(leaves: list[Leaf]) -> dict:
    """Build a tree, sign the root, return a receipt dict ready to persist."""
    if not leaves:
        raise ValueError("anchor_batch needs ≥ 1 leaf")
    tree = MerkleTree(leaves)
    key_version, sig_b64 = anchor_root(tree.root)
    today = datetime.now(timezone.utc).date().isoformat()
    receipt_id = hashlib.sha256(f"{today}:{tree.root}".encode("utf-8")).hexdigest()[:24]
    return {
        "receipt_id":       receipt_id,
        "date":             today,
        "merkle_root_hex":  tree.root,
        "kms_key_version":  key_version,
        "kms_signature_b64": sig_b64,
        "leaf_count":       len(tree.leaves),
        "first_leaf_id":    tree.leaves[0].id,
        "last_leaf_id":     tree.leaves[-1].id,
    }
