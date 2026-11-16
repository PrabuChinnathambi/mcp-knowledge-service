import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from packages.core.config import get_settings
from packages.harness.agent import ask_docs
from packages.harness.auth import (
    USER_DIRECTORY,
    AccessDeniedError,
    assert_can_write,
    assert_workspace_access,
)
from packages.infrastructure.llm import llm_client
from packages.ingestion.pipeline import ingest_document_file
from packages.observability.logger import logger
from packages.retrieval.hybrid import hybrid_retrieve

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("FastAPI service starting up", app_name=settings.APP_NAME, env=settings.ENVIRONMENT)
    yield
    logger.info("FastAPI service shutting down")


app = FastAPI(
    title=f"{settings.APP_NAME} REST Gateway",
    description="Enterprise Knowledge Retrieval, Document Ingestion, and Multi-LLM Agent Grounding REST API.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# Request / Response Schemas
# ============================================================================


class WorkspacesResponse(BaseModel):
    user_id: str
    workspaces: list[str]


class AskRequest(BaseModel):
    workspace_id: str = Field(..., description="Target workspace ID (e.g. 'hr-docs', 'api-docs')")
    question: str = Field(..., description="The query to answer grounded strictly in workspace documentation.")
    user_id: str = Field(default="alice", description="User ID for RBAC workspace access enforcement.")
    model: str | None = Field(
        default=None,
        description="Optional local LLM ('qwen2.5:7b-instruct', 'llama3.2:3b', 'deepseek-r1:1.5b'). Defaults to configured model.",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of context chunks to retrieve.")


class SearchRequest(BaseModel):
    workspace_id: str = Field(..., description="Target workspace ID")
    query: str = Field(..., description="Semantic or keyword search query")
    user_id: str = Field(default="alice", description="User ID for RBAC")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of ranked results to return")


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    return {
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/v1/workspaces", response_model=WorkspacesResponse, tags=["Workspaces"])
async def list_workspaces(
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> WorkspacesResponse:
    """List knowledge workspaces accessible to the user."""
    user_id = x_user_id or settings.MCP_USER_ID
    user_record = USER_DIRECTORY.get(user_id, {"workspaces": []})
    return WorkspacesResponse(user_id=user_id, workspaces=user_record["workspaces"])


@app.get("/v1/models", tags=["LLM Models"])
async def list_models() -> dict[str, list[dict]]:
    """List available local offline LLMs and their hardware / installation status."""
    models = await llm_client.list_available_models()
    return {"models": models}


SUPPORTED_UPLOAD_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".xlsx"}


@app.post("/v1/documents/upload", tags=["Ingestion"])
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (.md, .txt, .pdf, .docx, .xlsx)"),  # noqa: B008
    workspace_id: str = Form(..., description="Target knowledge workspace"),
    user_id: str = Form(default="alice", description="User ID performing upload (must have write permission)"),
) -> dict:
    """
    Upload and synchronously index a document into a workspace.
    Performs PII redaction, hierarchical section chunking, 768-dim GPU embedding, and delta re-indexing.
    """
    try:
        assert_can_write(user_id, workspace_id)
    except AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))}",
        )

    try:
        content = await file.read()
        logger.info(
            "REST document upload received",
            filename=file.filename,
            workspace=workspace_id,
            user_id=user_id,
            bytes=len(content),
        )

        result = await ingest_document_file(
            file_path=file.filename or "uploaded_file.txt",
            workspace_id=workspace_id,
            raw_content=content,
        )
        return {
            "status": "success",
            "message": f"Document '{file.filename}' processed successfully.",
            "data": result,
        }
    except Exception as e:
        logger.error("REST document upload failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {e!s}")


@app.post("/v1/documents/upload/async", tags=["Ingestion"])
async def upload_document_async(
    file: UploadFile = File(..., description="Document file to queue (.md, .txt, .pdf, .docx, .xlsx)"),  # noqa: B008
    workspace_id: str = Form(..., description="Target knowledge workspace"),
    user_id: str = Form(default="alice", description="User ID performing upload"),
) -> dict:
    """
    Asynchronously upload a heavy document. Enqueues processing to Celery background workers.
    Returns task_id for polling status via GET /v1/tasks/{task_id}.
    """
    try:
        assert_can_write(user_id, workspace_id)
    except AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))}",
        )

    try:
        staging_dir = os.path.join("data", "storage", "staging")
        os.makedirs(staging_dir, exist_ok=True)
        safe_name = f"{uuid.uuid4()}-{file.filename}"
        staging_path = os.path.abspath(os.path.join(staging_dir, safe_name))

        content = await file.read()
        with open(staging_path, "wb") as f:
            f.write(content)

        from apps.worker.tasks import process_document_task
        task = process_document_task.delay(staging_path, workspace_id)

        logger.info("Enqueued async ingestion task", task_id=task.id, filename=file.filename, workspace=workspace_id)
        return {
            "status": "queued",
            "task_id": task.id,
            "filename": file.filename,
            "workspace_id": workspace_id,
            "message": "Document queued for asynchronous background processing.",
        }
    except Exception as e:
        logger.error("Failed to enqueue async upload", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {e!s}")


@app.get("/v1/tasks/{task_id}", tags=["Ingestion"])
async def get_task_status(task_id: str) -> dict:
    """Check status and output of an asynchronous Celery ingestion task."""
    from apps.worker.celery_app import celery_app
    res = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": res.status,
        "ready": res.ready(),
        "successful": res.successful() if res.ready() else None,
        "result": res.result if res.ready() and res.successful() else None,
        "error": str(res.result) if res.ready() and not res.successful() else None,
    }


@app.post("/v1/harness/ask", tags=["Agent Harness"])
async def ask_knowledge(request: AskRequest) -> dict:
    """
    Ask a question grounded in documentation through the Agent Harness.
    Enforces RBAC, PII redaction, prompt injection defense, hybrid RRF retrieval,
    strict JSON schema synthesis via local LLM, and citation verification.
    """
    logger.info("REST ask_knowledge called", workspace=request.workspace_id, user_id=request.user_id, model=request.model)
    return await ask_docs(
        question=request.question,
        workspace_id=request.workspace_id,
        user_id=request.user_id,
        top_k=request.top_k,
        model=request.model,
    )


@app.post("/v1/retrieval/search", tags=["Retrieval"])
async def search_retrieval(request: SearchRequest) -> dict:
    """
    Direct hybrid search combining dense vector similarity (<=>) and sparse tsvector search
    fused with Reciprocal Rank Fusion (RRF k=60).
    """
    try:
        assert_workspace_access(request.user_id, request.workspace_id)
    except AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    logger.info("REST hybrid search called", workspace=request.workspace_id, query=request.query)
    retrieval = await hybrid_retrieve(
        query=request.query,
        workspace_id=request.workspace_id,
        top_k=request.top_k,
    )

    return {
        "results": [
            {
                "chunk_id": c.id,
                "title": c.title,
                "section": c.section_title,
                "content": c.content,
                "score": c.score,
                "source_uri": c.source_uri,
            }
            for c in retrieval.chunks
        ],
        "top_vector_score": retrieval.top_vector_score,
        "trace": retrieval.trace,
    }
