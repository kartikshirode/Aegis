"""Make `backend` and `services` importable when running pytest from the repo root."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force LOCAL mode defaults for every test unless a test overrides.
import os

os.environ.setdefault("AEGIS_INDEX_MODE", "LOCAL")
os.environ.setdefault("AEGIS_STORAGE_MODE", "LOCAL")
os.environ.setdefault("AEGIS_KMS_MODE", "LOCAL")
os.environ.setdefault("AEGIS_ANCHOR_MODE", "EAGER")
