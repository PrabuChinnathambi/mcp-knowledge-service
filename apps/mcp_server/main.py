from mcp.server.mcpserver import MCPServer
from packages.core.config import get_settings
from packages.harness.agent import ask_docs
from packages.harness.auth import USER_DIRECTORY, assert_can_write, assert_workspace_access
from packages.ingestion.pipeline import ingest_document_file
from packages.observability.logger import logger
from packages.retrieval.hybrid import hybrid_retrieve

settings = get_settings()

mcp = MCPServer(
    name="knowledge-service",
    instructions="Enterprise knowledge retrieval server with citation-verified document grounding.",
)


@mcp.tool(name="list_collections", description="List accessible knowledge workspaces for the current user.")
async def list_collections() -> list[str]:
    user_id = settings.MCP_USER_ID
    logger.info("mcp_tool_called", tool="list_collections", user_id=user_id)
    user_record = USER_DIRECTORY.get(user_id, {"workspaces": []})
    return user_record["workspaces"]


@mcp.tool(
    name="search_knowledge",
    description="Hybrid semantic and keyword search. Returns ranked document chunks with relevance scores.",
)
async def search_knowledge(workspace_id: str, query: str, top_k: int = 5) -> dict:
    user_id = settings.MCP_USER_ID
    logger.info("mcp_tool_called", tool="search_knowledge", workspace=workspace_id, user_id=user_id)
    assert_workspace_access(user_id, workspace_id)
    retrieval = await hybrid_retrieve(query=query, workspace_id=workspace_id, top_k=top_k)
    return {
        "results": [
            {
                "chunk_id": c.id,
                "title": c.title,
                "section": c.section_title,
                "content": c.content,
                "score": c.score,
                "source_uri": c.source_uri,
            }
            for c in retrieval.chunks
        ],
        "trace": retrieval.trace,
    }


@mcp.tool(
    name="ask_docs",
    description="Ask a question grounded in documentation. Returns a verified answer with citations, or refuses.",
)
async def ask_docs_tool(workspace_id: str, question: str) -> dict:
    user_id = settings.MCP_USER_ID
    logger.info("mcp_tool_called", tool="ask_docs", workspace=workspace_id, user_id=user_id)
    return await ask_docs(question=question, workspace_id=workspace_id, user_id=user_id)


@mcp.tool(
    name="ingest_document",
    description="Index a document into a workspace. Requires write permissions.",
)
async def ingest_document_tool(workspace_id: str, file_path: str) -> dict:
    user_id = settings.MCP_USER_ID
    logger.info("mcp_tool_called", tool="ingest_document", workspace=workspace_id, user_id=user_id)
    assert_can_write(user_id, workspace_id)
    return await ingest_document_file(file_path=file_path, workspace_id=workspace_id)


if __name__ == "__main__":
    # Runs over stdio JSON-RPC transport by default in mcp 2.x
    mcp.run()
