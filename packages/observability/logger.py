import sys
import structlog
from packages.core.config import get_settings


def setup_logger():
    settings = get_settings()

    # CRITICAL: Always direct logs to stderr. stdout is reserved for MCP JSON-RPC.
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


setup_logger()
logger = structlog.get_logger()

