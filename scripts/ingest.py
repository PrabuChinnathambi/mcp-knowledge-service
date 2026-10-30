import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.ingestion.pipeline import ingest_document_file


async def main():
    if len(sys.argv) < 3:
        print("Usage: uv run python scripts/ingest.py <path_to_file_or_dir> <workspace_id>")
        sys.exit(1)

    target_path = sys.argv[1]
    workspace = sys.argv[2]

    if os.path.isfile(target_path):
        res = await ingest_document_file(target_path, workspace)
        print(f"Result: {res}")
    elif os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for file in files:
                if any(file.endswith(ext) for ext in [".md", ".txt", ".pdf"]):
                    full_p = os.path.join(root, file)
                    res = await ingest_document_file(full_p, workspace)
                    print(f"File {file}: {res['status']} ({res['chunks_count']} chunks)")


if __name__ == "__main__":
    asyncio.run(main())
