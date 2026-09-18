# Copyright 2026 Anacodic AI Labs — https://anacodicai.org
# SPDX-License-Identifier: Apache-2.0

"""Compute inter-rater agreement statistics from paired rating exports.

Ported from `specialist-rag`'s `tests/clinician_validation/analyze_ratings.py`,
branch `origin/fix-completion` at commit `130ff868` (not on `main`).

The cookbook had no human-rating analysis path at all before this file. The
question it answers generalizes past clinical review: "do two people who
looked at the same thing agree?" is the question behind every hand-checked
ground-truth set, not just a clinician rating a clinical answer. If a second
person ever re-counts the outcome tables that would seed `gold/`, this is
what says whether that recount is reliable.

Usage:
    python analyze_ratings.py ratings.json
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

try:
    import numpy as np
except ImportError as e:
    raise SystemExit("numpy required: pip install numpy") from e


def compute_icc(*raters: Sequence[float]) -> float | None:
    """ICC(2,1): two-way random effects, single rater, absolute agreement.

    Shrout & Fleiss (1979) case 2; McGraw & Wong (1996) ICC(A,1).

        ICC(2,1) = (MS_R - MS_E) / (MS_R + (k-1) MS_E + k (MS_C - MS_E) / n)

    Subjects and raters are both random effects. The k(MS_C - MS_E)/n term
    charges systematic rater bias against the score, which is the property
    that matters for rating agreement: two raters who rank cases identically
    but differ by a constant offset are not interchangeable, and a
    consistency-only coefficient would call them perfect.

    Returns None when ICC is undefined -- fewer than two subjects or two
    raters, or no variance anywhere. A negative result is returned as-is
    rather than floored at zero: it means within-subject disagreement
    exceeds between-subject variance, which is a finding, not noise.
    """
    if len(raters) < 2:
        return None
    lengths = {len(r) for r in raters}
    if len(lengths) != 1:
        raise ValueError(
            f"every rater must score the same subjects; got lengths {sorted(lengths)}"
        )

    matrix = np.asarray(raters, dtype=float).T  # n subjects x k raters
    n, k = matrix.shape
    if n < 2:
        return None

    grand = matrix.mean()
    ss_total = ((matrix - grand) ** 2).sum()
    ss_rows = k * ((matrix.mean(axis=1) - grand) ** 2).sum()
    ss_cols = n * ((matrix.mean(axis=0) - grand) ** 2).sum()
    # A sum of squares cannot be negative; clamp away float residue at perfect fit.
    ss_error = max(0.0, ss_total - ss_rows - ss_cols)

    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1)
    ms_error = ss_error / ((n - 1) * (k - 1))

    denominator = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    if abs(denominator) < 1e-12:
        return None
    return float((ms_rows - ms_error) / denominator)


def analyze_ratings(ratings_file: str, metrics: list[str] | None = None) -> dict:
    """Compute inter-rater statistics from paired ratings.

    Input: JSON with `rater_1` and `rater_2` lists of equal length, each
    entry a dict carrying at least the fields named in `metrics`.
    """
    data = json.loads(Path(ratings_file).read_text(encoding="utf-8"))
    rater_1 = data["rater_1"]
    rater_2 = data["rater_2"]
    metrics = metrics or ["accuracy", "grounding", "utility"]

    results: dict = {}
    for metric in metrics:
        r1_scores = [r[metric] for r in rater_1]
        r2_scores = [r[metric] for r in rater_2]
        combined = r1_scores + r2_scores
        icc = compute_icc(r1_scores, r2_scores)

        results[metric] = {
            "mean": round(float(np.mean(combined)), 2),
            "sd": round(float(np.std(combined)), 2),
            "median": round(float(np.median(combined)), 2),
            "rater1_mean": round(float(np.mean(r1_scores)), 2),
            "rater2_mean": round(float(np.mean(r2_scores)), 2),
            "icc": None if icc is None else round(icc, 3),
            "n_score_4_or_5": sum(1 for s in combined if s >= 4),
            "pct_score_4_or_5": round(sum(1 for s in combined if s >= 4) / len(combined), 2),
        }

    if all("safety" in r for r in rater_1 + rater_2):
        unsafe_r1 = sum(1 for r in rater_1 if r.get("safety") == "Unsafe")
        unsafe_r2 = sum(1 for r in rater_2 if r.get("safety") == "Unsafe")
        n_cases = len(rater_1)
        results["safety"] = {
            "unsafe_r1": unsafe_r1,
            "unsafe_r2": unsafe_r2,
            "safe_rate": round(1 - max(unsafe_r1, unsafe_r2) / max(n_cases, 1), 2),
            "unsafe_queries": sorted({
                r.get("query_id", "")
                for r in rater_1 + rater_2
                if r.get("safety") == "Unsafe" and r.get("query_id")
            }),
        }

    return results


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python analyze_ratings.py <ratings.json>")
        raise SystemExit(1)
    results = analyze_ratings(sys.argv[1])
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
