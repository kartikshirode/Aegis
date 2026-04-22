"""Make `backend` and `services` importable when running pytest from the repo root."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True, scope="function")
def _force_local_mode(monkeypatch):
    """Override (not setdefault) Aegis env vars to LOCAL for every test.

    setdefault leaks a developer's local GCP-mode env into the test run, which
    would silently talk to real Vertex. monkeypatch.setenv is explicit and
    reversible on teardown.
    """
    monkeypatch.setenv("AEGIS_INDEX_MODE", "LOCAL")
    monkeypatch.setenv("AEGIS_STORAGE_MODE", "LOCAL")
    monkeypatch.setenv("AEGIS_KMS_MODE", "LOCAL")
    monkeypatch.setenv("AEGIS_ANCHOR_MODE", "EAGER")
    monkeypatch.delenv("VERTEX_AI_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    # AEGIS_DEMO_MODE must not leak in — the caption-based mock-verdict rule
    # is demo-only and would poison test assertions that care about verdict type.
    monkeypatch.delenv("AEGIS_DEMO_MODE", raising=False)
