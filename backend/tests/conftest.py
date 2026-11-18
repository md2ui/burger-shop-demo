import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


import pytest  # noqa: E402 -- after the path above
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def api(monkeypatch):
    """The backend's app with a fresh shop and no conversations."""
    import main
    from shop import Shop

    monkeypatch.setattr(main, "shop", Shop())
    monkeypatch.setattr(main, "NOTES", main.AppNotes())
    monkeypatch.setattr(main, "CONVERSATIONS", {})
    monkeypatch.setattr(main, "AGENT_SESSIONS", set())
    with TestClient(main.app) as client:
        yield client
