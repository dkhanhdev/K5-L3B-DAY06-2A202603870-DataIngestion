"""TODO: evaluate retrieved evidence and preserve per-query traces."""
from typing import Any
import re
import unicodedata


def canonical(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """TODO: check source/page and enough gold evidence; keep hit@1 and hit@3 trace.

    Accept any documented alternative gold evidence. Do not infer human grounding
    or chunk coherence labels from exact string match.
    """
    golds = [{"source_id": question["gold_source_id"], "page": question["gold_page"],
              "evidence_quote": question["evidence_quote"]}] + question.get("alternative_gold", [])
    evaluated = []
    for hit in hits:
        matches = [g for g in golds if hit["document_id"] == g["source_id"]
                   and hit["page"] == g["page"]
                   and canonical(g["evidence_quote"]) in canonical(hit["text"])]
        evaluated.append({**hit, "evidence_hit": bool(matches)})
    return {**question, "hits": evaluated,
            "hit1": bool(evaluated and evaluated[0]["evidence_hit"]),
            "hit3": any(h["evidence_hit"] for h in evaluated[:3]),
            "metric_method": "same gold source/page + full evidence quote, whitespace normalized; unlisted equivalent evidence needs review"}


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """TODO: aggregate Hit@1 and Evidence Hit@3 by strategy and dev/test split."""
    groups = {}
    for row in traces:
        key = (row["strategy"], row["split"])
        groups.setdefault(key, []).append(row)
    return [{"strategy": strategy, "split": split, "n": len(rows),
             "hit1_n": sum(r["hit1"] for r in rows), "hit3_n": sum(r["hit3"] for r in rows),
             "hit1": sum(r["hit1"] for r in rows)/len(rows),
             "hit3": sum(r["hit3"] for r in rows)/len(rows),
             "retrieval_seconds": sum(r["retrieval_seconds"] for r in rows)}
            for (strategy, split), rows in sorted(groups.items())]
