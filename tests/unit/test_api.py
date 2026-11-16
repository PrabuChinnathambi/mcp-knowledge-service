import io
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "app" in data
    assert data["docs"] == "/docs"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_workspaces_default():
    response = client.get("/v1/workspaces")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "alice"
    assert isinstance(data["workspaces"], list)
    assert "hr-docs" in data["workspaces"]


def test_list_workspaces_header_override():
    response = client.get("/v1/workspaces", headers={"X-User-ID": "charlie"})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "charlie"
    assert "hr-docs" not in data["workspaces"]


def test_list_models():
    fake_models = [
        {"id": "qwen2.5:7b-instruct", "installed": True},
        {"id": "llama3.2:3b", "installed": True},
        {"id": "deepseek-r1:1.5b", "installed": True},
    ]
    with patch("apps.api.main.llm_client.list_available_models", new=AsyncMock(return_value=fake_models)):
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 3


def test_upload_document_unsupported_extension():
    fake_file = io.BytesIO(b"binary data")
    response = client.post(
        "/v1/documents/upload",
        data={"workspace_id": "hr-docs", "user_id": "alice"},
        files={"file": ("unsupported.exe", fake_file, "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_document_unauthorized_user():
    fake_file = io.BytesIO(b"# Sample Header\nSome markdown text.")
    # Charlie does not have write access to hr-docs
    response = client.post(
        "/v1/documents/upload",
        data={"workspace_id": "hr-docs", "user_id": "charlie"},
        files={"file": ("sample.md", fake_file, "text/markdown")},
    )
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


def test_upload_document_success():
    fake_file = io.BytesIO(b"# Policy\nEmployee guidelines here.")
    mock_result = {
        "document_id": "doc-uuid-1",
        "source_uri": "workspace://hr-docs/policy.md",
        "status": "indexed",
        "chunks_count": 1,
        "version": 1,
    }
    with patch("apps.api.main.ingest_document_file", new=AsyncMock(return_value=mock_result)):
        response = client.post(
            "/v1/documents/upload",
            data={"workspace_id": "hr-docs", "user_id": "alice"},
            files={"file": ("policy.md", fake_file, "text/markdown")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "indexed"


def test_ask_knowledge():
    mock_response = {
        "trace_id": "tr-12345",
        "status": "answered",
        "model": "llama3.2:3b",
        "answer": "20 days annual vacation.",
        "citations": [{"chunk_id": "chunk-1", "title": "HR"}],
    }
    with patch("apps.api.main.ask_docs", new=AsyncMock(return_value=mock_response)):
        response = client.post(
            "/v1/harness/ask",
            json={
                "workspace_id": "hr-docs",
                "question": "How many days off?",
                "user_id": "alice",
                "model": "llama3.2:3b",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "answered"
        assert data["model"] == "llama3.2:3b"
        assert data["answer"] == "20 days annual vacation."


def test_search_retrieval_unauthorized():
    # Charlie does not have access to hr-docs
    response = client.post(
        "/v1/retrieval/search",
        json={"workspace_id": "hr-docs", "query": "vacation", "user_id": "charlie"},
    )
    assert response.status_code == 403
