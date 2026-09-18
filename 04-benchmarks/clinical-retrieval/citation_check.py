# Copyright 2026 Anacodic AI Labs — https://anacodicai.org
# SPDX-License-Identifier: Apache-2.0

"""Deterministic citation verification for benchmark answers.

Ported from `specialist-rag`'s `tests/benchmark/citation_check.py`,
branch `origin/fix-completion` at commit `130ff868` (not on `main`).

`eval.py`'s own `extract_citations()` pulls PMCIDs and DOIs out of an answer
and stops there — it never checks whether those identifiers appear in the
papers actually retrieved. An answer citing a plausible-looking DOI that came
from nowhere passes today. This module finishes that job: is every
identifier the model cited actually present in the evidence it was given?

This is the offline twin of `01-modules/01-tools/05-gate/01-grounding-check.ipynb`'s
grounding check. Same question — is this citation real? — asked at two
different times. Gate asks it live, on one answer, and refuses. This module
asks it afterwards, over a stored run, and counts. Two modules checking "the
same" thing in one repo is exactly the duplication this lab tries to stop —
here it is deliberate, because the two run at different points in the
pipeline and neither can do the other's job.

Deliberately free of any product-specific import so it is unit-testable
with plain dicts, and cheap enough to run on every benchmark query without a
judge call.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

# PMC identifiers are "PMC" + digits.
PMCID_RE = re.compile(r"PMC\d{5,8}", re.IGNORECASE)

# DOIs have no formal terminator, so a greedy \S+ swallows trailing prose
# punctuation ("...10.1234/abc)." -> "10.1234/abc).") and would then never
# match a stored DOI without the trailing-punctuation strip below.
DOI_RE = re.compile(r"10\.\d{4,}/\S+")
_DOI_TRAILING_PUNCT = ".,;:)]}>\"'"


def _norm_doi(raw: str) -> str:
    """Lowercase, strip a doi.org prefix, and drop trailing sentence punctuation."""
    d = (raw or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if d.startswith(prefix):
            d = d[len(prefix):]
    return d.rstrip(_DOI_TRAILING_PUNCT).strip()


def _norm_pmcid(raw: str) -> str:
    return (raw or "").strip().upper()


def extract_citations(text: str) -> tuple[list[str], list[str]]:
    """Return (pmcids, dois) cited in free-text, normalized and de-duplicated."""
    pmcids: list[str] = []
    for m in PMCID_RE.findall(text or ""):
        n = _norm_pmcid(m)
        if n and n not in pmcids:
            pmcids.append(n)

    dois: list[str] = []
    for m in DOI_RE.findall(text or ""):
        n = _norm_doi(m)
        if n and n not in dois:
            dois.append(n)
    return pmcids, dois


def known_identifiers(papers: Iterable[dict[str, Any]]) -> tuple[set[str], set[str]]:
    """Collect the PMCIDs and DOIs the model was actually given.

    Uses explicit identifier fields rather than substring-matching one big
    blob of concatenated paper text, so a citation cannot be "verified" by
    coincidentally appearing inside an unrelated abstract.
    """
    pmcids: set[str] = set()
    dois: set[str] = set()
    for p in papers or []:
        pmcid = _norm_pmcid(str(p.get("pmcid") or ""))
        if pmcid:
            pmcids.add(pmcid)
        # pmc_url is the link actually rendered to a reader; a PMCID reachable
        # only through that URL still counts as grounded.
        for found in PMCID_RE.findall(str(p.get("pmc_url") or "")):
            pmcids.add(_norm_pmcid(found))
        doi = _norm_doi(str(p.get("doi") or ""))
        if doi:
            dois.add(doi)
    return pmcids, dois


def verify_citations(answer: str, papers: list[dict[str, Any]]) -> dict[str, Any]:
    """Check every identifier cited in `answer` against the retrieved `papers`.

    `citation_pass` requires both that the answer cites something at all (an
    uncited clinical answer is not acceptable) and that nothing it cited was
    invented.
    """
    cited_pmcids, cited_dois = extract_citations(answer)
    known_pmcids, known_dois = known_identifiers(papers)

    verified_pmcids = [c for c in cited_pmcids if c in known_pmcids]
    verified_dois = [c for c in cited_dois if c in known_dois]
    hallucinated_pmcids = [c for c in cited_pmcids if c not in known_pmcids]
    hallucinated_dois = [c for c in cited_dois if c not in known_dois]

    has_citation = bool(cited_pmcids or cited_dois)
    hallucinated = bool(hallucinated_pmcids or hallucinated_dois)

    return {
        "has_citation": has_citation,
        "all_verified": has_citation and not hallucinated,
        "citation_pass": has_citation and not hallucinated,
        "cited_pmcids": cited_pmcids,
        "cited_dois": cited_dois,
        "verified_pmcids": verified_pmcids,
        "verified_dois": verified_dois,
        "hallucinated_pmcids": hallucinated_pmcids,
        "hallucinated_dois": hallucinated_dois,
    }


__all__ = [
    "extract_citations",
    "known_identifiers",
    "verify_citations",
    "PMCID_RE",
    "DOI_RE",
]
