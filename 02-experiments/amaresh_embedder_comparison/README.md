# Embedder Comparison on COVID QA

Which embedding model finds the right chunk best on the ClinicalSearch style corpus, and does a medical embedder (MedCPT) beat the general baseline (BGE small)?

**Short answer:** no. MedCPT is 28% worse than BGE small on the realistic corpus, and BM25 is still the best single retriever. Details are at the bottom.

## Quick start

### 1. Setup (once)

```bash
cd 02-experiments/amaresh_embedder_comparison
python3 -m venv .venv
source .venv/bin/activate
pip install bm25s faiss-cpu sentence-transformers transformers huggingface_hub pandas matplotlib requests python-dotenv jupyter nbconvert ipykernel
cp .env.example .env
```

### 2. Run (local, free, no keys)

```bash
python run_benchmark.py
```

Pick from the menus:

| Menu | Example | Meaning |
|---|---|---|
| Embedders | `1,6` | BGE small vs MedCPT |
| Run mode | `1` | quick test (easy setting, 300 questions) |
| | `2` | standard (both settings, all questions, 3 runs) |
| | `3` | full (5 runs, use for final numbers) |
| Device | `1` | auto (GPU if available) |
| Vector store | `1` | local FAISS |

Start with mode `1` to check everything works, then run mode `2` or `3`.

### 3. Optional: API embedders

Add keys to `.env`, then pick their numbers in the menu. Embedders without a key are skipped automatically.

```bash
OPENAI_API_KEY=your_key
COHERE_API_KEY=your_key
VOYAGE_API_KEY=your_key
```

### 4. Optional: Pinecone instead of FAISS

```bash
USE_PINECONE=true
PINECONE_API_KEY=your_key
```

### 5. Optional: run without menus

```bash
export BENCH_EMBEDDERS="1,6" BENCH_MODE="2" BENCH_DEVICE="1" USE_PINECONE="false"
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 embedder_comparison.ipynb
```

Embeddings are cached in `cache/`, so each embedder is encoded only once.

## Check results

Start with `results/findings.txt`. Open `embedder_comparison.ipynb` for everything with explanations and plots.

| File in `results/` | Answers |
|---|---|
| `findings.txt` | plain text summary, start here |
| `leaderboard.csv` / `.png` | which retriever is best, with confidence intervals |
| `focus_vs_baseline.csv` | MedCPT vs BGE small, is the difference real |
| `all_vs_baseline.csv` | every embedder vs BGE small |
| `hybrid_gain.csv` | does hybrid beat BM25 with each embedder |
| `stability.csv` | same questions asked again, do results change |
| `scaling.csv`, `questions_needed.csv` | how many questions a fair comparison needs |
| `quality_vs_cost.csv` / `.png` | score vs time to embed |
| `unique_wins.csv` | questions only one embedder finds |
| `diagnosis.csv` | missed, found low, or found in top 3 |
| `per_query.csv.gz` | every question, every retriever, every metric |
| `run_meta.json` | config, hardware, versions, data hashes |

| Metric | Meaning |
|---|---|
| Hit@10 | right chunk is somewhere in the top 10 |
| nDCG@10 | right chunk is near the top (main score, 0 to 1) |
| MRR@10 | how high the first right chunk is |
| `tied_with_best = True` | difference from the leader is not statistically real |

---

## What I did

I tested which embedding model finds the right chunk best on `anacodicai-labs/covidqa-bench`: 64,965 chunks from 1,637 papers, and 1,840 questions with known answers.

Every embedder runs on the same questions, in two settings:

| Setting | What it is |
|---|---|
| `questions_only` | 137 papers that have questions (easy) |
| `full_with_decoys` | all 1,637 papers, including 1,500 similar decoy papers (hard, realistic) |

Each embedder is tested alone (`dense`) and combined with keyword search (`hybrid` = BM25 + embedder).

## Why

The first benchmark (`02-experiments/amaresh_new_eval_10th_oct`) showed:

* BM25 (keyword search) beat the dense embedder BGE small by about 0.12 to 0.15 nDCG@10
* the weak embedder was also pulling hybrid search down
* so the embedder is the weakest part of retrieval

This notebook asks: **does a medical embedder like MedCPT fix that, and which embedder is best overall?**

## What I got

Run: standard mode, 1,840 questions, 3 repeated runs, FAISS, GTX 1650.

**Hard setting (all 1,637 papers, with decoys)**

| Retriever | Hit@10 | nDCG@10 (95% CI) | vs BGE small |
|---|---|---|---|
| BM25 | 0.633 | 0.466 (0.447 to 0.485) | best overall |
| Hybrid BM25 + BGE small | 0.655 | 0.459 | tied with BM25 |
| Hybrid BM25 + MedCPT | 0.620 | 0.411 | lower by 0.048, significant |
| BGE small (baseline) | 0.515 | 0.348 | baseline |
| MedCPT | 0.418 | 0.249 | lower by 0.099 (28%), significant |

**Easy setting (137 question papers)**

| Retriever | Hit@10 | nDCG@10 |
|---|---|---|
| BM25 | 0.773 | 0.581 |
| Hybrid BM25 + BGE small | 0.749 | 0.544 |
| Hybrid BM25 + MedCPT | 0.745 | 0.526 |
| BGE small | 0.613 | 0.427 |
| MedCPT | 0.585 | 0.358 |

**In plain words**

* **MedCPT does not help on this benchmark.** It is significantly worse than BGE small in every setting: 16% lower on the easy corpus, 28% lower on the hard one. It wins 271 questions, BGE small wins 613.
* **Why, most likely:** MedCPT was trained on short PubMed search queries matched to titles and abstracts. COVID QA asks full natural language questions about passages deep inside full text papers, which is a different task.
* **MedCPT is not broken:** it finds 120 questions BGE small misses, and with BM25 its Hit@20 on the easy corpus (0.831) is the best of all.
* **BM25 is still the best single retriever.** Hybrid with BGE small ties it on the hard corpus; no hybrid beats it yet.
* **MedCPT is also 3 times slower:** 57 minutes to embed the corpus vs 19 minutes for BGE small, with twice the index size.
* **Results are stable:** across 3 repeated runs no question changed between found and missed, and the scores did not move.
* **Same conclusions on the filtered set:** removing the 106 questions that never name a paper ("What was the purpose of this study?") raises every score by about 0.02 to 0.03 but changes no ranking.
* **BM25 and BGE small match the first benchmark exactly**, so the setup is reproducible.

**Next:** test stronger general embedders (BGE large, E5 large, mxbai) and the MedEmbed family, which is fine tuned for medical question style retrieval.

## Embedders available

| # | Embedder | Type |
|---|---|---|
| 1 | BGE small (baseline) | general, local |
| 2 to 5 | BGE base, BGE large, E5 large, mxbai large | general, local |
| 6 | MedCPT (NCBI) | medical, local |
| 7 to 9 | MedEmbed small, base, large | medical, local |
| 10 | BioLORD 2023 | medical, local |
| 11 | PubMedBERT MS MARCO | medical, local |
| 12, 13 | OpenAI text embedding 3 small, large | API |
| 14 | Cohere embed v3 | API |
| 15 | Voyage 3 | API |
| 16 | any OpenAI compatible server (Ollama, vLLM) | custom |

The list lives in `embedders.json`. Every table in the notebook is shown twice: on **all** questions and on **filtered** questions.