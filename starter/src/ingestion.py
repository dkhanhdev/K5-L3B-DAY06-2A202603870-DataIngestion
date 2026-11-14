"""Read and normalize source data. TODO: implement functions."""
from pathlib import Path
import unicodedata
from pypdf import PdfReader
from .models import DocumentPage


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """TODO: extract each physical page; keep its page number and source.

    Detect and record pages with no text. OCR, when needed, is a separate step.
    """
    result = []
    for number, page in enumerate(PdfReader(path).pages, 1):
        text = normalize_text(page.extract_text() or "")
        result.append(DocumentPage(document_id, source, number, text, {"extraction_status": "ok" if text else "empty_needs_review"}))
    return result


def normalize_text(text: str) -> str:
    """TODO: normalize Unicode and whitespace without discarding useful structure."""
    return "\n".join(" ".join(line.split()) for line in unicodedata.normalize("NFC", text).splitlines()).strip()
