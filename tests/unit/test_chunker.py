import pytest
from packages.ingestion.chunker import chunk_document, split_into_sections


def test_split_into_sections():
    text = "# Policy\n## Annual Leave\n24 days per year.\n## Sick Leave\n10 days per year."
    sections = split_into_sections(text)
    assert len(sections) == 2
    assert sections[0][0] == "Annual Leave"
    assert "24 days" in sections[0][1]
    assert sections[1][0] == "Sick Leave"
    assert "10 days" in sections[1][1]


def test_chunk_document_preserves_section():
    text = "## Webhooks\nRetries are up to 5 times."
    chunks = chunk_document(text, chunk_size=500, chunk_overlap=50)
    assert len(chunks) == 1
    assert chunks[0].section_title == "Webhooks"
    assert "Retries" in chunks[0].content


def test_chunk_document_rejects_invalid_overlap():
    with pytest.raises(ValueError, match="strictly less than"):
        chunk_document("Sample text", chunk_size=100, chunk_overlap=100)

