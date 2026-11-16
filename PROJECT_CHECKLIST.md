# Project Progress & Roadmap Checklist: MCP Knowledge Service

This document tracks the end-to-end implementation status of the **MCP Knowledge Service**. It serves as the living source of truth for both Junior Developers and Senior Reviewers.

> [!NOTE]
> Every time a task or feature is completed, update this checklist by checking the box (`[x]`), adding relevant metrics/commit hashes, and updating the summary dashboard below.

---

## Executive Progress Dashboard

| Metric | Current Status | Target |
| :--- | :--- | :--- |
| **Current Git Branch** | `feat-setup-mcp-environment` | Protected `main` via PR |
| **Implementation Progress** | **95% Complete** (Production-Ready Architecture) | 100% (Production Cloud Deployment) |
| **Automated Unit Tests** | **33 / 33 Passing** (100%) | 100% Pass Rate |
| **Golden Evals Benchmark** | **8 / 8 Passing** (100.0% Pass Rate) | $\ge$ 80% Pass Gate |
| **Local Offline LLMs** | **3 Models Integrated** (Qwen 2.5, Llama 3.2, DeepSeek-R1) | Multi-Model Local Fallback |
| **Supported Ingestion Formats** | Markdown (`.md`), Text (`.txt`), PDF (`.pdf`), Word (`.docx`), Excel (`.xlsx`) | Full Enterprise Format Support |
| **MCP Transports** | Stdio (Claude/Cursor) & SSE (HTTP Remote Agents) | Local & Distributed Agents |

---

## Phase 1: Environment & Foundational Infrastructure

- [x] **Python 3.12+ & `uv` Package Management**
  - [x] Monorepo layout initialized with `apps/`, `packages/`, `scripts/`, `tests/`, `evals/`.
  - [x] Dependencies locked with `uv.lock`.
- [x] **PostgreSQL 17 + `pgvector` Vector Store**
  - [x] Docker container `my-postgres` configured on `localhost:5432`.
  - [x] Installed `postgresql-17-pgvector` (extension `vector` v0.8.7) & `pg_trgm`.
  - [x] Async SQLAlchemy database engine with `asyncpg` and `greenlet` support.
  - [x] Database schema initializer script: `packages/infrastructure/init_db.py`.
- [x] **Storage Layer (MinIO + Local Storage Fallback)**
  - [x] MinIO S3 client initialized with lazy loading.
  - [x] Resilient local filesystem fallback to `data/storage/` if MinIO port 9000 is offline.
- [x] **Logging & Observability**
  - [x] Structured JSON logging via `structlog`.
  - [x] Stdio-safe routing to `sys.stderr` to prevent JSON-RPC stream corruption for MCP clients.

---

## Phase 2: Ingestion & Document Processing Pipeline

- [x] **Multi-Format Document Extractors (`packages/ingestion/loaders.py`)**
  - [x] Markdown loader (`.md`) with header hierarchy extraction.
  - [x] Plain text loader (`.txt`).
  - [x] PDF loader (`.pdf`) powered by PyMuPDF (`fitz`).
  - [x] Microsoft Word loader (`.docx`) with heading hierarchy & Markdown table extraction.
  - [x] Microsoft Excel loader (`.xlsx`) with multi-sheet Markdown table conversion.
- [x] **Hierarchical Section-Aware Chunker (`packages/ingestion/chunker.py`)**
  - [x] Splits documents along natural `#`, `##`, `###` Markdown section boundaries.
  - [x] Token-window sliding with configurable overlap (`CHUNK_SIZE=1000`, `CHUNK_OVERLAP=150`).
- [x] **Idempotent Ingestion Controller (`packages/ingestion/pipeline.py`)**
  - [x] Content hashing (SHA-256) to skip unchanged documents (`status: skipped`).
  - [x] PII redaction (email, phone numbers, SSNs) before embedding generation.
  - [x] Atomic delta re-indexing: purges outdated chunks in a single transaction before inserting new ones.
- [x] **Operational CLI Ingestion Script (`scripts/ingest.py`)**
  - [x] Batch folder ingestion (`uv run python scripts/ingest.py data/docs/hr-docs hr-docs`).
  - [x] Single file ingestion (`uv run python scripts/ingest.py file.md workspace_id`).

---

## Phase 3: Embeddings & Hybrid Retrieval Engine

- [x] **768-Dimensional Embedding Provider (`packages/retrieval/embeddings.py`)**
  - [x] Local GPU-accelerated Ollama embedding client using `nomic-embed-text:latest` (768-dim).
  - [x] L2 vector normalization for accurate cosine distance calculation.
  - [x] Deterministic `MockEmbeddingProvider` for lightning-fast, zero-dependency CI unit testing.
- [x] **Hybrid Retrieval Engine (`packages/retrieval/hybrid.py`)**
  - [x] Dense semantic vector similarity search using `pgvector` cosine distance operator (`<=>`).
  - [x] Sparse keyword full-text search using PostgreSQL `tsvector` and `ts_rank_cd`.
  - [x] Reciprocal Rank Fusion (RRF with constant $k=60$) combining vector and keyword ranks.
- [x] **Operational CLI Search Utility (`scripts/search.py`)**
  - [x] Interactive terminal testing for hybrid retrieval queries.

---

## Phase 4: Multi-LLM Offline Inference Engine

- [x] **Multi-Model Local Inference (`packages/infrastructure/llm.py`)**
  - [x] **Qwen 2.5 7B Instruct** (`qwen2.5:7b-instruct`): Default balanced model for enterprise JSON schemas.
  - [x] **Llama 3.2 3B** (`llama3.2:3b`): Ultra-fast edge model (~5.5s latency, 40% faster).
  - [x] **DeepSeek-R1 1.5B** (`deepseek-r1:1.5b`): Multi-step reasoning model with chain-of-thought extraction.
- [x] **DeepSeek `<think>` Tag Stripper**
  - [x] Isolates and extracts `<think>...</think>` reasoning into `reasoning_trace` while preserving valid JSON parsing.
- [x] **Model Discovery & Catalog API**
  - [x] Real-time Ollama tag detection (`llm_client.list_available_models()`).
- [x] **Dynamic CLI Model Switcher (`scripts/ask.py`)**
  - [x] Supports `--model` flag: `uv run python scripts/ask.py hr-docs "Question" --model llama3.2:3b`.

---

## Phase 5: Enterprise Agent Harness & Guardrails

- [x] **Role-Based Access Control (RBAC) (`packages/harness/auth.py`)**
  - [x] Multi-tenant workspace boundary enforcement (`hr-docs`, `api-docs`, `engineering`).
  - [x] Read vs Write permission checks before retrieval or ingestion.
- [x] **Security Guardrails (`packages/harness/guardrails.py`)**
  - [x] Prompt injection defense (regex pattern scanning for instruction override attempts).
  - [x] Malicious chunk isolation (chunks with injected instructions are flagged and excluded from citations).
  - [x] PII scrubbing (masks emails, phones, credentials).
- [x] **Strict Citation Verifier (`packages/harness/verifier.py`)**
  - [x] Validates that every citation in LLM answer exists in authorized, unflagged context chunks.
  - [x] Discards hallucinated chunk UUIDs and flags failed answers.
- [x] **Audit Trace Persistence (`packages/harness/trace.py`)**
  - [x] Records full execution lifecycle (latency, prompt tokens, completion tokens, model, status, citations) to PostgreSQL `execution_traces`.

---

## Phase 6: MCP Server & Client Integrations

- [x] **Official Anthropic MCP 2.x Engine (`apps/mcp_server/main.py`)**
  - [x] Built on `mcp.server.mcpserver.MCPServer`.
  - [x] Registered tools: `list_collections`, `search_knowledge`, `ask_docs`, `ingest_document`, `list_models`.
  - [x] Dual transport support: `stdio` (default) and `sse` (Server-Sent Events over HTTP).
- [x] **Claude Desktop Integration**
  - [x] Standard path: `%APPDATA%\Claude\claude_desktop_config.json`.
  - [x] MSIX / Windows Store path: `AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\claude_desktop_config.json`.
  - [x] Verified live tool execution inside Claude Desktop chat.
- [x] **Cursor AI Integration**
  - [x] Workspace level: `.cursor/mcp.json`.
  - [x] Global level: `~/.cursor/mcp.json`.
  - [x] Verified active green status in Cursor MCP settings.

---

## Phase 7: Production REST API Gateway

- [x] **FastAPI REST Gateway (`apps/api/main.py`)**
  - [x] `GET /health`: Health and environment status.
  - [x] `GET /v1/workspaces`: RBAC tenant workspaces for user.
  - [x] `GET /v1/models`: Local offline LLM hardware and availability catalog.
  - [x] `POST /v1/documents/upload`: Synchronous multipart file upload (`.md`, `.txt`, `.pdf`, `.docx`, `.xlsx`).
  - [x] `POST /v1/documents/upload/async`: Asynchronous background upload returning Celery `task_id`.
  - [x] `GET /v1/tasks/{task_id}`: Polling endpoint for background ingestion progress.
  - [x] `POST /v1/harness/ask`: Grounded Q&A with model selection parameter.
  - [x] `POST /v1/retrieval/search`: Hybrid search with scores and metadata.
  - [x] Interactive OpenAPI / Swagger UI at `http://localhost:8000/docs`.

---

## Phase 8: Evaluation Harness & Golden Benchmark

- [x] **Golden Dataset (`evals/datasets/golden.jsonl`)**
  - [x] 8 curated test cases spanning HR policies, API docs, negative/refusal cases, and prompt injection attacks.
- [x] **Deterministic Evaluation Graders (`evals/graders/graders.py`)**
  - [x] Source recall grader.
  - [x] Keyword coverage grader.
  - [x] Refusal grader (for ungrounded queries).
  - [x] Access control grader (for unauthorized users).
  - [x] Injection defense grader (verifies attacks are blocked without leaking forbidden phrases).
- [x] **Automated Evaluation Runner (`evals/runner/run_evals.py`)**
  - [x] Supports testing any local model (`python evals/runner/run_evals.py llama3.2:3b`).
  - [x] **Achieved 100.0% Pass Rate (8/8 cases passing)**.

---

## Phase 9: Quality Assurance & CI/CD Pipeline

- [x] **Comprehensive Pytest Suite (`tests/unit/`)**
  - [x] `test_api.py`: 10 tests covering REST endpoints and validation errors.
  - [x] `test_api_async.py`: 3 tests covering async upload queuing and Celery task status.
  - [x] `test_chunker.py`: 3 tests covering section splitting and sliding windows.
  - [x] `test_config.py`: 2 tests covering environment loading and embedding dimensions.
  - [x] `test_guardrails.py`: 3 tests covering PII masking and injection detection.
  - [x] `test_llm_multi_model.py`: 6 tests covering multi-model routing and DeepSeek `<think>` extraction.
  - [x] `test_loaders_advanced.py`: 3 tests covering `.docx`, `.xlsx`, and format validation.
  - [x] `test_verifier.py`: 3 tests covering grounded citation validation and hallucination rejection.
  - [x] **Total: 33 / 33 unit tests passing** (`uv run pytest tests/unit/`).
- [x] **Enterprise CI/CD Workflow (`.github/workflows/ci.yml`)**
  - [x] Automated GitHub Actions workflow on PR / Push.
  - [x] Spins up PostgreSQL 17 + `pgvector` service container.
  - [x] Runs `ruff` linter check.
  - [x] Runs full unit test suite with mock embeddings.

---

## Phase 10: Production Readiness & Enterprise Cloud Roadmap

### 10.1 Background Worker & Broker Deployment
- [x] **Launch Redis Service in Docker**
  - [x] Redis container `mcp-redis` running on port 6379 (`redis:7-alpine`).
  - [x] Verified connection with `redis-py` ping (`SUCCESS`).
- [x] **Asynchronous Ingestion Worker**
  - [x] `apps/worker/celery_app.py` & `apps/worker/tasks.py` wired to Redis.
- [x] **Expose Async Ingestion Endpoints in REST API**
  - [x] `POST /v1/documents/upload/async`: Enqueue document processing and return Celery `task_id`.
  - [x] `GET /v1/tasks/{task_id}`: Poll Celery task progress (`PENDING`, `STARTED`, `SUCCESS`, `FAILURE`).

### 10.2 Remote MCP Server over SSE (Server-Sent Events)
- [x] **Remote Agent Access over HTTP/SSE**
  - [x] Added `--transport sse --host 0.0.0.0 --port 8080` CLI runner to `apps/mcp_server/main.py`.
  - [x] Enables remote agents, curl, or web apps to connect over network SSE.

### 10.3 Advanced Document Ingestion
- [x] **Microsoft Office Format Support**
  - [x] `.docx` parser with heading hierarchy and table extraction.
  - [x] `.xlsx` spreadsheet parser with multi-sheet Markdown table conversion.
- [ ] **OCR for Scanned Documents**
  - [ ] Integrate Tesseract OCR or Docling for scanned image-based PDFs without embedded text.

### 10.4 Production Authentication & Security Hardening
- [ ] **JWT / OAuth2 Bearer Authentication**
  - [ ] Replace static API key with JWT access tokens for REST API endpoints.
  - [ ] Wire user identity claims into `USER_DIRECTORY` dynamically.
- [ ] **Rate Limiting & Throttling**
  - [ ] Add SlowAPI / Redis-backed rate limiting on `POST /v1/harness/ask` and `POST /v1/documents/upload`.

### 10.5 Deployment & Cloud Packaging
- [ ] **Production Docker Compose (`docker-compose.prod.yml`)**
  - [ ] Bundle FastAPI, Celery worker, PostgreSQL (pgvector), MinIO, and Redis into a single production compose file.
- [ ] **Kubernetes Helm Charts / Manifests**
  - [ ] Create deployment and service manifests for deploying into AWS EKS, Google Cloud GKE, or Azure AKS.

---

## How to Update This Checklist

1. When completing a task:
   - Change `- [ ]` to `- [x]`.
   - Add notes or metric improvements if applicable.
2. If tests or evals change:
   - Update the **Executive Progress Dashboard** table at the top.
3. Commit the updated checklist on your feature branch (`feat-setup-mcp-environment`):
   ```powershell
   git add PROJECT_CHECKLIST.md
   git commit -m "docs: update project task checklist"
   git push origin feat-setup-mcp-environment
   ```
