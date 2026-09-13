#!/usr/bin/env python
"""One-command harness for the clinical-retrieval benchmark.

    python eval.py                  # run all 20 questions, print a table
    python eval.py --query-id B01   # run one question
    python eval.py --json out.json  # also write the raw per-question records

Collapsed into one script with no product-specific imports, so it runs in
this public repo with nothing installed beyond requirements.txt.

## What "runs" here, and what doesn't

This repo does not ship a retrieval or generation backend — plugging one in
here would defeat the point of a cookbook meant to run standalone. Instead,
this script defines the INTERFACE a backend must satisfy and calls a
default, honest stub if nothing is configured:

    retrieval_fn(query: str) -> (papers: list[dict], error: str | None)
    generation_fn(query: str, papers: list[dict]) -> str

Point the harness at a real implementation with:

    EVAL_RETRIEVAL_BACKEND=mypackage.mymodule:my_retrieval_fn
    EVAL_GENERATION_BACKEND=mypackage.mymodule:my_generation_fn

Without either set, retrieval returns zero papers and generation returns an
explicit "no backend configured" string rather than a confident answer. That
default is deliberate: it is easy for a RAG pipeline to retrieve nothing and
still answer confidently with specific clinical numbers anyway (see
LEADERBOARD.md). This script's default path would rather say nothing than
repeat that.

## Degrading gracefully

- No backend configured -> every question retrieves 0 papers. The table
  still prints; that IS the current honest baseline, not a crash.
- No OPENAI_API_KEY / no `deepeval` installed -> the four DeepEval columns
  (Faithfulness, Answer Relevancy, Contextual Precision, Contextual Recall)
  print "skipped (no judge)" instead of raising.
- No gold/ content for a question -> the gold-context columns print
  "no gold" instead of raising. See gold/README.md.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from questions import BENCHMARK_QUERIES  # noqa: E402
from citation_check import verify_citations  # noqa: E402
from citation_check import extract_citations  # noqa: E402
import pass_rubric  # noqa: E402
import judge_model  # noqa: E402

GOLD_DIR = HERE / "gold"

_LEVEL_MAP = {
    "Level I": 5,
    "Level II": 4,
    "Level III": 3,
    "Level IV": 2,
    "Level V": 1,
    "Unknown": 0,
}


# --------------------------------------------------------------------------- backend loading

def _load_callable(spec: str) -> Callable:
    """Resolve 'package.module:function_name' to the function object."""
    module_name, _, func_name = spec.partition(":")
    if not func_name:
        raise ValueError(f"backend spec must be 'module:function', got {spec!r}")
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def default_retrieval(query: str) -> tuple[list[dict], Optional[str]]:
    """No backend configured: zero papers, no error. See module docstring."""
    return [], None


def default_generation(query: str, papers: list[dict]) -> str:
    """No backend configured: say so, rather than answering confidently
    from parametric memory with nothing retrieved."""
    return "[no generation backend configured — see eval.py docstring]"


def resolve_backends() -> tuple[Callable, Callable]:
    retrieval_fn = default_retrieval
    generation_fn = default_generation
    if spec := os.getenv("EVAL_RETRIEVAL_BACKEND"):
        retrieval_fn = _load_callable(spec)
    if spec := os.getenv("EVAL_GENERATION_BACKEND"):
        generation_fn = _load_callable(spec)
    return retrieval_fn, generation_fn


# --------------------------------------------------------------------------- gold context

def load_gold(question_id: str) -> Optional[list[dict]]:
    path = GOLD_DIR / question_id / "passages.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("passages") or None


# --------------------------------------------------------------------------- deepeval (optional)

def deepeval_status() -> tuple[bool, str]:
    """(available, reason). Never raises."""
    if not judge_model.deepeval_installed():
        return False, "deepeval not installed (pip install -r requirements.txt)"
    if not judge_model.has_judge_model():
        return False, "no judge model API key set (OPENAI_API_KEY, GROQ_API_KEY, GOOGLE_API_KEY/GEMINI_API_KEY, or XAI_API_KEY)"
    return True, "available"


def run_deepeval_metrics(
    query: str, answer: str, contexts: list[str], ground_truth_facts: list[str]
) -> dict:
    """Faithfulness, Answer Relevancy, Contextual Precision, Contextual Recall.

    Returns a dict of metric name -> score, or {"skipped": reason} if the
    judge model isn't configured. The judge model comes from
    `judge_model.get_judge_model()`, which picks whichever provider you
    have a key for (OpenAI, Gemini, xAI, or Groq) rather than assuming
    OpenAI the way this function used to.
    """
    available, reason = deepeval_status()
    if not available:
        return {"skipped": reason}

    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        FaithfulnessMetric,
    )
    from deepeval.test_case import LLMTestCase

    resolved_judge = judge_model.get_judge_model()
    judge_label = resolved_judge if isinstance(resolved_judge, str) else resolved_judge.get_model_name()

    pipeline_model = os.getenv("EVAL_PIPELINE_MODEL", "")
    conflict = judge_model.judge_shares_model_with_pipeline(pipeline_model, judge_label)
    if conflict:
        print(f"WARNING: {conflict}")

    expected_output = "\n".join(ground_truth_facts)
    test_case = LLMTestCase(
        input=query,
        actual_output=answer,
        retrieval_context=contexts or ["No retrieval context available."],
        expected_output=expected_output,
    )

    scores: dict[str, Any] = {"judge_model": judge_label}
    metrics = {
        "faithfulness": FaithfulnessMetric(threshold=0.70, model=resolved_judge),
        "answer_relevancy": AnswerRelevancyMetric(threshold=0.70, model=resolved_judge),
        "contextual_precision": ContextualPrecisionMetric(threshold=0.60, model=resolved_judge),
        "contextual_recall": ContextualRecallMetric(threshold=0.60, model=resolved_judge),
    }
    for name, metric in metrics.items():
        try:
            metric.measure(test_case)
            scores[name] = round(float(metric.score), 3)
        except Exception as exc:  # noqa: BLE001 — a judge failure scores nothing, not a crash
            scores[name] = f"error: {exc}"
    return scores


# --------------------------------------------------------------------------- per-question run

def run_one_question(
    case: dict, retrieval_fn: Callable, generation_fn: Callable, run_deepeval: bool
) -> dict:
    t0 = time.monotonic()
    papers, error = retrieval_fn(case["query"])
    papers = papers or []
    latency_ms = int((time.monotonic() - t0) * 1000)

    all_text = " ".join(
        (p.get("summary") or p.get("text") or p.get("title") or "").lower() for p in papers
    )
    required = case.get("required_keywords", [])
    keywords_found = [kw for kw in required if kw.lower() in all_text]
    keyword_precision = len(keywords_found) / len(required) if required else 0.0

    evidence_levels = [p.get("evidence_level", "Unknown") for p in papers]
    min_required = _LEVEL_MAP.get(case.get("min_evidence_level", "Level III"), 3)
    papers_meeting_level = sum(1 for ev in evidence_levels if _LEVEL_MAP.get(ev, 0) >= min_required)

    answer = generation_fn(case["query"], papers)

    # verify_citations() replaces a plain extract-and-count: it checks every
    # PMCID/DOI the answer cites against the identifiers actually present in
    # `papers`, so a plausible-looking but invented citation is caught rather
    # than counted as evidence. See citation_check.py's module docstring for
    # why this is a different check from 05-gate's grounding check.
    citation_result = verify_citations(answer, papers)
    has_citation = citation_result["has_citation"]

    # The exact failure mode named in LEADERBOARD.md: an answer with content
    # but zero retrieved papers and zero citations.
    answered_without_evidence = (
        len(papers) == 0
        and not has_citation
        and answer.strip() not in ("", "[no generation backend configured — see eval.py docstring]")
    )

    contexts = [
        (p.get("summary") or p.get("text") or p.get("title") or "")[:4000] for p in papers
    ]
    gold_passages = load_gold(case["id"])

    result: dict[str, Any] = {
        "id": case["id"],
        "query": case["query"],
        "error": error,
        "papers": papers,
        "paper_count": len(papers),
        "keyword_precision": round(keyword_precision, 3),
        "keywords_found": keywords_found,
        "papers_meeting_min_evidence": papers_meeting_level,
        "latency_ms": latency_ms,
        "answer": answer,
        "has_citation": has_citation,
        "citation_verification": citation_result,
        "answered_without_evidence": answered_without_evidence,
        "gold_available": gold_passages is not None,
    }

    if run_deepeval:
        result["deepeval"] = run_deepeval_metrics(
            case["query"], answer, contexts, case.get("ground_truth_facts", [])
        )
    else:
        result["deepeval"] = {"skipped": "not requested (pass --deepeval)"}

    # The rubric that defines what "pass" means for this question. Retrieval
    # and citation are always evaluated; the DeepEval layer only enters the
    # verdict when real scores were computed above (a skip must not count as
    # neither a pass nor a fail).
    deepeval_scores = result["deepeval"] if "skipped" not in result["deepeval"] else None
    result["rubric"] = pass_rubric.evaluate_question_pass(
        result, case, deepeval_scores=deepeval_scores, answer=answer
    )

    return result


# --------------------------------------------------------------------------- reporting

def print_table(results: list[dict]) -> None:
    print(f"\n{'ID':<5}{'papers':>7}{'kw-prec':>9}{'evidence':>9}{'citation':>10}{'flag':>28}")
    print("-" * 68)
    for r in results:
        flag = "ANSWERED WITHOUT EVIDENCE" if r["answered_without_evidence"] else ""
        print(
            f"{r['id']:<5}{r['paper_count']:>7}{r['keyword_precision']:>9.0%}"
            f"{r['papers_meeting_min_evidence']:>9}{('yes' if r['has_citation'] else 'no'):>10}"
            f"{flag:>28}"
        )

    n = len(results)
    zero_paper = sum(1 for r in results if r["paper_count"] == 0)
    no_citation = sum(1 for r in results if not r["has_citation"])
    hallucinated = sum(1 for r in results if not r["citation_verification"]["all_verified"] and r["has_citation"])
    flagged = sum(1 for r in results if r["answered_without_evidence"])
    gold_covered = sum(1 for r in results if r["gold_available"])
    retrieval_pass = sum(1 for r in results if r["rubric"]["retrieval"]["retrieval_pass"])
    overall_pass = sum(1 for r in results if r["rubric"]["overall_pass"])

    print("-" * 68)
    print(f"{zero_paper}/{n} questions retrieved zero papers")
    print(f"{no_citation}/{n} answers contained no PMCID/DOI citation")
    print(f"{hallucinated}/{n} answers cited an identifier not in the retrieved papers (see citation_check.py)")
    print(f"{flagged}/{n} answers matched the 'answered without evidence' failure pattern")
    print(f"{gold_covered}/{n} questions have gold context (see gold/README.md)")
    print(f"{retrieval_pass}/{n} questions pass the retrieval rubric (see pass_rubric.py)")
    print(f"{overall_pass}/{n} questions pass overall (retrieval + DeepEval where computed)")

    if results and "deepeval" in results[0]:
        available, reason = deepeval_status()
        if not available:
            print(f"\nDeepEval metrics: skipped for all questions — {reason}")
        else:
            print("\nDeepEval metrics (faithfulness / relevancy / ctx-precision / ctx-recall):")
            for r in results:
                d = r["deepeval"]
                if "skipped" in d:
                    continue
                print(
                    f"  {r['id']:<5}"
                    f"{d.get('faithfulness', '—'):>6}  "
                    f"{d.get('answer_relevancy', '—'):>6}  "
                    f"{d.get('contextual_precision', '—'):>6}  "
                    f"{d.get('contextual_recall', '—'):>6}"
                )

    if zero_paper == n:
        print(
            "\nEvery question retrieved zero papers. If no EVAL_RETRIEVAL_BACKEND is "
            "set, this is expected — see LEADERBOARD.md, task 1: name the cause of "
            "paper_count 0."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--query-id", default=None, help="run a single question, e.g. B01")
    parser.add_argument("--json", default=None, help="path to also write raw per-question records")
    parser.add_argument(
        "--deepeval", action="store_true",
        help="also compute DeepEval metrics (needs `pip install deepeval` and a judge API key)",
    )
    args = parser.parse_args()

    retrieval_fn, generation_fn = resolve_backends()
    if retrieval_fn is default_retrieval:
        print(
            "No EVAL_RETRIEVAL_BACKEND configured — every question will retrieve 0 papers.\n"
            "This is the honest default, not a bug in this script. See eval.py's docstring "
            "and LEADERBOARD.md.\n"
        )

    cases = BENCHMARK_QUERIES
    if args.query_id:
        cases = [c for c in BENCHMARK_QUERIES if c["id"] == args.query_id]
        if not cases:
            parser.error(f"no such question id: {args.query_id}")

    results = [
        run_one_question(case, retrieval_fn, generation_fn, run_deepeval=args.deepeval)
        for case in cases
    ]

    print_table(results)

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
