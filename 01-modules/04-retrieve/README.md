# 04 · Retrieve

**In → out, in 5 lines:** a query (plus, for the simple path, a course/tenant
id) goes in. Ranked, deduplicated, scored candidate chunks or papers come out.
The simple path returns cosine-scored chunks from one course's own store. The
full path fans a query out across six sources in parallel, merges and
dedupes what comes back, has an LLM score every surviving candidate, and
blends five normalized signals into one `final_score` — with every signal
persisted so a ranking can be re-derived later without calling anything again.

Two implementations are included side by side because the pairing is the
point: read the simple one first, then see exactly what each extra mechanism
in the full one buys.

## Notebooks

| Notebook | Needs a key? |
|---|---|
| [`01-single-index-retrieval.ipynb`](01-single-index-retrieval.ipynb) | No. Runs entirely offline on a local, in-memory per-course store. |
| [`02-multi-source-fanout.ipynb`](02-multi-source-fanout.ipynb) | No key required for 4/6 sources (PubMed, OpenAlex, ClinicalTrials.gov, and the local vector stand-in are free/keyless). Semantic Scholar works without a key but is rate-limited — see defect 2 below. `TAVILY_API_KEY` unlocks the web-search leg. |
| [`03-dedupe-and-merge.ipynb`](03-dedupe-and-merge.ipynb) | No. Fully deterministic, offline, synthetic input. |
| [`04-llm-chunk-scoring.ipynb`](04-llm-chunk-scoring.ipynb) | The parsing/repair logic and threshold-filtering demo run offline with no key. The live-scoring cell needs `GROQ_API_KEY` or `OPENAI_API_KEY`; without one it reports that via `nbio.show_environment()` and skips, rather than failing. |
| [`05-ranking-and-final-score.ipynb`](05-ranking-and-final-score.ipynb) | No. Fully offline, synthetic candidates, zero API calls — including the re-ranking demo. |
| [`06-retraction-check.ipynb`](06-retraction-check.ipynb) | No. Runs against a small, hand-written retraction list, never the real ~60 MB Crossref download. |
| [`07-rate-limiting.ipynb`](07-rate-limiting.ipynb) | No. A sliding-window rate limiter and 429-backoff logic, demonstrated against synthetic calls and errors — no real provider call is made. |
| [`08-backend-cascade.ipynb`](08-backend-cascade.ipynb) | No. Pinecone/pgvector are stubs that stop cleanly when unconfigured; only the local, in-memory backend runs. |
| [`09-multi-query.ipynb`](09-multi-query.ipynb) | No. Fully offline, synthetic course store. |

Notebooks `06`–`09` port four capabilities our own products run in
production that didn't come across in the original port: a retraction
check ahead of ranking, a rate limiter for `04`'s highest-volume model
call, the multi-backend fallback pattern behind `01`'s simple path, and
multi-query retrieval — the cheapest partial answer to "is this a bad
query or an empty corpus?" `07`'s rate limiter and `nbio.cost_meter()`
(used in `04`) cap different things: one caps *rate*, the other caps
*spend*. A run can be cheap and still blow through a rate limit, or stay
well under a rate limit and still be expensive.

## How to run

```bash
pip install -r ../../requirements.txt -r requirements.txt
jupyter notebook .
```

Run `01`, `03`, and `05` first — none of them need any credential at all. Run
`02` to see the fan-out (most of it works with no key); run `04` last if you
want to see live LLM scoring rather than just the offline parser demo.

## Two known defects, carried over honestly

A cookbook that hides its defects teaches the defects; naming them turns each
into a bounded first contribution.

1. **`journal_quality.csv` is absent.** The configured path points into a
   vendored `paper-qa` checkout that isn't there. Symptom: every paper
   scores `-1` on this signal, `journal_impact` normalizes to `0.00` for
   every paper, and roughly 10–12% of `final_score`'s weight is silently
   switched off — the ranking runs, produces a number, and gives no
   indication that a whole signal contributed nothing. This repo ships a tiny
   *illustrative* example (`data/journal_quality_example.csv`, ten journals) so
   notebook `05` can show the signal actually contributing something — and
   also simulates the missing-file case explicitly, so you can see the exact
   degraded state side by side with the working one.
2. **Semantic Scholar without an API key returns HTTP 429 in practice.**
   Verified live against the real API while building this stage
   (2026-09-11): a keyless search request comes back `429 Too Many Requests`.
   Both citation enrichment and citation-graph traversal in the full pipeline
   run through this client, so a thin shortlist has no working recovery path
   when it happens. Notebook `02` lets this exception surface and print,
   rather than swallowing it into an empty result — set
   `SEMANTIC_SCHOLAR_API_KEY` (a free registration at
   semanticscholar.org/product/api) and rerun that cell to see a non-zero
   count instead.

## Weights are configuration, not code

`final_score` blends five normalized signals — relevance, citations, recency,
journal impact, evidence level — using configurable weights. No department
config, course config, or partner data travels here.
[`weights.json`](weights.json) ships one neutral, illustrative default
weight set, used whenever no domain-specific weights are configured. Change
them freely; `05` shows exactly what changing them does to a ranking,
offline.

## Not in scope

- **Fixing the zero-retrieval failure.** That's the headline open task on the
  benchmark in stage `06-bench` — real, unsolved, and left open on purpose.
- **Multi-hop sub-question routing.** Not stable enough to teach yet.
- **Agent orchestration** (supervisor, specialists, agents-as-tools). That's
  generation and domain judgment, not machinery, and it's out of scope for
  this cookbook.
- **Query rewriting.** `09-multi-query.ipynb`'s alternative phrasings are
  hand-written for the demo; generating them with a model is a separate
  capability, not built here.
- **Hybrid dense+sparse fusion, a cross-encoder reranker, and diagnosing the
  zero-retrieval-but-answers-anyway failure.** None of these exist anywhere
  in the lab to copy — they're new work, tracked as stories, not a port.
- **`sparse_retrieval.py`, `journal_quality.py` as a live signal.** Not
  ported: the former needs a fitted BM25 pickle this repo doesn't ship, the
  latter's CSV is absent in production too — copying either would move a
  defect, not fix one. `02`'s own `rank-bm25` demo and `05`'s illustrative
  journal-quality CSV are the honest stand-ins already in this stage.
