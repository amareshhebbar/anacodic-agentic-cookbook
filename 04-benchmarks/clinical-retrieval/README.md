# Clinical retrieval — benchmark

**The baseline is flaky, and this benchmark ships that way on purpose.** On
the most recent set of saved runs of the retrieval pipeline this benchmark
measures — six runs against the identical question and configuration — five
retrieved real papers (three to five each) and one retrieved zero and
produced a confident, specific clinical recommendation anyway, with no
citation and no runtime error. Nobody has fixed the one-in-six case. Fixing
it is explicitly out of scope here: naming the cause is the first open task
below, and it is a real, unsolved, bounded problem rather than a toy
exercise. See `LEADERBOARD.md` for the full state and the three tasks that
add the next row.

## What this measures

Twenty clinical-topic questions (`questions.py`, ids `B01`-`M04`, spanning
burn/trauma, wound care, breast surgery, hand surgery, craniofacial,
oncology, nerve regeneration, tissue engineering, and multi-domain queries),
each with:

- `required_keywords` — terms a competent retrieval should surface
- `min_evidence_level` — an Oxford CEBM level the retrieved evidence should meet
- `ground_truth_facts` — short reference facts used by DeepEval's contextual
  recall/precision metrics

For a configured retrieval + generation backend, `eval.py` reports:

- **paper_count** — how many documents were retrieved per question (three to
  five on five of the last six saved runs against the same question; zero on
  the sixth, with no configuration change identified yet)
- **keyword_precision** — fraction of `required_keywords` found in retrieved text
- **evidence-level coverage** — how many retrieved papers meet `min_evidence_level`
- **citation verification** (`citation_verification`) — not just whether the
  answer contains a PMCID/DOI-shaped string, but whether every identifier it
  cites is actually present in the papers that were retrieved. See
  `citation_check.py` and `01-modules/01-tools/06-bench/05-citation-and-rubric.ipynb`.
- **rubric verdict** (`rubric`) — a pass/fail attributable to a stage
  (retrieval, citation, DeepEval), not one undifferentiated pass/fail. See
  `pass_rubric.py` and the same notebook.
- **answered-without-evidence** — the specific failure this benchmark exists to
  catch: an answer with content, zero retrieved papers, and no citation
- **DeepEval metrics** (optional, needs a judge model key): Faithfulness,
  Answer Relevancy, Contextual Precision, Contextual Recall — see
  `01-modules/01-tools/06-bench/02-deepeval-metrics.ipynb` for what each one actually
  catches. The judge model is resolved by `judge_model.py`, which also warns
  when the judge and the pipeline under test are the same model — see
  `01-modules/01-tools/06-bench/06-judge-integrity-and-agreement.ipynb`.

## How to run it

```bash
cd 04-benchmarks/clinical-retrieval
python eval.py                    # all 20 questions, offline stub backend
python eval.py --query-id B01     # one question
python eval.py --deepeval         # also compute DeepEval metrics (needs a judge key)
python eval.py --json out.json    # also write raw per-question records
```

With nothing configured, `eval.py` runs to completion and reports
**20/20 questions retrieved zero papers** — truthfully, not as a bug in the
script, and not a claim about a real backend's typical run: with no backend
wired up, there is nothing to retrieve from. See `LEADERBOARD.md` for what a
real, configured backend actually does. To point it at a real
retrieval/generation implementation:

```bash
export EVAL_RETRIEVAL_BACKEND=mypackage.mymodule:my_retrieval_fn
export EVAL_GENERATION_BACKEND=mypackage.mymodule:my_generation_fn
python eval.py
```

See `eval.py`'s module docstring for the exact function signatures.

## Gold context

`gold/` is intentionally empty except for a README explaining the format.
Gold context — a hand-checked set of correct passages per question — requires
clinical judgment that only a domain expert can supply; it is not copied,
generated, or invented here. See `gold/README.md` for the format and how to
contribute one. `eval.py` and
`01-modules/01-tools/06-bench/03-gold-context-arm.ipynb` report the gold-context arm as
"no gold" / skipped until entries exist.

## Two setup traps that each cost a day to find cold

Neither is a bug in this benchmark or in your install. Both are documented
here so a contributor doesn't lose a day rediscovering them:

1. **A domain-routing test defect, not an install problem.** Three of the
   unit tests fail whenever `DOMAIN` is set to a department other than
   `plastic_surgery` — they assert
   `burn_trauma` routing, which departments like `breast_reconstruction`
   don't have. If you're porting or extending the retrieval side and see
   exactly three failures tied to domain routing, this is why; it is a defect
   in the tests, not in your setup.
2. **`api.groq.com` rejects Python's default `urllib` User-Agent.** Groq's
   API sits behind Cloudflare, which returns an HTTP 403 (Cloudflare error
   1010) to requests carrying Python's default `urllib`/`requests`
   User-Agent string. The `openai` SDK (used for Groq-compatible chat
   completions) sets its own User-Agent and is unaffected. A hand-rolled
   `urllib.request` or bare `requests.get` probe against `api.groq.com` will
   hit this and look like an auth failure when it isn't one — use the
   `openai` SDK pointed at Groq's base URL instead of rolling your own HTTP
   call.

## Measurement machinery — ported, not yet exercised on a real run

`citation_check.py`, `pass_rubric.py`, `judge_model.py`, and
`clinician_validation/` (with `analyze_ratings.py` and
`ratings_template.json`) were ported from `specialist-rag`'s
`tests/benchmark/` and `tests/clinician_validation/`, branch
`origin/fix-completion` at commit `130ff868` — not on `main`. `eval.py`
already imports and calls the first three on every run; `analyze_ratings.py`
is a separate, offline tool for whenever a second person hand-rates the same
answers, run directly rather than through `eval.py`. See
`01-modules/01-tools/06-bench/05-citation-and-rubric.ipynb` and
`06-judge-integrity-and-agreement.ipynb` for what each one catches, with real
examples — including one known gap carried across honestly: the rubric's
`overall_pass` does not currently fold in `citation_pass`, verified directly
in notebook 05.

Left out of the port entirely: `breast_reconstruction_queries.py` and its
build scripts (one department's question set — this benchmark already has
`questions.py`), `clinical_queries.py` (superseded), `ontario_extractor.py`
(a different project), `runner.py` (`eval.py` is this benchmark's harness;
importing a second one would leave two things owning "run the benchmark"),
and the pytest wrappers around these modules — the notebooks above are this
benchmark's test surface instead.

## Not in scope for this benchmark

- **Fixing the one-in-six retrieval failure.** Left as open task 1 in
  `LEADERBOARD.md` on purpose.
- **Running real clinician validation.** `analyze_ratings.py` can analyze
  ratings once they exist; producing them needs answers worth rating, which
  needs a working retrieval path first. Sending a clinician answers from a
  zero-retrieval run spends a favor for nothing.
- **Latency attribution.** Real work, but out of scope for this benchmark.

## Disclaimer

Nothing here is a medical device or validated for clinical use. These
questions and this harness measure retrieval-system behavior against
published literature; they do not produce advice for patient care. See the
repo-root `README.md`.
