from typing import Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    workspace_id: str
    title: str
    source_uri: str
    version: int
    status: str
    chunks_count: int = 0


class ScoredChunkSchema(BaseModel):
    id: str
    document_id: str
    workspace_id: str
    section_title: str
    content: str
    title: str
    source_uri: str
    score: float
    vector_score: float | None = None


class CitationSchema(BaseModel):
    chunk_id: str
    title: str
    section: str
    source_uri: str


class AskDocsResponse(BaseModel):
    trace_id: str
    status: str
    answer: str
    citations: list[CitationSchema] = Field(default_factory=list)
    error: str | None = None

