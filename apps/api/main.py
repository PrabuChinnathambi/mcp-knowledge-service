from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from packages.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Application startup logic
    yield
    # Application shutdown logic


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }

