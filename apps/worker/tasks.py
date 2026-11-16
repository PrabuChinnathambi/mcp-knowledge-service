import asyncio

from apps.worker.celery_app import celery_app
from packages.ingestion.pipeline import ingest_document_file
from packages.observability.logger import logger


@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, file_path: str, workspace_id: str):
    logger.info("Starting background ingestion task", file=file_path, workspace=workspace_id)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(ingest_document_file(file_path, workspace_id))
    except Exception as exc:
        logger.error("Ingestion task failed", exc=str(exc))
        raise self.retry(exc=exc, countdown=5)
