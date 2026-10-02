> **Moved from clinical-search** (`benchmark-proof`, f28601c) on 2026-10-02. Paths now point at
> this folder's gitignored `corpus/`. Not moved: `harness.py` / `run_pilot.py` (they import
> clinical-search internals), raw `single_*.json` (contains corpus text) and `results.db`.
> Publish a run with `python provider/export_public_summary.py provider/results/single_<id>.json`.

# ClinicalSearch Benchmarks

Two independent benchmark suites under `amaresh_benchmark/`. Neither shares
code with `tests/benchmark/runner.py` or the production Pinecone pipeline —
both run fully offline/local except for the LLM synthesis call.

```
amaresh_benchmark/
  extraction/     # is the PDF->chunk extraction clean?
  provider/       # which LLM model gives the best/most stable answers?
```

## Prerequisites

```bash
cd anacodic-agentic-cookbook   # repo root
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install groq requests numpy matplotlib networkx python-dotenv
```

`provider/` additionally needs:
- A running local Ollama daemon with `nomic-embed-text` pulled (`ollama pull nomic-embed-text`) — used for both corpus embedding and query embedding, so retrieval never calls OpenAI or Pinecone.
- A `GROQ_API_KEY` in `.env` at the repo root — used only for the answer-synthesis LLM call.

---

## 1. extraction/

Checks whether the PDF-ingestion pipeline produced structurally sound,
non-corrupted chunks and embeddings, and cross-checks extracted paper
metadata against CrossRef.

```
extraction/
  metrics.py                  structural + embedding checks (offline)
  metadata_fidelity.py        CrossRef title/author cross-check (needs internet)
  run_extraction_benchmark.py CLI entrypoint
  ../corpus/                  chunk_meta.jsonl, embeddings.npy, manifest.json (gitignored)
  results/                    <timestamp>.json (kept forever) + LEADERBOARD.md (overwritten each run)
```

### Run

```bash
cd 02-experiments/amaresh-eval-harness/extraction
python run_extraction_benchmark.py \
  --chunk-meta ../corpus/chunk_meta.jsonl \
  --embeddings ../corpus/embeddings.npy \
  --mailto you@domain.com
```

Add `--skip-crossref` to run fully offline.

### What each metric means

| Metric | Meaning |
|---|---|
| Papers with page gaps | Missing pages in the extracted sequence — signals dropped content |
| Empty/near-empty chunks | Chunks under 20 chars — usually boilerplate leaking in as its own chunk |
| Suspicious glyph hits | Font-encoding corruption |
| Table cells_status distribution | Should be all `ok`; anything else needs a manual look |
| Row-count mismatches | `table_data.rows` count disagrees with reported row count |
| Duplicate chunk pairs | Same text under two different chunk_ids |
| Embedding health (NaN/zero-norm) | Should always be 0/0 |
| Semantic separation | Within-paper cosine similarity minus across-paper — should be positive |
| Metadata fidelity pass rate | % of papers matching the live CrossRef record for their DOI |

---

## 2. provider/

Runs clinical queries against the local corpus, entirely locally except
for the final LLM answer:

```
query → Ollama embed (nomic-embed-text, 768-dim)
      → cosine similarity search over the full local corpus (no vector DB)
      → top-k chunks → Groq LLM synthesis
      → deterministic keyword-precision scoring against ground truth
```

```
provider/
  local_retrieval.py       in-memory cosine search over chunk_meta.jsonl + embeddings
  ollama_embed.py           Ollama /api/embed wrapper (corpus + query embedding)
  reembed_corpus.py         one-time script: re-embeds the corpus locally via Ollama
  local_pipeline.py         retrieval + Groq synthesis + keyword scoring for one trial
  local_queries.py          the 5 benchmark queries (L01-L05) + required ground-truth keywords
  run_local_pilot.py         CLI: runs N trials x M providers x K queries, writes DB/graph/charts
  run_single_benchmark.py   CLI: runs ONE query N times against ONE model — deep consistency check
  storage.py                SQLite persistence
  graph_store.py            builds + writes the comparison graph
  charts.py                 all PNG chart generation
  harness.py                legacy: Pinecone-backed provider switching (tests/benchmark/runner.py wrapper) — superseded by local_pipeline.py, kept for reference only
  ../corpus/                chunk_meta.jsonl, embeddings.npy, embeddings_ollama.npy (gitignored)
  results/                  results.db, comparison.graphml, single_*.json, charts/*.png
```

### One-time setup: re-embed the corpus locally

```bash
cd 02-experiments/amaresh-eval-harness/provider
python reembed_corpus.py --chunk-meta ../corpus/chunk_meta.jsonl --out ../corpus/embeddings_ollama.npy
```

Writes `../corpus/embeddings_ollama.npy` (680 x 768). Required once, or whenever
`../corpus/chunk_meta.jsonl` changes — OpenAI-embedded `embeddings.npy` and
Ollama-embedded `embeddings_ollama.npy` are different vector spaces and
cannot be mixed.

### Check which Groq models your key can use

```bash
python run_local_pilot.py --list-models
```

### Run the full comparison (multiple queries x multiple models)

```bash
python run_local_pilot.py \
  --chunk-meta ../corpus/chunk_meta.jsonl \
  --embeddings ../corpus/embeddings_ollama.npy \
  --query-ids L01 L02 L03 L04 L05 \
  --providers groq_llama groq_qwen \
  --trials 3 \
  --groq-llama-model openai/gpt-oss-120b \
  --groq-qwen-model qwen/qwen3.8-27b
```

`--groq-llama-model` / `--groq-qwen-model` accept any model ID from
`--list-models` — the `groq_llama`/`groq_qwen` provider labels are just
labels for the DB/graph/charts, not tied to actual Llama/Qwen models.

### Run a deep single-query consistency check

Runs one query N times against one model, scores each trial's keyword
precision against ground truth, computes a groundedness score (answer vs
retrieved evidence, via Ollama embedding cosine similarity) per trial, and
an answer-to-answer self-consistency matrix across all N trials.

```bash
python run_single_benchmark.py \
  --query-id L01 \
  --groq-model openai/gpt-oss-120b \
  --trials 10
```

### Where metrics land

```
results/
  results.db                    SQLite, one row per trial from run_local_pilot.py, appended forever
  comparison.graphml             query/provider/trial nodes + pairwise comparison edges
  single_<query_id>.json         full per-trial detail from run_single_benchmark.py, including:
                                  corpus_size_checked, top_k_retrieved_per_trial, and for every
                                  trial the exact retrieved chunks (chunk_id, paper, section,
                                  similarity_score, text_preview) plus the generated answer
  charts/
    precision_by_provider.png    mean keyword precision per provider, error bars = stdev
    keyword_gap_by_query.png     per-query grouped bars vs a 1.0 "ideal" line
    paper_count_variance.png     box plot of paper_count per query across trials
    latency_by_provider.png      retrieval latency spread per provider
    single_<id>_deep.png         3-panel: keyword precision per trial, groundedness per trial,
                                  answer-to-answer similarity heatmap
```

### How to read each output

**SQLite:**

```sql
SELECT query_id, provider, AVG(keyword_precision), AVG(paper_count)
FROM trials
GROUP BY query_id, provider;
```

**GraphML** (open in Gephi/Cytoscape, or in Python):

```python
import networkx as nx
G = nx.read_graphml("results/comparison.graphml")
for u, v, d in G.edges(data=True):
    if d.get("relation") == "compared_on":
        print(u, "vs", v, "->", d["winner"], "diff:", d["diff"])
```

**Groundedness score** (`single_<id>.json`, `run_single_benchmark.py`) —
cosine similarity between the LLM's answer and its own retrieved evidence.
High = answer stays faithful to what was retrieved. Low = drifting/hallucinating
beyond the evidence, even if keyword precision looks fine.

**Confidence score** (`single_<id>.json`) — average pairwise cosine similarity
across all N answers to the same query. High = model gives the same answer
every time (expected at `temperature=0.0`). Low = unstable, inconsistent
answers to identical input — a reliability problem worth investigating.

---

## Notes

- No Pinecone, no vector database — `local_retrieval.py` does a full
  in-memory cosine scan of the local `.npy` embeddings file on every query.
- No OpenAI dependency — corpus and queries are both embedded via a local
  Ollama model (`nomic-embed-text`). The only external API call in the
  entire `provider/` suite is the Groq synthesis call.
- `../corpus/` (chunk_meta.jsonl, embeddings*.npy, manifest.json) is gitignored
  in both suites — only code and `results/` (metrics/graph/charts) belong
  in git.
- `harness.py` is legacy: it wraps the production Pinecone pipeline via
  `tests/benchmark/runner.py` and is kept for reference, but
  `local_pipeline.py` + `run_local_pilot.py` is the actively used path.