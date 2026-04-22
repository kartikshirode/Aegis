"""Unit tests for the Merkle log + local HMAC anchor.

These tests are fast, GCP-free, and prove the inclusion-proof + verify-anchor
contract that /verify depends on.
"""

from __future__ import annotations

import os

from backend.provenance import merkle


def test_single_leaf_tree_root_equals_leaf():
    leaf = merkle.build_leaf_for_clip("clip-1", {"x": 1})
    tree = merkle.MerkleTree([leaf])
    assert tree.root == leaf.leaf_hex


def test_inclusion_proof_round_trip_for_many_leaves():
    leaves = [merkle.build_leaf_for_clip(f"clip-{i}", {"i": i}) for i in range(7)]
    tree = merkle.MerkleTree(leaves)
    for l in leaves:
        proof = tree.inclusion_proof(l.leaf_hex)
        # mypy: proof entries are tuples of ("L"|"R", hex)
        assert merkle.verify_inclusion(l.leaf_hex, proof, tree.root)


def test_local_hmac_anchor_round_trip():
    os.environ["AEGIS_KMS_MODE"] = "LOCAL"
    os.environ["AEGIS_LOCAL_HMAC_KEY"] = "test-key-1"
    leaves = [merkle.build_leaf_for_notice(f"notice-{i}", {"i": i}) for i in range(3)]
    receipt = merkle.anchor_batch(leaves)
    assert merkle.verify_anchor(
        receipt["merkle_root_hex"],
        receipt["kms_key_version"],
        receipt["kms_signature_b64"],
    )


def test_anchor_rejects_empty_batch():
    try:
        merkle.anchor_batch([])
    except ValueError:
        return
    raise AssertionError("expected ValueError for empty batch")


def test_deterministic_ordering_of_leaves():
    # Same input set in any order should produce the same tree + root.
    leaves = [merkle.build_leaf_for_clip(f"c-{i}", {"i": i}) for i in range(5)]
    root_a = merkle.MerkleTree(leaves).root
    root_b = merkle.MerkleTree(list(reversed(leaves))).root
    assert root_a == root_b
