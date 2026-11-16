import io
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_upload_document_async():
    fake_file = io.BytesIO(b"# Architecture\nDesign guidelines.")
    mock_task = MagicMock()
    mock_task.id = "celery-task-12345"

    with patch("apps.worker.tasks.process_document_task.delay", return_value=mock_task):
        response = client.post(
            "/v1/documents/upload/async",
            data={"workspace_id": "engineering", "user_id": "alice"},
            files={"file": ("architecture.md", fake_file, "text/markdown")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["task_id"] == "celery-task-12345"
        assert data["filename"] == "architecture.md"


def test_get_task_status_pending():
    mock_async_res = MagicMock()
    mock_async_res.status = "PENDING"
    mock_async_res.ready.return_value = False

    with patch("apps.worker.celery_app.celery_app.AsyncResult", return_value=mock_async_res):
        response = client.get("/v1/tasks/task-999")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-999"
        assert data["status"] == "PENDING"
        assert data["ready"] is False


def test_get_task_status_success():
    mock_async_res = MagicMock()
    mock_async_res.status = "SUCCESS"
    mock_async_res.ready.return_value = True
    mock_async_res.successful.return_value = True
    mock_async_res.result = {"document_id": "doc-1", "status": "indexed", "chunks_count": 3}

    with patch("apps.worker.celery_app.celery_app.AsyncResult", return_value=mock_async_res):
        response = client.get("/v1/tasks/task-success-123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["ready"] is True
        assert data["successful"] is True
        assert data["result"]["chunks_count"] == 3
