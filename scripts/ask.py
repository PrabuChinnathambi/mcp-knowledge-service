import asyncio
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.harness.agent import ask_docs


async def main():
    if len(sys.argv) < 3:
        print("Usage: uv run python scripts/ask.py <workspace_id> <question>")
        sys.exit(1)

    workspace = sys.argv[1]
    question = " ".join(sys.argv[2:])
    user_id = os.getenv("MCP_USER_ID", "alice")

    result = await ask_docs(question=question, workspace_id=workspace, user_id=user_id)
    print("\n" + "=" * 60)
    print("HARNESS RESPONSE:")
    print("=" * 60)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
