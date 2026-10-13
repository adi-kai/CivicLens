"""Shared test setup. Import this before any civiclens module.

civiclens/config.py reads .streamlit/secrets.toml at import time, and CI has no secrets
file, so any module that imports it (data/civic.py, data/ai.py, ...) would fail to
import. Tests get fake keys instead, and every network call is mocked.
"""
import os
import sys
import types
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

FAKE_GEMINI_KEY = "SECRETKEY"
sys.modules["civiclens.config"] = types.SimpleNamespace(
    GOOGLE_KEY="google", OPENSTATES_KEY="openstates", GEMINI_KEY=FAKE_GEMINI_KEY,
    GROQ_KEY="groq", TAVILY_KEY="tavily",
)


def response(status: int = 200, payload=None, text: str = ""):
    """A stand-in for a requests.Response."""
    return mock.Mock(status_code=status, json=lambda: payload, text=text)
