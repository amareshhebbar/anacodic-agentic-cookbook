# Read this before opening the notebook

This folder does **not** run on its own. It has to sit inside a clone of the
cookbook, because the notebook imports `nbio.py` from the repo root and the
benchmark from `04-benchmarks/clinical-retrieval/`.

## Four steps

```bash
# 1. fork anacodicAI-labs/anacodic-agentic-cookbook on GitHub, then:
git clone https://github.com/<you>/anacodic-agentic-cookbook.git
cd anacodic-agentic-cookbook

# 2. branch, named to match this folder
git checkout -b amaresh/eval-harness

# 3. move this whole folder in
mv /path/to/amaresh-eval-harness 02-experiments/

# 4. open it from there
jupyter notebook 02-experiments/amaresh-eval-harness/01-run-one-question.ipynb
```

If you skip step 3 the first cell stops with an explanation rather than a
traceback — it will tell you this same thing.

## What is in here

| | |
|---|---|
| `01-run-one-question.ipynb` | Sprint 1, complete and already run. Start here. |
| `goldens.json` | 5 real queries matching the corpus, with terms verified present |
| `corpus/` | 680 real chunks. **Local only — gitignored, never commit it.** |
| `results/` | where your CSVs land |
| `README.md` | what this experiment is, and what came before |

## Two things that will bite you if nobody says them

**1. The corpus is breast reconstruction. The benchmark questions are burns.**
`04-benchmarks/clinical-retrieval/questions.py` asks about skin grafting,
Parkland formula, NPWT. The corpus in `corpus/` is about nipple-sparing
mastectomy. Running those questions against this corpus returns almost nothing
— that is a topic mismatch, not a broken harness. Use `goldens.json` with this
corpus.

**2. Dimensions.** The original index was 3072-dim (`text-embedding-3-large`),
which needs an OpenAI key to query. Only the TEXT is shipped here, so re-embed
locally — Ollama `nomic-embed-text` is 768-dim and free. Write the dimension
next to every number you report. A 768 result and a 3072 result are not
comparable and the mistake is invisible once both are in a table.

## Never commit

`corpus/`, any `.npy`, any `.env`. The `.gitignore` already covers these — do
not override it. The cookbook is a public repo and the corpus is licensed
journal text.
