import io

import docx
import openpyxl
import pytest

from packages.ingestion.loaders import DocumentLoader


def test_docx_loader():
    doc = docx.Document()
    doc.add_heading("Employee Benefits Guide", level=1)
    doc.add_paragraph("Full-time employees receive health and dental insurance.")

    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Benefit"
    table.cell(0, 1).text = "Coverage"
    table.cell(1, 0).text = "Dental"
    table.cell(1, 1).text = "80%"

    buffer = io.BytesIO()
    doc.save(buffer)
    raw_bytes = buffer.getvalue()

    loaded = DocumentLoader.load("benefits.docx", raw_bytes=raw_bytes)
    assert loaded.title == "Employee Benefits Guide"
    assert "Full-time employees receive health and dental insurance." in loaded.content
    assert "| Benefit | Coverage |" in loaded.content
    assert "| Dental | 80% |" in loaded.content
    assert loaded.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_xlsx_loader():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Compensation"

    ws.append(["Role", "Level", "Salary Range"])
    ws.append(["Software Engineer", "L4", "$120k - $160k"])
    ws.append(["Staff Engineer", "L6", "$200k - $260k"])

    buffer = io.BytesIO()
    wb.save(buffer)
    raw_bytes = buffer.getvalue()

    loaded = DocumentLoader.load("compensation.xlsx", raw_bytes=raw_bytes)
    assert "## Sheet: Compensation" in loaded.content
    assert "| Role | Level | Salary Range |" in loaded.content
    assert "| Software Engineer | L4 | $120k - $160k |" in loaded.content
    assert loaded.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_unsupported_loader_extension():
    with pytest.raises(ValueError, match="Unsupported file extension"):
        DocumentLoader.load("script.sh", raw_bytes=b"echo hello")
