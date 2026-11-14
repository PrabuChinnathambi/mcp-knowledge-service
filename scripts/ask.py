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
    parser.add_argument("workspace_id", help="Target workspace (e.g. hr-docs)")
    parser.add_argument("question", help="Question to ask grounded in workspace documents")
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Optional local LLM model (e.g. qwen2.5:7b-instruct, llama3.2:3b, deepseek-r1:1.5b)",
    )
    args = parser.parse_args()

    user_id = os.getenv("MCP_USER_ID", "alice")

    result = await ask_docs(
        question=args.question,
        workspace_id=args.workspace_id,
        user_id=user_id,
        model=args.model,
    )
    print("\n" + "=" * 60)
    print("HARNESS RESPONSE:")
    print("=" * 60)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
