
from packages.core.config import Settings


def test_settings_load_from_environment(monkeypatch):

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://test:test@localhost:5432/testdb",
    )

    monkeypatch.setenv(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )

    monkeypatch.setenv("MINIO_ACCESS_KEY", "test-access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "test-secret")

    settings = Settings(_env_file=None)

    assert settings.APP_NAME in {"mcp-knowledge-service", "knowledge-mcp"}
    assert settings.DATABASE_URL.startswith("postgresql")
    assert settings.REDIS_URL.startswith("redis")
    assert settings.MINIO_BUCKET in {"knowledge", "knowledge-docs"}

    print("Configuration test passed!")


def test_default_settings():

    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        MINIO_ACCESS_KEY="test",
        MINIO_SECRET_KEY="test",
        _env_file=None,
    )

    assert settings.ENVIRONMENT == "development"
    assert settings.LOG_LEVEL == "INFO"
