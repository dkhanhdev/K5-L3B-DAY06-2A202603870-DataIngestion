"""Extract only the configured corpus; run from any working directory."""
import hashlib
import json
import unicodedata
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]


def main():
    config = json.loads((ROOT / "data/corpus_config.json").read_text(encoding="utf-8"))
    log = ROOT / "results/corpus_preparation.json"
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        path = ROOT / config["source_path"]
        reader = PdfReader(path)
        start, end = config["page_start"], config["page_end"]
        if not 1 <= start <= end <= len(reader.pages):
            raise ValueError("Invalid inclusive physical PDF page range")
        pages = []
        for number in range(start, end + 1):
            try:
                raw = reader.pages[number - 1].extract_text() or ""
            except Exception as exc:
                raise RuntimeError(f"Cannot extract PDF page {number}") from exc
            text = "\n".join(" ".join(line.split()) for line in unicodedata.normalize("NFC", raw).splitlines()).strip()
            if not text:
                raise ValueError(f"PDF page {number} is empty or needs OCR")
            sections = [s for s in config["sections"] if s["start"] <= number <= s["end"]]
            if len(sections) != 1:
                raise ValueError(f"Ambiguous or missing section for page {number}")
            pages.append({"document_id": config["document_id"], "source": config["source_path"],
                          "page": number, "text": text,
                          "metadata": {**config["metadata"], "section": sections[0]["section"],
                                       "printed_page": number + config["printed_page_offset"]}})
        if len(pages) < 30:
            raise ValueError("Fewer than 30 selected content pages")
        manifest = {**config, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "total_physical_pages": len(reader.pages), "selected_content_pages": len(pages),
                    "counting_rule": "Physical PDF 75-104 (printed 55-84), chapter 2 body, excludes front matter, chapter cover and references; figures remain within source pages.",
                    "section_assignment": "Page-level labels from contents; transition pages may contain the previous section too. Box 2.1 belongs to Policy implications.",
                    "pages": [{"page_id": f"{config['document_id']}:p{p['page']}", "page": p["page"],
                               "printed_page": p["metadata"]["printed_page"], "characters": len(p["text"])} for p in pages]}
        output = ROOT / "data/processed/pages.jsonl"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pages), encoding="utf-8")
        (ROOT / "data/manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log.write_text(json.dumps({"status": "ok", "pages": len(pages), "empty_pages": []}, indent=2) + "\n", encoding="utf-8")
        print(f"Prepared {len(pages)} pages: PDF {start}-{end}")
    except Exception as exc:
        log.write_text(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
