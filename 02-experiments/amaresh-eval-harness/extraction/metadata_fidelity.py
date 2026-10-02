from __future__ import annotations

import difflib
import time
from typing import Optional

import requests

CROSSREF_BASE = "https://api.crossref.org/works"
TITLE_MATCH_THRESHOLD = 0.80
REQUEST_TIMEOUT = 10
RATE_LIMIT_SLEEP = 0.15


def fetch_crossref_record(doi: str, mailto: Optional[str] = None) -> Optional[dict]:
    headers = {}
    params = {}
    if mailto:
        headers["User-Agent"] = f"clinical-search-benchmark/1.0 (mailto:{mailto})"
        params["mailto"] = mailto
    try:
        resp = requests.get(
            f"{CROSSREF_BASE}/{doi}",
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        return resp.json().get("message")
    except requests.RequestException:
        return None


def title_similarity(a: str, b: str) -> float:
    a_norm = " ".join(a.lower().split())
    b_norm = " ".join(b.lower().split())
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()


def author_last_names(crossref_authors: list[dict]) -> set[str]:
    return {
        a.get("family", "").lower()
        for a in crossref_authors or []
        if a.get("family")
    }


def extracted_authors_from_text(text: str) -> set[str]:
    tokens = [t.strip(",.") for t in text.split()]
    return {
        tokens[i - 1].lower()
        for i, t in enumerate(tokens)
        if t in ("MD,", "MD", "MD*", "PhD", "PhD,") and i > 0
    }


def check_paper_metadata_fidelity(
    paper_slug: str,
    extracted_title: str,
    extracted_first_chunk_text: str,
    dois: list[str],
    mailto: Optional[str] = None,
) -> dict:
    if not dois:
        return {
            "paper_slug": paper_slug,
            "status": "no_doi_found",
            "title_similarity": None,
            "author_overlap": None,
        }

    record = None
    used_doi = None
    for doi in dois:
        record = fetch_crossref_record(doi, mailto=mailto)
        time.sleep(RATE_LIMIT_SLEEP)
        if record:
            used_doi = doi
            break

    if not record:
        return {
            "paper_slug": paper_slug,
            "status": "crossref_lookup_failed",
            "dois_tried": dois,
            "title_similarity": None,
            "author_overlap": None,
        }

    crossref_titles = record.get("title") or [""]
    crossref_title = crossref_titles[0] if crossref_titles else ""
    sim = title_similarity(extracted_title, crossref_title)

    crossref_last_names = author_last_names(record.get("author", []))
    extracted_names = extracted_authors_from_text(extracted_first_chunk_text)
    overlap = (
        len(crossref_last_names & extracted_names) / len(crossref_last_names)
        if crossref_last_names
        else None
    )

    return {
        "paper_slug": paper_slug,
        "status": "pass" if sim >= TITLE_MATCH_THRESHOLD else "title_mismatch",
        "doi_used": used_doi,
        "extracted_title": extracted_title,
        "crossref_title": crossref_title,
        "title_similarity": round(sim, 3),
        "crossref_authors": sorted(crossref_last_names),
        "extracted_author_hits": sorted(extracted_names),
        "author_overlap_ratio": round(overlap, 3) if overlap is not None else None,
    }


def run_metadata_fidelity(
    papers: dict[str, list[dict]],
    doi_map: dict[str, list[str]],
    mailto: Optional[str] = None,
) -> dict:
    results = []
    for slug, chunks in papers.items():
        first = sorted(chunks, key=lambda c: c.get("chunk_index", 0))[0]
        result = check_paper_metadata_fidelity(
            paper_slug=slug,
            extracted_title=first.get("section_path") or first.get("embed_text", "")[:150],
            extracted_first_chunk_text=first.get("text", ""),
            dois=doi_map.get(slug, []),
            mailto=mailto,
        )
        results.append(result)

    passed = sum(1 for r in results if r["status"] == "pass")
    no_doi = sum(1 for r in results if r["status"] == "no_doi_found")
    failed_lookup = sum(1 for r in results if r["status"] == "crossref_lookup_failed")
    mismatched = sum(1 for r in results if r["status"] == "title_mismatch")

    return {
        "papers_checked": len(results),
        "passed": passed,
        "no_doi_found": no_doi,
        "crossref_lookup_failed": failed_lookup,
        "title_mismatch": mismatched,
        "pass_rate": round(passed / len(results), 3) if results else 0.0,
        "detail": results,
    }