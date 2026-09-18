# 06 · Bench — evaluation

Questions + (optionally) gold answers -> a score table. This stage teaches the
evaluation harness behind `04-benchmarks/clinical-retrieval/`: how to run one
question end to end, what each DeepEval metric actually catches, how a
gold-context arm separates a retrieval failure from a generation failure, and
how to re-rank existing results for free with no API calls at all.

**The benchmark this stage teaches is flaky, on purpose left unfixed.** On a
run of six against the identical question and configuration, the pipeline it
measures retrieved real papers five times and none once. See
`04-benchmarks/clinical-retrieval/README.md` and `LEADERBOARD.md` for the
full state — these notebooks are written to be useful and honest about that,
not to pretend it's fixed.

## Notebooks

| # | Notebook | What it teaches |
|---|---|---|
| 01 | `01-run-one-question.ipynb` | End to end: one question from `questions.py` through the harness, every setup trap named along the way |
| 02 | `02-deepeval-metrics.ipynb` | What Faithfulness, Answer Relevancy, Contextual Precision, and Contextual Recall each catch — and don't |
| 03 | `03-gold-context-arm.ipynb` | Why scoring against gold context (not just retrieved context) tells you *which* stage failed — demonstrated on a synthetic example, since real gold context doesn't exist yet |
| 04 | `04-ablation-offline.ipynb` | Re-ranking from stored score components with a changed weight — zero API calls, zero retrieval, the cheapest useful experiment in the repo |
| 05 | `05-citation-and-rubric.ipynb` | `verify_citations` catching a fabricated DOI a plain extract-and-count would miss, and the pass rubric's four verdicts — including a real gap: `overall_pass` doesn't currently see `citation_pass` |
| 06 | `06-judge-integrity-and-agreement.ipynb` | `judge_shares_model_with_pipeline` — is the judge grading its own homework? — and `compute_icc`, showing why two raters with the same mean can still disagree completely |

Each notebook `import nbio; nbio.bootstrap()`s in its first cell and is
runnable with no API key — every one has an offline path that produces real
output, even if that output is "skipped: no key configured" for a specific
cell.

## Two setup traps, so you don't lose a day to either

Neither is a bug in these notebooks.

1. **A domain-routing test defect, not an install problem.** The test suite
   this stage builds on has three tests that fail whenever `DOMAIN` names a
   department other than `plastic_surgery`, because they assert
   `burn_trauma` routing that other departments (e.g.
   `breast_reconstruction`) don't have. If you're extending these notebooks
   against a real backend and see exactly three domain-routing failures,
   that's why — it's a defect in the tests, not in your setup.
2. **`api.groq.com` rejects a plain `urllib`/`requests` User-Agent with HTTP
   403 (Cloudflare error 1010).** Groq's API sits behind Cloudflare, which
   blocks Python's default User-Agent string. The `openai` SDK (used
   throughout this stage for Groq-compatible calls) sets its own
   User-Agent and is unaffected — a hand-rolled HTTP probe against Groq is
   not. If you're debugging what looks like an auth failure against Groq,
   check whether you're using the SDK or a raw HTTP call before you assume
   the key is wrong.

## Relationship to `04-benchmarks/clinical-retrieval/`

That folder is the frozen benchmark: the 20 questions, the harness
(`eval.py`), the gold-context format, and the leaderboard — plus, as of
notebooks 05/06, `citation_check.py`, `pass_rubric.py`, `judge_model.py`, and
`clinician_validation/`, which `eval.py` now imports and calls directly on
every run. These notebooks are the teaching layer on top of all of it — they
import the real modules from there and walk through the same logic `eval.py`
runs, one concept at a time, with explanation. Running `eval.py` directly is
the fast path; these notebooks are the slow, explained one.

## Setup

```bash
pip install -r requirements.txt          # from this directory
pip install -r ../../../requirements.txt    # repo root, if you haven't already
jupyter notebook 01-run-one-question.ipynb
```

No key is required for any notebook to run. `nbio.show_environment()` in the
first cell of each notebook prints which optional keys are loaded, so you
always know which code path you're on.
