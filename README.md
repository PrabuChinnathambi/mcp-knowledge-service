# MCP Knowledge Service

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Model Context Protocol](https://img.shields.io/badge/MCP-2.3%2B-purple.svg)](https://modelcontextprotocol.io/)
[![Package Manager](https://img.shields.io/badge/uv-managed-2b2b2b.svg)](https://astral.sh/uv)
[![Vector Engine](https://img.shields.io/badge/PostgreSQL%2017-pgvector-336791.svg?logo=postgresql)](https://github.com/pgvector/pgvector)
[![Inference Engine](https://img.shields.io/badge/Ollama-Multi--LLM%20(Qwen%20%7C%20Llama%20%7C%20DeepSeek)-black.svg)](https://ollama.com/)
[![Tests](https://img.shields.io/badge/Tests-19%20Passing-brightgreen.svg)](#testing--quality-assurance)

An enterprise-grade, local-first Knowledge Management and Semantic Retrieval Service built on Anthropic's **Model Context Protocol (MCP)**. 

The service acts as a governed, zero-hallucination knowledge backbone that empowers AI clients—such as **Claude Desktop**, **Cursor AI**, and autonomous agent loops—to securely index, search, and ground contextual answers across private enterprise documentation with **verified citations, multi-tenant RBAC, PII redaction, and prompt injection defense**.

---

## Table of Contents

- [What is MCP Knowledge Service?](#what-is-mcp-knowledge-service)
- [The Problem It Solves](#the-problem-it-solves)
- [System Architecture](#system-architecture)
  - [High-Level Context Diagram](#high-level-context-diagram)
  - [Query Flow with the Agent Harness](#query-flow-with-the-agent-harness)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Quickstart Guide](#quickstart-guide)
  - [1. Environment Setup](#1-environment-setup)
  - [2. Dependencies Installation](#2-dependencies-installation)
  - [3. Start Infrastructure (Postgres, MinIO, Redis)](#3-start-infrastructure-postgres-minio-redis)
  - [4. Database Initialization](#4-database-initialization)
  - [5. Ingest Sample Documents](#5-ingest-sample-documents)
  - [6. Test Hybrid Retrieval & Agent Harness](#6-test-hybrid-retrieval--agent-harness)
- [MCP Client Integrations](#mcp-client-integrations)
  - [Claude Desktop Integration](#claude-desktop-integration)
  - [Cursor AI Integration](#cursor-ai-integration)
- [CLI Operations Manual](#cli-operations-manual)
- [The Agent Harness & Guardrails](#the-agent-harness--guardrails)
- [Evaluation Harness & Golden Dataset](#evaluation-harness--golden-dataset)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Git Workflow Policy](#git-workflow-policy)
- [License](#license)

---

## What is MCP Knowledge Service?

Think of this service as a **secure, private "Company Brain" for AI agents**.

Standard AI models (like Claude or ChatGPT) are trained on public Internet data and know nothing about your company's private policies, technical specs, or internal code. Uploading sensitive PDFs directly to public web chats risks data leakage, exceeds token limits, and causes costly hallucinations.

**`mcp-knowledge-service`** solves this by establishing a standardized, local-first **Model Context Protocol (MCP)** bridge:
1. Documents (PDF, Markdown, TXT) are parsed, scrubbed of PII, chunked, and embedded locally on your GPU.
2. Vectors and text are stored in a unified **PostgreSQL 17 + `pgvector`** database.
3. When Claude or Cursor queries the service, our **Agent Harness** retrieves relevant snippets, gates relevance, prevents prompt injection, and **verifies citations** before Claude outputs the answer.

---

## The Problem It Solves

| Enterprise Risk | Naive RAG / Public AI | How `mcp-knowledge-service` Solves It |
|---|---|---|
| **Hallucination Liability** | LLMs fabricate plausible-sounding policies or API parameters. | **Relevance Gating & Citation Verifier**: Refuses when evidence is absent; verifies every citation against retrieved chunk IDs. |
| **Data & Privacy Leaks** | Raw employee emails, phones, and IDs are indexed. | **Automated PII Scrubbing**: Masks emails, phones, PAN, and Aadhaar before vectorization. |
| **Search Blind Spots** | Keyword search misses synonyms; vector search misses exact technical codes (`X-Signature`). | **Hybrid Retrieval with RRF**: Combines dense `pgvector` cosine similarity with sparse `tsvector` full-text search. |
| **Multi-Tenant Leakage** | Engineering queries reveal confidential HR/executive documents. | **Workspace RBAC Isolation**: Queries are partitioned by `workspace_id` and verified pre-retrieval. |
| **Indirect Prompt Injection** | Malicious notes hijack agent prompts (`"IGNORE ALL PREVIOUS INSTRUCTIONS"`). | **Untrusted Data Framing**: Chunks are treated as read-only data; injection chunks are denylisted from citations. |

---

## System Architecture

### High-Level Context Diagram

```mermaid
flowchart TD
    subgraph Clients["Clients & AI Assistants"]
        Claude["Claude Desktop\n(stdio JSON-RPC)"]
        Cursor["Cursor AI\n(Composer & Chat)"]
        CLI["Operational CLI Scripts\n(ingest, search, ask)"]
    end

    subgraph Entrypoints["Application Entrypoints (apps/)"]
        MCP["MCP Server Protocol Engine\n(apps/mcp_server)"]
        API["FastAPI REST Gateway\n(apps/api)"]
        Worker["Celery Background Worker\n(apps/worker)"]
    end

    subgraph Harness["The Agent Harness (packages/harness)"]
        Auth["Workspace RBAC Auth"]
        Guard["PII & Injection Guardrails"]
        Gate["Relevance Gate (Score >= 0.30)"]
        Verifier["Strict Citation Verifier"]
        Tracer["Execution Trace Recorder"]
    end

    subgraph Intelligence["Retrieval & AI Models"]
        Hybrid["Hybrid Retrieval Engine\nReciprocal Rank Fusion (RRF k=60)"]
        OllamaEmbed["Ollama GPU Embedding\n(nomic-embed-text: 768-dim)"]
        OllamaLLM["Ollama GPU Generation\n(qwen2.5:7b-instruct: Temp=0)"]
    end

    subgraph Storage["Persistence Vault"]
        PG[("PostgreSQL 17 + pgvector\n- documents (metadata, checksum)\n- chunks (vector, tsvector)\n- execution_traces")]
        MinIO[("MinIO Object Storage\n- Raw document vault")]
        Redis[("Redis\n- Task queue & cache")]
    end

    Claude -->|stdio| MCP
    Cursor -->|stdio / mcp.json| MCP
    CLI --> Harness

    MCP --> Harness
    API --> Harness
    Worker --> Storage

    Harness --> Auth --> Guard --> Hybrid
    Hybrid --> PG
    Hybrid --> OllamaEmbed
    Harness --> Gate --> OllamaLLM --> Verifier --> Tracer
    Tracer --> PG
```

---

### Query Flow with the Agent Harness

```mermaid
sequenceDiagram
    autonumber
    actor User as User in Claude Desktop / Cursor
    participant MCP as apps/mcp_server
    participant Harness as packages/harness/agent.py
    participant Hybrid as packages/retrieval/hybrid.py
    participant DB as PostgreSQL 17 (pgvector)
    participant LLM as Ollama GPU (qwen2.5)

    User->>MCP: ask_docs(workspace_id, question)
    MCP->>Harness: ask_docs(input, user_id)
    Harness->>Harness: 1. RBAC Check (assert_workspace_access)
    Harness->>Harness: 2. Query Prompt Injection Scan
    Harness->>Hybrid: 3. Hybrid Retrieve (query, workspace_id)
    Hybrid->>DB: Dense Vector (<=>) + Sparse tsvector Search
    DB-->>Hybrid: Vector hits + Keyword hits
    Hybrid->>Hybrid: Reciprocal Rank Fusion (RRF k=60)
    Hybrid-->>Harness: Top-5 Scored Chunks + top_vector_score
    
    alt top_vector_score < 0.30
        Harness-->>MCP: status="refused" ("Insufficient authoritative evidence")
    else score >= 0.30
        Harness->>Harness: 4. Flag malicious injection chunks
        Harness->>LLM: 5. Grounded Prompt (Temperature 0, JSON Schema)
        LLM-->>Harness: JSON: {answer, citations}
        Harness->>Harness: 6. Verify citations ⊆ retrieved unflagged chunks
        alt Citation Invalid or from Malicious Chunk
            Harness-->>MCP: status="failed" ("Citation verification failed")
        else Citation Valid
            Harness->>DB: 7. Save Audit Trace (latency, tokens, status)
            Harness-->>MCP: status="answered" {answer, citations, trace_id}
            MCP-->>User: Verified answer with source footnotes
        end
    end
```

---

## Key Features

- **Anthropic MCP 2.x Native**: Implements official `MCPServer` exposing standard tools:
  - `list_collections`: List accessible knowledge workspaces.
  - `search_knowledge`: Hybrid semantic + keyword search with RRF scores.
  - `ask_docs`: Grounded Q&A with citation verification.
  - `ingest_document`: Index new documents into workspaces.
- **Local GPU Acceleration**: 100% private, zero-cloud API dependency using local **Ollama**:
  - Embeddings: `nomic-embed-text:latest` (768 dimensions).
  - Generation: `qwen2.5:7b-instruct` (runs with strict JSON formatting).
- **PostgreSQL 17 + `pgvector`**: Unified relational, vector, and full-text search in a single ACID database.
- **Hierarchical Section Chunker**: Splits text along Markdown headings (`#`, `##`, `###`) so chunks carry structural context.
- **PII Scrubbing**: Automatically sanitizes emails, phone numbers, and national IDs (`[EMAIL]`, `[PHONE]`, `[PAN_ID]`, `[AADHAAR_ID]`).
- **Prompt Injection Defense**: Detects adversarial jailbreaks (`"IGNORE ALL PREVIOUS INSTRUCTIONS"`) and excludes flagged chunks from valid citations.
- **Audit Traces**: Every query records latency, prompt tokens, completion tokens, and verification status in PostgreSQL `execution_traces`.

---

## Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Language & Runtime** | Python 3.12+ | Modern async IO, type annotations, pattern matching |
| **Package Manager** | `uv` (Astral) | Sub-second virtualenv resolution and deterministic lockfiles |
| **Agent Protocol** | `mcp` (v2.3+) | Official Anthropic Model Context Protocol SDK |
| **Database** | PostgreSQL 17 + `pgvector` | Unified metadata, vector embeddings (HNSW), and full-text search (GIN) |
| **ORM / Data Access** | SQLAlchemy 2.0 + `asyncpg` | Asynchronous relational data mapping with `greenlet` |
| **Object Store** | MinIO | S3-compatible raw file archive with local filesystem fallback |
| **Task Queue** | Celery + Redis | Asynchronous background processing queue |
| **Local Inference** | Ollama | Local GPU inference for embeddings and text generation |
| **PDF Extraction** | PyMuPDF (`fitz`) | High-speed layout and text parsing |
| **Observability** | `structlog` | Structured JSON logging routed strictly to `stderr` |
| **Testing** | `pytest` + `pytest-asyncio` | Automated unit test and regression suite |

---

## Repository Layout

```text
mcp-knowledge-service/
├── .cursor/
│   └── mcp.json                  # Cursor IDE project-level MCP configuration
├── .env                          # Local environment variables
├── .env.example                  # Environment template
├── pyproject.toml                # Dependencies and tool settings
├── uv.lock                       # Deterministic lockfile
├── docker-compose.yml            # PostgreSQL (pgvector), Redis, MinIO services
├── README.md                     # This documentation manual
│
├── apps/                         # Executable Application Entrypoints
│   ├── api/                      # FastAPI REST Gateway
│   │   └── main.py               # REST endpoints & health checks
│   ├── mcp_server/               # Model Context Protocol Engine
│   │   └── main.py               # FastMCP server with registered tools
│   └── worker/                   # Celery Background Workers
│       ├── celery_app.py         # Celery configuration
│       └── tasks.py              # Background ingestion tasks
│
├── packages/                     # Core Domain & Infrastructure (Hexagonal Architecture)
│   ├── core/                     # Configuration (pydantic-settings)
│   ├── domain/                   # SQLAlchemy ORM models & Pydantic schemas
│   ├── infrastructure/           # Database sessions, MinIO storage, Ollama client
│   ├── ingestion/                # Document loaders, section chunker, pipeline
│   ├── retrieval/                # Embeddings provider, hybrid search, RRF ranker
│   ├── harness/                  # Security policy, RBAC, guardrails, citation verifier
│   └── observability/            # Stdio-safe structured JSON logger
│
├── scripts/                      # Operational CLI Tools
│   ├── ingest.py                 # Ingest files/folders into a workspace
│   ├── search.py                 # CLI hybrid search tool
│   └── ask.py                    # CLI harness Q&A query tool
│
├── data/
│   ├── docs/                     # Sample workspace documents (hr-docs, api-docs)
│   └── storage/                  # Local object store fallback
│
├── tests/                        # Automated Pytest Suite
│   └── unit/                     # Fast unit tests (13 passing tests)
│
└── evals/                        # Evaluation Harness
    ├── datasets/golden.jsonl     # Ground-truth evaluation dataset
    ├── graders/graders.py        # Deterministic quality graders
    └── runner/run_evals.py       # CI evaluation gate script
```

---

## Prerequisites

Before starting, ensure the following are installed:
- [Python 3.12+](https://www.python.org/)
- [`uv` Package Manager](https://docs.astral.sh/uv/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- [Ollama](https://ollama.com/) (running)

Pull the local GPU models via Ollama:
```bash
ollama pull nomic-embed-text:latest
ollama pull qwen2.5:7b-instruct
```

---

## Quickstart Guide

### 1. Environment Setup
Copy the template and verify your environment parameters:
```bash
cp .env.example .env
```

Your `.env` should point to your PostgreSQL instance and local Ollama models:
```ini
DATABASE_URL=postgresql+asyncpg://admin:myMCPsecretpassword@localhost:5432/mcp-knowledge-service
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text:latest
EMBEDDING_DIMENSIONS=768
OLLAMA_URL=http://localhost:11434
LLM_MODEL=qwen2.5:7b-instruct
MIN_RELEVANCE=0.30
MCP_USER_ID=alice
```

### 2. Dependencies Installation
Sync dependencies in sub-second time using `uv`:
```bash
uv sync --all-groups
```

### 3. Start Infrastructure (Postgres, MinIO, Redis)
If using Docker Compose:
```bash
docker compose up -d
```
*(If you already have a PostgreSQL container named `my-postgres`, ensure `postgresql-17-pgvector` is installed).*

### 4. Database Initialization
Initialize database tables and enable `vector` and `pg_trgm` extensions:
```bash
uv run python -m packages.infrastructure.init_db
```

### 5. Ingest Sample Documents
Index the sample HR documents into the `hr-docs` workspace:
```bash
uv run python scripts/ingest.py data/docs/hr-docs hr-docs
```
*Note: Running the command again will compute SHA-256 checksums and automatically report `status: skipped`.*

### 6. Test Hybrid Retrieval & Agent Harness
Run a hybrid search query:
```bash
uv run python scripts/search.py hr-docs "how many vacation days roll over"
```

Ask a grounded question through the complete Agent Harness:
```bash
uv run python scripts/ask.py hr-docs "How many unused annual leave days can be carried forward?"
```

---

## MCP Client Integrations

### Claude Desktop Integration

#### 1. Open Claude Desktop Configuration
Depending on how Claude was installed on Windows, the configuration is stored in:
- **Standard Install:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Windows Store Install:**  
  `%LOCALAPPDATA%\Claude-Data\claude_pzs8sxrjxfjjc\claude_desktop_config.json`

#### 2. Add the MCP Server Configuration
```json
{
  "mcpServers": {
    "knowledge-service": {
      "command": "C:\\Users\\Karunakaran\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\Users\\Karunakaran\\Prabu\\mcp-knowledge-service",
        "run",
        "python",
        "-m",
        "apps.mcp_server.main"
      ],
      "env": {
        "MCP_USER_ID": "alice"
      }
    }
  }
}
```
*(Replace paths with your local absolute paths).*

#### 3. Restart Claude Desktop
Quit Claude completely from your Windows system tray, then relaunch it.
Under **Settings $\rightarrow$ Developer**, you will see **`knowledge-service`** connected with 4 tools.

---

### Cursor AI Integration

Cursor natively supports MCP through `.cursor/mcp.json`.

1. Open this repository in **Cursor**.
2. Go to **Settings** (`Ctrl + Shift + J`) $\rightarrow$ **Features** $\rightarrow$ **MCP**.
3. You will see **`knowledge-service`** active with a green indicator.
4. In Cursor Chat (`Ctrl + L`) or Composer (`Ctrl + I`), query:
   > *"@knowledge-service What is our webhook retry policy according to api-docs?"*

---

## CLI Operations Manual

The `scripts/` directory provides operational utilities for testing every layer independently:

### 1. Ingest Documents
```bash
# Ingest a single file
uv run python scripts/ingest.py data/docs/api-docs/webhooks.md api-docs

# Ingest an entire directory
uv run python scripts/ingest.py data/docs/hr-docs hr-docs
```

### 2. Hybrid Search
```bash
uv run python scripts/search.py <workspace_id> <query>
```
*Example:*
```bash
uv run python scripts/search.py api-docs "X-Signature header"
```

### 3. Agent Harness Q&A (Multi-LLM Enabled)

The service supports dynamic local model switching between **Qwen 2.5**, **Llama 3.2**, and **DeepSeek-R1**:

```bash
# Default (Qwen 2.5 7B Instruct - Enterprise Structured Output)
uv run python scripts/ask.py hr-docs "When is a medical certificate required for sick leave?"

# Fast Inference (Llama 3.2 3B - Ultra-low latency)
uv run python scripts/ask.py hr-docs "How many days of annual vacation do employees get?" --model llama3.2:3b

# Deep Reasoning (DeepSeek-R1 1.5B - Multi-step logic & <think> reasoning)
uv run python scripts/ask.py hr-docs "Can an employee carry forward leave into Q2?" --model deepseek-r1:1.5b
```

---

## The Agent Harness & Guardrails

The Agent Harness (`packages/harness/`) ensures enterprise safety:

```text
 1. RBAC Check            ──> Blocks unauthorized users before running retrieval.
 2. PII Sanitizer         ──> Masks personal data before indexing/generating.
 3. Relevance Gate        ──> If hybrid score < 0.30, refuses instead of hallucinating.
 4. Context Isolation     ──> Frames chunks as untrusted DATA inside XML tags.
 5. Citation Verifier     ──> Discards answers citing non-existent or malicious chunks.
 6. Trace Recorder        ──> Persists full execution telemetry to PostgreSQL.
```

### Testing the Guardrails

```bash
# 1. Active Refusal on Missing Facts (Refuses cleanly)
uv run python scripts/ask.py hr-docs "What is our company policy on dental implants?"

# 2. Prompt Injection Defense (Rejects malicious instruction in untrusted-note.md)
uv run python scripts/ask.py hr-docs "Is remote work unlimited without approval?"

# 3. RBAC Access Control (Bob is blocked from hr-docs)
$env:MCP_USER_ID="bob"; uv run python scripts/ask.py hr-docs "What is the sick leave policy?"
```

---

## Evaluation Harness & Golden Dataset

The project includes an automated evaluation harness in `evals/` that evaluates the production `ask_docs` code path against `evals/datasets/golden.jsonl`:

- **Source Recall@K:** Verifies expected source documents are retrieved.
- **Keyword Coverage:** Verifies key facts appear in the generated answer.
- **Refusal Behavior:** Verifies the system refuses when questions are ungrounded.
- **Access Control:** Verifies cross-workspace access is denied.

Run the evaluation suite:
```bash
uv run python evals/runner/run_evals.py
```

---

## Testing & Quality Assurance

Run the automated Pytest test suite:
```bash
uv run pytest tests/unit/
```

Run test suite with coverage:
```bash
uv run pytest --cov=packages --cov-report=term-missing
```

Code quality and static typing:
```bash
# Linting & Formatting
uv run ruff check .

# Static Type Checking
uv run mypy packages apps
```

---

## Git Workflow Policy

> [!IMPORTANT]
> **Strict No-Direct-Push to `main` / `master`**
>
> 1. All development must occur on dedicated feature branches (e.g. `feat-setup-mcp-environment`).
> 2. Direct pushes to `main` or `master` are strictly prohibited.
> 3. Merging into `main` requires a formal Senior Developer Code Review sign-off, passing all unit tests (`pytest`), and clean linter checks (`ruff`).

---

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
