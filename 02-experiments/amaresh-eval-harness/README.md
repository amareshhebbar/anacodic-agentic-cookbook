# amaresh-eval-harness

Measurement for clinical retrieval: a harness that runs a question many times
and scores every run, plus a quality check of the corpus the retriever reads.

| | |
|---|---|
| Owner | Amaresh Hebbar |
| Part | measurement — scores what the retrieval tools produce |
| Benchmark | `04-benchmarks/clinical-retrieval/` |
| Code origin | moved from `clinical-search` branch `benchmark-proof` (f28601c) on 2026-10-02 |

## What is here

```
  01-run-one-question.ipynb   Exp 0 — one question, end to end, no key, no corpus
  goldens.json                5 queries matched to the corpus + their expected terms
  provider/                   Exp 1–2 — repeated-trial harness (local retrieval + Groq)
    results/                    charts, comparison graph, per-trial CSV, public summary
  extraction/                 Exp 3 — corpus quality checks + LEADERBOARD.md
  corpus/                     the corpus — LOCAL ONLY, gitignored, never committed
  HOW_TO_RUN.md               full run instructions for provider/ and extraction/
```

## Results

Every number below is read from a file in this folder.

### Exp 1 — model comparison (local pilot)

```
  design     5 queries (L01–L05) x 2 providers x 3 trials = 33 trial rows
  retrieval  local exact cosine search over 680 chunks, top 8 (no vector DB)
  embedding  768-dim, nomic-embed-text via Ollama
  scoring    keyword precision against each query's expected clinical terms
  result     28 runs succeeded, 5 failed on the provider side (see "What broke")
             groq_llama 0.938 mean · groq_qwen 0.945 mean — effectively tied
  file       provider/results/local_pilot_trials.csv, charts/*_by_provider.png
```

**Read this as a generation comparison, not a retrieval study.** Retrieval is
deterministic here: every query returned the same number of papers on every
successful trial (L01 6 · L02 4 · L03 3 · L04 5 · L05 4). The one `0` in the
CSV is a failed API call, not an empty search.

### Exp 2 — one question, ten trials

```
  query      L01   model openai/gpt-oss-120b   trials 10
  keyword precision   1.00 on every trial
  groundedness        0.876 ± 0.004   (embedding similarity, answer vs evidence)
  answer similarity   0.981            (embedding similarity between trials' answers)
  papers retrieved    6 on every trial
  latency             1.2 s – 12.6 s   (a 10x spread on identical requests)
  file       provider/results/summary_single_L01.json, charts/single_L01_*.png
```

### Exp 3 — extraction quality of the corpus

20 papers, 680 chunks — see `extraction/LEADERBOARD.md`. Headlines: no page
gaps; 202/202 table chunks carry markdown and cells; 16 empty chunks (2.4%);
6 table row-count mismatches; only 3/20 extracted titles match CrossRef.

## What this does NOT show yet

```
  the open question         six runs of one question on the REAL clinical-search
                            pipeline returned 4 / 0 / 4 / 5 / 3 / 3 papers.
                            Is retrieval reproducible?
  why Exp 1–2 can't answer  local exact search returns the same chunks every time,
                            so only the model's wording can vary
  next                      the real pipeline, one query, 16+ runs, printing WHICH
                            papers come back each run — min, max, how often zero
```

On run count: for a failure that occurs about 1 run in 6, the chance of missing
it in n runs is `(5/6)^n` — 57% at 3 runs, 5% at 16.

Known limits of the current metrics: keyword precision saturates at 1.0 on
this corpus, and "groundedness" is embedding similarity, not a check that each
claim is supported.

## What broke on the way (from the run logs and setup)

- No free OpenAI key; a $5 top-up was declined → switched to Groq free tier.
- The original 3072-dim index was too heavy for a laptop → re-embedded at 768
  with Ollama. **768 and 3072 results are not comparable** — different vector spaces.
- Groq errors recorded in the CSV: `429 no credits remaining`, `404` for
  `llama-3.3-70b-versatile` (model retired), `429 request too large` for qwen3.
- Label to check: in `run_local_pilot.py`, provider `groq_qwen` maps to
  `openai/gpt-oss-120b`.

## Safety rules for this folder

- `corpus/`, `*.npy`, `*.db`, `.env` and raw `provider/results/single_*.json`
  are gitignored. Raw runs contain licensed journal text.
- To publish a run: `python provider/export_public_summary.py provider/results/single_<id>.json`
  — writes `summary_<id>.json` with text fields removed.
- Not moved from clinical-search: `harness.py` and `run_pilot.py` (they import
  clinical-search internals and do not run here).

## Reused from the repo — not reimplemented

| what | where |
|---|---|
| keyword precision | `04-benchmarks/clinical-retrieval/eval.py` |
| the 20 benchmark questions | `04-benchmarks/clinical-retrieval/questions.py` |
| pass/fail thresholds | `04-benchmarks/clinical-retrieval/pass_rubric.py` |
| judge abstraction + judge-shares-model check | `04-benchmarks/clinical-retrieval/judge_model.py` |
