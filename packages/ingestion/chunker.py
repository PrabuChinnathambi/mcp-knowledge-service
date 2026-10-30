import re
from dataclasses import dataclass
from packages.core.config import get_settings

settings = get_settings()


@dataclass
class TextChunk:
    chunk_index: int
    section_title: str
    content: str
    token_count: int


def split_into_sections(text: str) -> list[tuple[str, str]]:
    """Splits markdown content into tuples of (heading, section_body)."""
    sections: list[tuple[str, str]] = []
    current_heading = "Introduction"
    current_lines: list[str] = []

    for line in text.splitlines():
        heading_match = re.match(r"^#{1,6}\s+(.*)$", line)
        if heading_match:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_heading, body))
            current_heading = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    body = "\n".join(current_lines).strip()
    if body:
        sections.append((current_heading, body))

    return sections if sections else [("General", text)]


def chunk_document(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[TextChunk]:
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if overlap >= size:
        raise ValueError("overlap must be strictly less than chunk_size")

    sections = split_into_sections(text)
    chunks: list[TextChunk] = []
    global_index = 0

    for section_title, body in sections:
        # Normalize excessive newlines
        clean_body = re.sub(r"\n{3,}", "\n\n", body).strip()
        step = size - overlap

        for start in range(0, len(clean_body), step):
            piece = clean_body[start : start + size].strip()
            if len(piece) >= 20:  # Skip trivial fragments
                # Approximate token count (1 token ~= 4 chars)
                token_est = max(1, len(piece) // 4)
                chunks.append(
                    TextChunk(
                        chunk_index=global_index,
                        section_title=section_title,
                        content=piece,
                        token_count=token_est,
                    )
                )
                global_index += 1

            if start + size >= len(clean_body):
                break

    return chunks

