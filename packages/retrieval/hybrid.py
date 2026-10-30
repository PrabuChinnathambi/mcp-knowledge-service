import time
import uuid
from dataclasses import dataclass
from sqlalchemy import select, text
from packages.domain.models import Chunk, Document
from packages.infrastructure.database import AsyncSessionLocal
from packages.retrieval.embeddings import get_embedding_provider
from packages.observability.logger import logger

embedder = get_embedding_provider()


@dataclass
class ScoredChunk:
    id: str
    document_id: str
    workspace_id: str
    section_title: str
    content: str
    title: str
    source_uri: str
    score: float
    vector_score: float | None = None


@dataclass
class RetrievalResult:
    chunks: list[ScoredChunk]
    top_vector_score: float
    trace: dict


def rrf(rank_lists: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for r_list in rank_lists:
        for rank, chunk_id in enumerate(r_list):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (k + rank + 1))
    return scores


async def hybrid_retrieve(
    query: str,
    workspace_id: str,
    top_k: int = 5,
) -> RetrievalResult:
    start_time = time.time()

    # 1. Generate query embedding
    query_vector = embedder.embed_texts([query])[0]

    async with AsyncSessionLocal() as session:
        # 2. Vector Search (Cosine distance: <=> operator)
        vector_stmt = text(
            """
            SELECT id::text, 1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM chunks
            WHERE workspace_id = :workspace_id
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT 20;
            """
        )
        vec_res = await session.execute(
            vector_stmt,
            {"query_vec": str(query_vector), "workspace_id": workspace_id},
        )
        vector_hits = [(str(row[0]), float(row[1])) for row in vec_res.fetchall()]

        # 3. Full-Text Search (tsvector websearch_to_tsquery)
        fts_stmt = text(
            """
            SELECT id::text, ts_rank_cd(tsv_content, websearch_to_tsquery('english', :query)) as rank
            FROM chunks
            WHERE workspace_id = :workspace_id
              AND tsv_content @@ websearch_to_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT 20;
            """
        )
        fts_res = await session.execute(
            fts_stmt,
            {"query": query, "workspace_id": workspace_id},
        )
        fts_hits = [str(row[0]) for row in fts_res.fetchall()]

        # 4. Reciprocal Rank Fusion
        fused_scores = rrf([[h[0] for h in vector_hits], fts_hits], k=60)
        sorted_chunk_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)[:top_k]

        if not sorted_chunk_ids:
            return RetrievalResult(
                chunks=[],
                top_vector_score=0.0,
                trace={"vector_hits": 0, "fts_hits": 0, "latency_ms": int((time.time() - start_time) * 1000)},
            )

        # 5. Hydrate Chunk Entities
        chunk_uuids = [uuid.UUID(uid) for uid in sorted_chunk_ids]
        hydrate_stmt = (
            select(
                Chunk.id,
                Chunk.document_id,
                Chunk.workspace_id,
                Chunk.section_title,
                Chunk.content,
                Document.title,
                Document.source_uri,
            )
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.id.in_(chunk_uuids))
        )
        hydrate_res = await session.execute(hydrate_stmt)
        hydrated_map = {str(row.id): row for row in hydrate_res.fetchall()}
        vec_score_map = dict(vector_hits)

        results: list[ScoredChunk] = []
        for cid in sorted_chunk_ids:
            if cid in hydrated_map:
                row = hydrated_map[cid]
                results.append(
                    ScoredChunk(
                        id=cid,
                        document_id=str(row.document_id),
                        workspace_id=row.workspace_id,
                        section_title=row.section_title,
                        content=row.content,
                        title=row.title,
                        source_uri=row.source_uri,
                        score=fused_scores[cid],
                        vector_score=vec_score_map.get(cid),
                    )
                )

        top_vector_score = vector_hits[0][1] if vector_hits else 0.0
        latency_ms = int((time.time() - start_time) * 1000)

        return RetrievalResult(
            chunks=results,
            top_vector_score=top_vector_score,
            trace={
                "query": query,
                "vector_hits": len(vector_hits),
                "fts_hits": len(fts_hits),
                "returned": len(results),
                "latency_ms": latency_ms,
            },
        )

