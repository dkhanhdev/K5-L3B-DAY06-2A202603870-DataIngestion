"""Page-local chunking with exact character offsets and stable content IDs."""
import hashlib
import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Require size > 0 and 0 <= overlap < size")
    result = []
    start = 0
    while start < len(page.text):
        end = min(start + size, len(page.text))
        result.append(_chunk(page, start, end, f"fixed:{size}:{overlap}"))
        if end == len(page.text):
            break
        start = end - overlap
    return result


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Recover paragraph-like blocks from PDF line breaks, then pack to max_size.

    Blank lines, bullets, short headings and sentence-final newlines are boundaries.
    This is a heuristic, not PDF layout reconstruction. Oversized blocks split at
    sentence/word boundaries without overlap; exact source offsets are retained.
    """
    if max_size < 2:
        raise ValueError("max_size must be >= 2")
    boundaries = [0]
    for match in re.finditer(r"\n+", page.text):
        before = page.text[boundaries[-1]:match.start()].strip()
        after = page.text[match.end():]
        if (len(match.group()) > 1 or before.endswith((".", "?", "!", ":"))
                or after.startswith("•") or (0 < len(before) < 70 and not before[-1:].islower())):
            boundaries.append(match.end())
    boundaries.append(len(page.text))
    blocks = []
    for left, right in zip(boundaries, boundaries[1:]):
        while right - left > max_size:
            window = page.text[left:left + max_size]
            choices = [m.end() for m in re.finditer(r"[.!?]\s+", window)]
            cut = choices[-1] if choices else window.rfind(" ") + 1
            cut = cut if cut > 0 else max_size
            blocks.append((left, left + cut))
            left += cut
        if right > left:
            blocks.append((left, right))
    result = []
    start = end = None
    for left, right in blocks:
        if start is not None and right - start > max_size:
            result.append(_chunk(page, start, end, f"paragraph:{max_size}"))
            start = None
        if start is None:
            start = left
        end = right
    if start is not None:
        result.append(_chunk(page, start, end, f"paragraph:{max_size}"))
    return result


def _chunk(page, start, end, method):
    text = page.text[start:end]
    key = f"{page.document_id}:{page.page}:{method}:{start}:{end}:{text}"
    return Chunk(hashlib.sha256(key.encode()).hexdigest()[:32], page.document_id,
                 page.source, page.page, text,
                 {**page.metadata, "char_start": start, "char_end": end, "chunking": method})
