import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from packages.core.config import get_settings
from packages.harness.agent import ask_docs
from packages.harness.auth import (
    USER_DIRECTORY,
    AccessDeniedError,
    assert_can_write,
    assert_workspace_access,
    authenticate_user,
    create_access_token,
    verify_jwt_token,
)
from packages.infrastructure.llm import llm_client
from packages.ingestion.pipeline import ingest_document_file
from packages.observability.logger import logger
from packages.retrieval.hybrid import hybrid_retrieve

settings = get_settings()

bearer_security = HTTPBearer(auto_error=False)

# ============================================================================
# Rate Limiter Setup — tries Redis, falls back to in-memory storage
# ============================================================================
# In production (REDIS_URL set), rate-limit counters are shared across all
# API replicas via Redis.  During local dev / unit tests (no Redis), the
# limiter automatically degrades to a process-local MemoryStorage so the app
# and tests work without any running Redis instance.
_redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")


def _build_limiter() -> "Limiter":
    """Return a Limiter backed by Redis when available, else MemoryStorage."""
    try:
        import redis as _redis_lib
        _client = _redis_lib.from_url(_redis_url, socket_connect_timeout=1)
        _client.ping()
        return Limiter(
            key_func=get_remote_address,
            storage_uri=_redis_url,
            strategy="fixed-window",
        )
    except Exception:
        # Redis offline (CI, unit tests, local dev without Docker) — use memory
        return Limiter(
            key_func=get_remote_address,
            storage_uri="memory://",
            strategy="fixed-window",
        )


limiter = _build_limiter()


def _rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a clean 429 response when a rate limit is hit."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down your requests.",
            "limit": str(exc.limit),
            "retry_after": "60s",
        },
        headers={"Retry-After": "60"},
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("FastAPI service starting up", app_name=settings.APP_NAME, env=settings.ENVIRONMENT)
    yield
    logger.info("FastAPI service shutting down")


app = FastAPI(
    title=f"{settings.APP_NAME} REST Gateway",
    description=(
        "Enterprise Knowledge Retrieval, Document Ingestion, and Multi-LLM Agent Grounding REST API "
        "with JWT Authentication and Redis-backed Rate Limiting."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach SlowAPI middleware and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)


# ============================================================================
# Request / Response Schemas
# ============================================================================


class LoginRequest(BaseModel):
    username: str = Field(..., description="User account identifier (e.g. 'alice', 'bob', 'charlie')")
    password: str = Field(..., description="Account password (default dev credential: 'password123')")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    workspaces: list[str]
    expires_in_minutes: int


class WorkspacesResponse(BaseModel):
    user_id: str
    workspaces: list[str]


class AskRequest(BaseModel):
    workspace_id: str = Field(..., description="Target workspace ID (e.g. 'hr-docs', 'api-docs')")
    question: str = Field(..., description="The query to answer grounded strictly in workspace documentation.")
    user_id: str | None = Field(default=None, description="Optional override user ID for RBAC. Defaults to authenticated JWT user.")
    model: str | None = Field(
        default=None,
        description="Optional local LLM ('qwen2.5:7b-instruct', 'llama3.2:3b', 'deepseek-r1:1.5b'). Defaults to configured model.",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of context chunks to retrieve.")


class SearchRequest(BaseModel):
    workspace_id: str = Field(..., description="Target workspace ID")
    query: str = Field(..., description="Semantic or keyword search query")
    user_id: str | None = Field(default=None, description="Optional override user ID for RBAC. Defaults to authenticated JWT user.")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of ranked results to return")


# ============================================================================
# Security Dependencies
# ============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> str:
    """
    Extract and verify user identity.
    1. If a JWT Bearer token is provided in the Authorization header, validates signature and expiration.
    2. Falls back to X-User-ID header or default MCP user in development environments.
    """
    if credentials and credentials.credentials:
        try:
            payload = verify_jwt_token(credentials.credentials)
            user_id = payload.get("sub") or payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="JWT token missing user subject claim")

            # Synchronize runtime directory if claims are bundled
            if "workspaces" in payload and user_id not in USER_DIRECTORY:
                USER_DIRECTORY[user_id] = {
                    "role": payload.get("role", "viewer"),
                    "workspaces": payload.get("workspaces", []),
                }
            return user_id
        except AccessDeniedError as e:
            raise HTTPException(status_code=401, detail=str(e))

    if x_user_id:
        return x_user_id
    return settings.MCP_USER_ID


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


@app.post("/v1/auth/token", response_model=TokenResponse, tags=["Authentication"])
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, credentials: LoginRequest) -> TokenResponse:
    """
    Authenticate user credentials and generate a signed JWT Bearer access token.
    Rate limited to **10 requests/minute** per IP to block credential stuffing attacks.

    Default credentials for dev testing:
    - alice / password123 (Role: admin, Workspaces: hr-docs, api-docs, engineering)
    - bob / password123 (Role: viewer, Workspaces: api-docs)
    - charlie / password123 (Role: editor, Workspaces: engineering)
    """
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
        data={
            "sub": user["user_id"],
            "role": user["role"],
            "workspaces": user["workspaces"],
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user["user_id"],
        role=user["role"],
        workspaces=user["workspaces"],
        expires_in_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@app.get("/v1/workspaces", response_model=WorkspacesResponse, tags=["Workspaces"])
async def list_workspaces(
    current_user: str = Depends(get_current_user),
) -> WorkspacesResponse:
    """List knowledge workspaces accessible to the authenticated user."""
    user_record = USER_DIRECTORY.get(current_user, {"workspaces": []})
    return WorkspacesResponse(user_id=current_user, workspaces=user_record["workspaces"])


@app.get("/v1/models", tags=["LLM Models"])
async def list_models() -> dict[str, list[dict]]:
    """List available local offline LLMs and their hardware / installation status."""
    models = await llm_client.list_available_models()
    return {"models": models}


SUPPORTED_UPLOAD_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".xlsx"}


@app.post("/v1/documents/upload", tags=["Ingestion"])
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="Document file to upload (.md, .txt, .pdf, .docx, .xlsx)"),
    workspace_id: str = Form(..., description="Target knowledge workspace"),
    user_id: str | None = Form(default=None, description="Optional override user ID for RBAC"),
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Upload and synchronously index a document into a workspace.
    Rate limited to **20 uploads/minute** per IP.
    Performs PII redaction, hierarchical section chunking, 768-dim GPU embedding, and delta re-indexing.
    """
    effective_user = user_id or current_user
    try:
        assert_can_write(effective_user, workspace_id)
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
            user_id=effective_user,
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
@limiter.limit("20/minute")
async def upload_document_async(
    request: Request,
    file: UploadFile = File(..., description="Document file to queue (.md, .txt, .pdf, .docx, .xlsx)"),
    workspace_id: str = Form(..., description="Target knowledge workspace"),
    user_id: str | None = Form(default=None, description="Optional override user ID for RBAC"),
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Asynchronously upload a heavy document. Enqueues processing to Celery background workers.
    Rate limited to **20 uploads/minute** per IP.
    Returns task_id for polling status via GET /v1/tasks/{task_id}.
    """
    effective_user = user_id or current_user
    try:
        assert_can_write(effective_user, workspace_id)
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
@limiter.limit("30/minute")
async def ask_knowledge(
    request: Request,
    body: AskRequest,
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Ask a question grounded in documentation through the Agent Harness.
    Rate limited to **30 questions/minute** per IP.
    Enforces RBAC, PII redaction, prompt injection defense, hybrid RRF retrieval,
    strict JSON schema synthesis via local LLM, and citation verification.
    """
    effective_user = body.user_id or current_user
    logger.info("REST ask_knowledge called", workspace=body.workspace_id, user_id=effective_user, model=body.model)
    return await ask_docs(
        question=body.question,
        workspace_id=body.workspace_id,
        user_id=effective_user,
        top_k=body.top_k,
        model=body.model,
    )


@app.post("/v1/retrieval/search", tags=["Retrieval"])
@limiter.limit("60/minute")
async def search_retrieval(
    request: Request,
    body: SearchRequest,
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Direct hybrid search combining dense vector similarity (<=>) and sparse tsvector search
    fused with Reciprocal Rank Fusion (RRF k=60).
    Rate limited to **60 searches/minute** per IP.
    """
    effective_user = body.user_id or current_user
    try:
        assert_workspace_access(effective_user, body.workspace_id)
    except AccessDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    logger.info("REST hybrid search called", workspace=body.workspace_id, query=body.query)
    retrieval = await hybrid_retrieve(
        query=body.query,
        workspace_id=body.workspace_id,
        top_k=body.top_k,
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
