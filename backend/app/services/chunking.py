from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str
    char_start: int
    char_end: int


def clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in normalized.split("\n"):
        compact = re.sub(r"[ \t\f\v]+", " ", line).strip()
        if compact:
            lines.append(compact)
    return "\n".join(lines)


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 160) -> list[TextChunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be non-negative and smaller than max_chars")

    cleaned = clean_text(text)
    if not cleaned:
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(cleaned):
        end = min(start + max_chars, len(cleaned))
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(TextChunk(index=index, text=chunk, char_start=start, char_end=end))
            index += 1
        if end == len(cleaned):
            break
        start = end - overlap
    return chunks
