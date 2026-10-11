# Read this before opening the notebook

This folder does **not** run on its own. It must sit inside a clone of the
cookbook, because the notebooks import `nbio.py` from the repo root and reuse
components from `01-modules/` and `04-benchmarks/`.

## Steps

```bash
# 1. fork anacodicAI-labs/anacodic-agentic-cookbook on GitHub, then:
git clone https://github.com/<you>/anacodic-agentic-cookbook.git
cd anacodic-agentic-cookbook

# 2. branch, named to match this folder
git checkout -b rashan/table-agent

# 3. this folder already lives at 02-experiments/rashan-t/ — open from there
jupyter notebook 02-experiments/rashan-t/01-load-scitableqa.ipynb
```

## Getting the data (SciTableQA, Biology subset)

MIT license. The HuggingFace auto-viewer is broken (inconsistent CSV columns),
so download the raw files and parse them — do **not** rely on `load_dataset()`.

```bash
# Biology tables + their annotations only (not the full 893 MB)
# tables:      Amazon-Extracted-Tables/Biology/...
# QA / gold:   Annotated/...   (JSON)
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("Kehindeajayi01/SciTableQA", repo_type="dataset",
                  local_dir="02-experiments/rashan-t/data/scitableqa",
                  allow_patterns=["Amazon-Extracted-Tables/Biology/*", "Annotated/*"])
PY
```

Everything under `data/` is **gitignored — never commit it** (size + we keep the
public repo clean).

## Notes

1. **Write the embedding dimension next to every number.** A 768-dim (local
   `nomic-embed-text`) result and a 3072-dim (`text-embedding-3-large`) result
   are not comparable, and the mistake is invisible once both are in a table.
2. **Offline path first.** Name the no-API-key path explicitly so the notebook
   runs for a reader without secrets, then add the keyed path on top.

## Never commit

`data/`, any `.npy`, any `.env`. The `.gitignore` already covers these.
