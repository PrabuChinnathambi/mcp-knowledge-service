# ============================================================================
# MCP Knowledge Service — Production Dockerfile
# ============================================================================
# Multi-stage build: install deps in builder, copy to slim runtime image.
# ============================================================================

ARG PYTHON_VERSION=3.12

# ── Stage 1: Dependency installer ──────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /app

# Install uv (fast Python package manager)
RUN pip install --no-cache-dir uv==0.5.5

# Copy dependency manifest first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install all production dependencies into an isolated venv
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: Runtime image ──────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime

WORKDIR /app

# Install curl for healthcheck probes
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy the pre-built venv from builder
COPY --from=builder /app/.venv /app/.venv

# Install uv runtime (needed for `uv run` commands in docker-compose)
RUN pip install --no-cache-dir uv==0.5.5

# Copy application source code
COPY apps/      ./apps/
COPY packages/  ./packages/
COPY evals/     ./evals/
COPY scripts/   ./scripts/
COPY pyproject.toml uv.lock ./

# Make venv discoverable on PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

# Create data directories used at runtime
RUN mkdir -p /app/data/storage/staging /app/data/docs

# Non-root user for security
RUN useradd --create-home --shell /bin/bash mcp
RUN chown -R mcp:mcp /app/data
USER mcp

EXPOSE 8000 8080

# Default command: FastAPI REST Gateway
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
