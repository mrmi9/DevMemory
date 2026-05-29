from pathlib import Path

from app.services.chunking import clean_text


SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "word",
    ".md": "markdown",
    ".markdown": "markdown",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
}


def detect_document_kind(filename: str, content_type: str = "") -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[suffix]
    if content_type == "application/pdf":
        return "pdf"
    if content_type in {"text/markdown", "text/x-markdown"}:
        return "markdown"
    if content_type.startswith("image/"):
        return "image"
    raise ValueError(f"Unsupported document type for {filename}")


def parse_document_text(path: Path, kind: str) -> str:
    if kind == "markdown":
        return clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    if kind == "word":
        return _parse_word(path)
    if kind == "pdf":
        return _parse_pdf(path)
    if kind == "image":
        return _parse_image(path)
    raise ValueError(f"Unsupported document kind: {kind}")


def _parse_word(path: Path) -> str:
    try:
        from docx import Document as DocxDocument
    except ImportError as exc:
        raise RuntimeError("python-docx is required to parse Word documents") from exc

    document = DocxDocument(str(path))
    return clean_text("\n".join(paragraph.text for paragraph in document.paragraphs))


def _parse_pdf(path: Path) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required to parse PDF documents") from exc

    parts: list[str] = []
    with fitz.open(str(path)) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")
            if text.strip():
                parts.append(f"[page:{page_number}]\n{text}")
    return clean_text("\n".join(parts))


def _parse_image(path: Path) -> str:
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError("PaddleOCR is required to parse image notes") from exc

    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    result = ocr.ocr(str(path), cls=True)
    lines: list[str] = []
    for page in result:
        for item in page:
            if len(item) >= 2 and item[1]:
                lines.append(str(item[1][0]))
    return clean_text("\n".join(lines))
