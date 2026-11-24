import argparse
import asyncio
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.harness.agent import ask_docs


async def main():
    parser = argparse.ArgumentParser(description="Query mcp-knowledge-service with multi-LLM support.")
    parser.add_argument("workspace_id", nargs="?", default=None, help="Target workspace (e.g. hr-docs)")
    parser.add_argument("question", nargs="?", default=None, help="Question to ask grounded in workspace documents")
    parser.add_argument(
        "--workspace",
        "-w",
        default=None,
        dest="workspace_flag",
        help="Optional workspace flag (e.g. --workspace hr-docs)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Optional local LLM model (e.g. qwen2.5:7b-instruct, llama3.2:3b, deepseek-r1:1.5b)",
    )
    args = parser.parse_args()

    if args.workspace_flag:
        workspace_id = args.workspace_flag
        question = args.question or args.workspace_id
    else:
        workspace_id = args.workspace_id
        question = args.question

    if not workspace_id or not question:
        parser.error(
            "Both workspace and question are required.\n"
            "Examples:\n"
            "  uv run python scripts/ask.py hr-docs 'What is the probation period?'\n"
            "  uv run python scripts/ask.py 'What is the probation period?' --workspace hr-docs"
        )

    user_id = os.getenv("MCP_USER_ID", "alice")

    result = await ask_docs(
        question=question,
        workspace_id=workspace_id,
        user_id=user_id,
        model=args.model,
    )
    print("\n" + "=" * 60)
    print("HARNESS RESPONSE:")
    print("=" * 60)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
