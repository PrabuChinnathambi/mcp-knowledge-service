import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.retrieval.hybrid import hybrid_retrieve


async def main():
    if len(sys.argv) < 3:
        print("Usage: uv run python scripts/search.py <workspace_id> <query>")
        sys.exit(1)

    workspace = sys.argv[1]
    query = " ".join(sys.argv[2:])

    result = await hybrid_retrieve(query=query, workspace_id=workspace, top_k=5)
    print(f"\nTrace: {result.trace}")
    print(f"Top Vector Score: {result.top_vector_score:.4f}\n")
    print(f"{'TITLE':<25} | {'SECTION':<25} | {'RRF SCORE':<10} | {'VEC SCORE':<10}")
    print("-" * 78)
    for c in result.chunks:
        vec_s = f"{c.vector_score:.4f}" if c.vector_score is not None else "N/A"
        print(f"{c.title[:24]:<25} | {c.section_title[:24]:<25} | {c.score:<10.4f} | {vec_s:<10}")


if __name__ == "__main__":
    asyncio.run(main())
