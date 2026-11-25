from datetime import timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from apps.api.main import app
from packages.harness.auth import create_access_token

client = TestClient(app)


def test_login_success():
    response = client.post(
        "/v1/auth/token",
        json={"username": "alice", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == "alice"
    assert data["role"] == "admin"
    assert "hr-docs" in data["workspaces"]


def test_login_invalid_password():
    response = client.post(
        "/v1/auth/token",
        json={"username": "alice", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_access_workspaces_with_jwt():
    # Login as bob
    login_resp = client.post(
        "/v1/auth/token",
        json={"username": "bob", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # Request workspaces with Bearer token
    response = client.get(
        "/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "bob"
    assert data["workspaces"] == ["api-docs"]


def test_access_workspaces_expired_token():
    # Create an already-expired token (-5 minutes)
    expired_token = create_access_token(
        data={"sub": "alice", "role": "admin", "workspaces": ["hr-docs"]},
        expires_delta=timedelta(minutes=-5),
    )

    response = client.get(
        "/v1/workspaces",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_access_workspaces_tampered_token():
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.invalid_signature"
    response = client.get(
        "/v1/workspaces",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401


def test_upload_with_editor_jwt():
    # Charlie is an editor in engineering
    login_resp = client.post(
        "/v1/auth/token",
        json={"username": "charlie", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    mock_result = {
        "document_id": "doc-uuid-99",
        "source_uri": "workspace://engineering/doc.md",
        "status": "indexed",
        "chunks_count": 1,
        "version": 1,
    }

    with patch("apps.api.main.ingest_document_file", new=AsyncMock(return_value=mock_result)):
        response = client.post(
            "/v1/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            data={"workspace_id": "engineering"},
            files={"file": ("doc.md", b"# Eng Guidelines", "text/markdown")},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"


def test_upload_with_viewer_jwt_denied():
    # Bob is only a viewer in api-docs
    login_resp = client.post(
        "/v1/auth/token",
        json={"username": "bob", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"workspace_id": "api-docs"},
        files={"file": ("doc.md", b"# Malicious write", "text/markdown")},
    )
    assert response.status_code == 403
    assert "lacks write permissions" in response.json()["detail"]
