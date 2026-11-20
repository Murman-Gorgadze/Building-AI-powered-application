import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.pop("OPENROUTER_API_KEY", None)   # tests never reach a real model


@pytest.fixture(autouse=True)
def usage_log(tmp_path, monkeypatch):
    """Every test writes usage to a temp file, never to the committed logs/usage.jsonl."""
    path = tmp_path / "usage.jsonl"
    monkeypatch.setenv("FANRESERVE_USAGE_LOG", str(path))
    return path
