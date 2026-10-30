import os
import re
from dataclasses import dataclass
import fitz  # PyMuPDF


@dataclass
class LoadedDocument:
    title: str
    content: str
    content_type: str
    byte_size: int


class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}

    @classmethod
    def load(cls, file_path: str, raw_bytes: bytes | None = None) -> LoadedDocument:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {ext}")

        if raw_bytes is None:
            with open(file_path, "rb") as f:
                raw_bytes = f.read()

        byte_size = len(raw_bytes)
        fallback_title = os.path.splitext(os.path.basename(file_path))[0]

        if ext in {".md", ".txt"}:
            text = raw_bytes.decode("utf-8", errors="replace")
            # Extract first markdown header if available
            heading_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            title = heading_match.group(1).strip() if heading_match else fallback_title
            content_type = "text/markdown" if ext == ".md" else "text/plain"
            return LoadedDocument(title=title, content=text, content_type=content_type, byte_size=byte_size)

        elif ext == ".pdf":
            doc = fitz.open(stream=raw_bytes, filetype="pdf")
            extracted_pages = []
            for page in doc:
                extracted_pages.append(page.get_text())
            doc.close()
            content = "\n\n".join(extracted_pages)
            return LoadedDocument(title=fallback_title, content=content, content_type="application/pdf", byte_size=byte_size)

        raise ValueError(f"Unhandled loader for extension: {ext}")

