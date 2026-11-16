import io
import os
import re
from dataclasses import dataclass

import docx
import fitz  # PyMuPDF
import openpyxl


@dataclass
class LoadedDocument:
    title: str
    content: str
    content_type: str
    byte_size: int


class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".xlsx"}

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

        elif ext == ".docx":
            doc = docx.Document(io.BytesIO(raw_bytes))
            sections = []

            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                # Handle heading styles
                if p.style and p.style.name and p.style.name.startswith("Heading"):
                    level_str = p.style.name.replace("Heading", "").strip()
                    level = int(level_str) if level_str.isdigit() else 2
                    hashes = "#" * max(1, min(6, level))
                    sections.append(f"{hashes} {text}")
                else:
                    sections.append(text)

            # Extract tables into Markdown format
            for table in doc.tables:
                table_rows = []
                for r_idx, row in enumerate(table.rows):
                    cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    table_rows.append("| " + " | ".join(cells) + " |")
                    if r_idx == 0:
                        table_rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
                if table_rows:
                    sections.append("\n" + "\n".join(table_rows) + "\n")

            content = "\n\n".join(sections)
            heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = heading_match.group(1).strip() if heading_match else fallback_title
            return LoadedDocument(
                title=title,
                content=content,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                byte_size=byte_size,
            )

        elif ext == ".xlsx":
            wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=True)
            sheets_md = []
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                rows = list(sheet.iter_rows(values_only=True))
                if not rows:
                    continue
                sheets_md.append(f"## Sheet: {sheet_name}")
                table_lines = []
                for r_idx, row in enumerate(rows):
                    if not any(row):
                        continue
                    cells = [str(c if c is not None else "").strip().replace("\n", " ") for c in row]
                    table_lines.append("| " + " | ".join(cells) + " |")
                    if r_idx == 0:
                        table_lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
                if table_lines:
                    sheets_md.append("\n".join(table_lines))

            content = "\n\n".join(sheets_md)
            return LoadedDocument(
                title=fallback_title,
                content=content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                byte_size=byte_size,
            )

        raise ValueError(f"Unhandled loader for extension: {ext}")
