"""Pass/fail rubric for the clinical-retrieval benchmark.

Ported from `specialist-rag`'s `tests/benchmark/pass_rubric.py`, branch
`origin/fix-completion` at commit `130ff868` (not on `main`). The original
carried a department-specific docstring ("breast-reconstruction benchmark");
generalized here, since nothing in the rubric structure itself is specific
to one clinical department.

The cookbook had no rubric of any kind before this file — nothing defined
the threshold a run has to clear to count as a pass. The threshold VALUES
below are a judgement made for one corpus and carried across as defaults,
not a constant of nature; whoever runs this against a different corpus
should expect to defend or change them, not assume they're correct.

Four separate judgements, not one undifferentiated pass/fail, so a failure
is attributable to a stage: `evaluate_retrieval_pass`, `evaluate_deepeval_pass`,
`evaluate_citation_pass`, `evaluate_question_pass`.
"""

from __future__ import annotations

from typing import Any

from citation_check import verify_citations

_RETRIEVAL_PASS_KEYWORD = True  # >=1 keyword in top-20
_RETRIEVAL_PASS_OVERLAP = 1  # >=1 expected paper in top-10
_RETRIEVAL_GOOD_OVERLAP_RATIO = 0.5
_RCS_MAJORITY_THRESHOLD = 0.5
_DEEPEVAL_FAITHFULNESS_THRESHOLD = 0.70
_DEEPEVAL_ANSWER_RELEVANCY_THRESHOLD = 0.70
_DEEPEVAL_CONTEXTUAL_RECALL_THRESHOLD = 0.60


def _paper_text(paper: dict) -> str:
    return " ".join(
        [
            str(paper.get("title") or ""),
            str(paper.get("summary") or ""),
            str(paper.get("text") or ""),
            str(paper.get("authors") or ""),
        ]
    ).lower()


def compute_paper_overlap(
    papers: list[dict],
    expected_papers: list[str],
    *,
    top_n: int = 10,
) -> dict[str, Any]:
    if not expected_papers:
        return {
            "expected_papers": [],
            "papers_found": [],
            "papers_missing": [],
            "overlap_count": 0,
            "overlap_ratio": 0.0,
            "overlap_pass": True,
            "overlap_good": True,
        }

    top = papers[:top_n]
    corpus = " ".join(_paper_text(p) for p in top)
    found: list[str] = []
    missing: list[str] = []
    for ep in expected_papers:
        needle = ep.lower().replace(" et al.", "").replace(" et al", "").strip()
        first_token = needle.split()[0] if needle else ""
        if needle and (needle in corpus or (first_token and first_token in corpus)):
            found.append(ep)
        else:
            missing.append(ep)

    ratio = len(found) / len(expected_papers)
    return {
        "expected_papers": expected_papers,
        "papers_found": found,
        "papers_missing": missing,
        "overlap_count": len(found),
        "overlap_ratio": round(ratio, 3),
        "overlap_pass": len(found) >= _RETRIEVAL_PASS_OVERLAP,
        "overlap_good": ratio >= _RETRIEVAL_GOOD_OVERLAP_RATIO,
    }


def evaluate_retrieval_pass(result: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    papers = result.get("papers") or []
    paper_count = int(result.get("paper_count") or len(papers))
    keywords_found = result.get("keywords_found") or []
    overlap = result.get("paper_overlap") or compute_paper_overlap(
        papers, case.get("expected_papers") or []
    )

    rcs_scores = [p.get("rcs_score") or 0 for p in papers]
    rcs_ge_5 = sum(1 for s in rcs_scores if s >= 5)
    rcs_majority = (
        (rcs_ge_5 / len(rcs_scores)) >= _RCS_MAJORITY_THRESHOLD if rcs_scores else False
    )
    evidence_assigned = all(p.get("evidence_level") for p in papers) if papers else False

    checks = {
        "papers_returned": paper_count > 0,
        "keyword_coverage": bool(keywords_found),
        "paper_overlap": bool(overlap.get("overlap_pass")),
        "rcs_majority_ge_5": rcs_majority,
        "evidence_levels_assigned": evidence_assigned,
    }
    passed = all(checks.values()) and not result.get("error")
    return {"retrieval_pass": passed, "retrieval_checks": checks, "paper_overlap": overlap}


def evaluate_deepeval_pass(scores: dict[str, float]) -> dict[str, Any]:
    checks = {
        "faithfulness": scores.get("faithfulness", 0) >= _DEEPEVAL_FAITHFULNESS_THRESHOLD,
        "answer_relevancy": scores.get("answer_relevancy", 0) >= _DEEPEVAL_ANSWER_RELEVANCY_THRESHOLD,
        "contextual_recall": scores.get("contextual_recall", 0) >= _DEEPEVAL_CONTEXTUAL_RECALL_THRESHOLD,
    }
    return {"deepeval_pass": all(checks.values()), "deepeval_checks": checks}


def evaluate_citation_pass(answer: str, papers: list[dict]) -> dict[str, Any]:
    """Delegates to `citation_check.verify_citations` rather than
    re-matching citations against a flattened text blob (the original
    donor's own inline approach). Copying two different citation-matching
    implementations into one small ported codebase would recreate exactly
    the duplication this lab is trying to close — this file and
    `citation_check.py` were ported together specifically so that doesn't
    happen here.
    """
    verified = verify_citations(answer, papers)
    return {
        "citation_pass": verified["citation_pass"],
        "pmcids_in_answer": verified["cited_pmcids"],
        "dois_in_answer": verified["cited_dois"],
        "verified_pmcids": verified["verified_pmcids"],
        "verified_dois": verified["verified_dois"],
    }


def evaluate_question_pass(
    result: dict[str, Any],
    case: dict[str, Any],
    *,
    deepeval_scores: dict[str, float] | None = None,
    answer: str | None = None,
) -> dict[str, Any]:
    retrieval = evaluate_retrieval_pass(result, case)
    out: dict[str, Any] = {
        "query_id": case.get("id"),
        "retrieval": retrieval,
    }
    if deepeval_scores:
        out["deepeval"] = evaluate_deepeval_pass(deepeval_scores)
    if answer is not None:
        out["citation"] = evaluate_citation_pass(answer, result.get("papers") or [])

    # CAUTION, carried across honestly rather than silently fixed: the donor's
    # own overall_pass never folds in citation_pass, even when `answer` is
    # supplied and the citation layer is computed and reported above. Verified
    # directly against a fabricated-DOI answer -- citation_pass came back
    # False while overall_pass still came back True. This is not this port's
    # bug to fix without a decision from whoever owns the rubric's definition
    # of "pass"; it is reported here so nobody assumes overall_pass already
    # accounts for citation hallucination.
    layers = [retrieval["retrieval_pass"]]
    if deepeval_scores:
        layers.append(out["deepeval"]["deepeval_pass"])
    out["overall_pass"] = all(layers)
    return out


__all__ = [
    "compute_paper_overlap",
    "evaluate_retrieval_pass",
    "evaluate_deepeval_pass",
    "evaluate_citation_pass",
    "evaluate_question_pass",
]
