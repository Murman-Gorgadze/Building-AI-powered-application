import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.pop("OPENROUTER_API_KEY", None)   # tests never reach a real model
os.environ.pop("FANRESERVE_OPERATOR", None)  # the MCP door starts signed out unless a test signs in


@pytest.fixture(autouse=True)
def usage_log(tmp_path, monkeypatch):
    """Every test writes usage to a temp file, never to the committed logs/usage.jsonl."""
    path = tmp_path / "usage.jsonl"
    monkeypatch.setenv("FANRESERVE_USAGE_LOG", str(path))
    return path


@pytest.fixture(autouse=True)
def tool_log(tmp_path, monkeypatch):
    """Tool calls log to a temp file, never to the committed logs/tools.jsonl."""
    path = tmp_path / "tools.jsonl"
    monkeypatch.setenv("FANRESERVE_TOOL_LOG", str(path))
    return path
