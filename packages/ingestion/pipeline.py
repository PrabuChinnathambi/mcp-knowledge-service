import hashlib
import os
import uuid
from sqlalchemy import delete, select
from packages.domain.models import Chunk, Document
from packages.harness.guardrails import redact_pii
from packages.infrastructure.database import AsyncSessionLocal
from packages.infrastructure.storage import storage_client
from packages.ingestion.chunker import chunk_document
from packages.ingestion.loaders import DocumentLoader
from packages.observability.logger import logger
from packages.retrieval.embeddings import get_embedding_provider

embedder = get_embedding_provider()


async def ingest_document_file(
    file_path: str,
    workspace_id: str,
    raw_content: bytes | None = None,
) -> dict:
    if raw_content is None:
        with open(file_path, "rb") as f:
            raw_content = f.read()

    filename = os.path.basename(file_path)
    source_uri = f"workspace://{workspace_id}/{filename}"

    # 1. Parse content
    loaded = DocumentLoader.load(file_path, raw_content)

    # 2. Redact PII (never index raw personal numbers or credentials)
    clean_text = redact_pii(loaded.content)
    checksum = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

    async with AsyncSessionLocal() as session:
        # Check for existing document
        stmt = select(Document).where(
            Document.workspace_id == workspace_id,
            Document.source_uri == source_uri,
        )
        result = await session.execute(stmt)
        existing_doc = result.scalar_one_or_none()

        if existing_doc and existing_doc.checksum == checksum:
            logger.info("Document unchanged, skipping", source_uri=source_uri)
            return {
                "document_id": str(existing_doc.id),
                "source_uri": source_uri,
                "status": "skipped",
                "chunks_count": 0,
            }

        # 3. Store raw asset in MinIO (or fallback storage)
        s3_key = f"{workspace_id}/{uuid.uuid4()}-{filename}"
        storage_client.upload_file(s3_key, raw_content, loaded.content_type)

        # 4. Handle versioning
        version = (existing_doc.version + 1) if existing_doc else 1
        if existing_doc:
            await session.execute(delete(Chunk).where(Chunk.document_id == existing_doc.id))
            doc_record = existing_doc
            doc_record.checksum = checksum
            doc_record.version = version
            doc_record.status = "processing"
            doc_record.embed_model = embedder.model_name
        else:
            doc_record = Document(
                workspace_id=workspace_id,
                source_uri=source_uri,
                title=loaded.title,
                checksum=checksum,
                version=version,
                status="processing",
                content_type=loaded.content_type,
                byte_size=loaded.byte_size,
                embed_model=embedder.model_name,
            )
            session.add(doc_record)

        await session.flush()

        # 5. Chunk and Embed
        text_chunks = chunk_document(clean_text)
        embed_inputs = [f"{loaded.title} > {c.section_title}\n{c.content}" for c in text_chunks]
        vectors = embedder.embed_texts(embed_inputs)

        # 6. Insert Chunks
        chunk_entities = []
        for i, c in enumerate(text_chunks):
            chunk_entities.append(
                Chunk(
                    document_id=doc_record.id,
                    workspace_id=workspace_id,
                    chunk_index=c.chunk_index,
                    section_title=c.section_title,
                    content=c.content,
                    token_count=c.token_count,
                    embedding=vectors[i],
                )
            )

        session.add_all(chunk_entities)
        doc_record.status = "indexed"
        await session.commit()

        logger.info(
            "Document successfully indexed",
            source_uri=source_uri,
            workspace_id=workspace_id,
            chunks=len(chunk_entities),
            version=version,
        )

        return {
            "document_id": str(doc_record.id),
            "source_uri": source_uri,
            "status": "indexed",
            "chunks_count": len(chunk_entities),
            "version": version,
        }

