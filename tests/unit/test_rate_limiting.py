"""
Unit tests for Phase 10.4 — SlowAPI Rate Limiting.

Strategy:
- Structural test: confirms the limiter is wired to app.state.
- Breach tests: exhaust each endpoint's budget then assert 429.
  Each test uses its own isolated limiter reset via the autouse conftest fixture,
  so there is no cross-test counter bleed.
"""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from slowapi import Limiter

from apps.api.main import app
from packages.harness.auth import create_access_token

client = TestClient(app)


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_token(username: str = "alice", role: str = "admin", workspaces: list[str] | None = None) -> str:
    """Create a JWT directly — does NOT call the /v1/auth/token endpoint."""
    return create_access_token(
        data={
            "sub": username,
            "role": role,
            "workspaces": workspaces or ["hr-docs", "api-docs", "engineering"],
        },
        expires_delta=timedelta(minutes=60),
    )


# ── Structural ────────────────────────────────────────────────────────────────

def test_rate_limiter_is_attached():
    """SlowAPI limiter must be registered on the app state."""
    assert hasattr(app.state, "limiter")
    assert isinstance(app.state.limiter, Limiter)


# ── Login endpoint: 10/minute ─────────────────────────────────────────────────

def test_login_rate_limit_blocks_on_11th():
    """After 10 logins the 11th must receive 429 with correct body/header."""
    for _ in range(10):
        client.post("/v1/auth/token", json={"username": "alice", "password": "password123"})
    resp = client.post("/v1/auth/token", json={"username": "alice", "password": "password123"})
    assert resp.status_code == 429
    assert "rate limit" in resp.json()["detail"].lower()
    assert "Retry-After" in resp.headers


# ── Ask endpoint: 30/minute ───────────────────────────────────────────────────

def test_ask_rate_limit_blocks_on_31st():
    """After 30 asks the 31st must receive 429."""
    token = _make_token()
    mock_result = {"trace_id": "t", "status": "answered", "answer": "ok", "citations": []}
    with patch("apps.api.main.ask_docs", new=AsyncMock(return_value=mock_result)):
        for _ in range(30):
            client.post(
                "/v1/harness/ask",
                headers={"Authorization": f"Bearer {token}"},
                json={"workspace_id": "hr-docs", "question": "Q"},
            )
        resp = client.post(
            "/v1/harness/ask",
            headers={"Authorization": f"Bearer {token}"},
            json={"workspace_id": "hr-docs", "question": "over limit"},
        )
    assert resp.status_code == 429


# ── Upload endpoint: 20/minute ────────────────────────────────────────────────

def test_upload_rate_limit_blocks_on_21st():
    """After 20 uploads the 21st must receive 429."""
    token = _make_token()
    mock_result = {"document_id": "d", "source_uri": "ws://hr/f.md", "status": "indexed", "chunks_count": 1, "version": 1}
    with patch("apps.api.main.ingest_document_file", new=AsyncMock(return_value=mock_result)):
        for _ in range(20):
            client.post(
                "/v1/documents/upload",
                headers={"Authorization": f"Bearer {token}"},
                data={"workspace_id": "hr-docs"},
                files={"file": ("d.md", b"# T", "text/markdown")},
            )
        resp = client.post(
            "/v1/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            data={"workspace_id": "hr-docs"},
            files={"file": ("over.md", b"# X", "text/markdown")},
        )
    assert resp.status_code == 429


# ── Search endpoint: 60/minute ────────────────────────────────────────────────

def test_search_rate_limit_blocks_on_61st():
    """After 60 searches the 61st must receive 429."""
    token = _make_token()
    mock_retrieval = type("R", (), {"chunks": [], "top_vector_score": 0.0, "trace": {}})()
    with patch("apps.api.main.hybrid_retrieve", new=AsyncMock(return_value=mock_retrieval)):
        for _ in range(60):
            client.post(
                "/v1/retrieval/search",
                headers={"Authorization": f"Bearer {token}"},
                json={"workspace_id": "hr-docs", "query": "q"},
            )
        resp = client.post(
            "/v1/retrieval/search",
            headers={"Authorization": f"Bearer {token}"},
            json={"workspace_id": "hr-docs", "query": "over limit"},
        )
    assert resp.status_code == 429
