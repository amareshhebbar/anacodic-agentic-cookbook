# 03 · Embed

Chunks (from `02-chunk`) go in as plain text strings. Vectors come out — one
per chunk, at whatever fixed dimension the model that produced them uses. The
dimension is the one number that must never silently change between the run
that builds an index and the run that queries it.

## Which model, which dimension

Multiple embedding dimensions are supported here, and mixing them does not
raise an error — it returns an empty result, which looks exactly like "no
relevant documents," and `03-dimensions.ipynb` demonstrates this happening.

| Model | Dimension | Needs |
|---|---|---|
| **hash-v1** (deterministic hash fallback) | configurable, default **384** | nothing — no model, no key, no network |
| `text-embedding-3-large` (OpenAI) | **3072** | `OPENAI_API_KEY` |
| `BAAI/bge-small-en-v1.5` / `bge-large-en-v1.5` (local, via `EMBEDDING_PROVIDER=local`) | 384 / **1024** | `sentence-transformers` + a local model download. `04-provider-dispatch.ipynb` wires the dispatch and raises a clear `EmbeddingError` if the package isn't installed, rather than an import traceback three calls deep. |
| `nomic-embed-text` (via Ollama) | **768** | a running Ollama daemon (not wired up as a runnable path in this stage — recorded here so the table is complete) |

## Run it

```bash
pip install -r requirements.txt
jupyter notebook 01-offline-embeddings.ipynb
```

`01-offline-embeddings.ipynb` needs **zero setup** — no key, no network, no
model download. It runs a deterministic hash embedding, and its first cell
states plainly that the resulting vectors are not semantically meaningful.
`02-openai-embeddings.ipynb` runs the real model once `OPENAI_API_KEY` is
set, and reports "not set, skipping" rather than crashing if it isn't.
`03-dimensions.ipynb` also needs no key — it demonstrates the dimension trap
using the hash path reconfigured to two different dimensions, and now
demonstrates the guard actually catching it before a search runs (Step 13),
not just proving the guard works in isolation. `04-provider-dispatch.ipynb`
and `05-local-vector-store.ipynb` need no key either — both run on the hash
path by default.

## Notebooks

| Notebook | What it proves |
|---|---|
| `01-offline-embeddings.ipynb` | the wiring works with no account anywhere — run this first |
| `02-openai-embeddings.ipynb` | the real 3072-dim path a production corpus would be built with |
| `03-dimensions.ipynb` | why a dimension mismatch is silent, not loud — what it looks like when it happens, and the guard wired into the search path itself (Step 13) |
| `04-provider-dispatch.ipynb` | one `embed_texts()` dispatching to hash, OpenAI, or a local model by a single setting, with strict-vs-degrade as an explicit choice |
| `05-local-vector-store.ipynb` | a real, local Chroma store this stage can write to and search — the read/write loop notebooks 01-04 don't close on their own |

## Index manifest — recording what an index was built with

Every index this stage creates should be written next to a small manifest —
one JSON file recording the model, dimension, tokenizer, max tokens, chunk
overlap, and the date it was built. Without one, a set of saved run
artifacts can accumulate with nothing recording what's actually in any of
them or at what dimension. Writing this manifest is the one JSON file that
turns "why is retrieval returning nothing" back into a one-line dimension
check instead of a debugging session.

`write_index_manifest()` (implemented in both `02-openai-embeddings.ipynb`
and `03-dimensions.ipynb`) writes exactly this:

```python
def write_index_manifest(path, *, index_name, model, dimension, tokenizer,
                          max_tokens, overlap):
    manifest = {
        "index_name": index_name,
        "model": model,
        "dimension": dimension,
        "tokenizer": tokenizer,
        "max_tokens": max_tokens,
        "overlap": overlap,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))
    return manifest
```

Read it back and compare `dimension` to the model you're about to embed a
query with, *before* the query ever touches the index. `03-dimensions.ipynb`
shows exactly what happens when that check is skipped: not an exception, an
empty result list that looks indistinguishable from "the corpus doesn't have
the answer."

## Files

```
03-embed/
├── README.md
├── 01-offline-embeddings.ipynb   hash fallback -- zero setup, run this first
├── 02-openai-embeddings.ipynb    text-embedding-3-large, 3072 dim, needs a key
├── 03-dimensions.ipynb           the dimension mismatch, demonstrated AND guarded against
├── 04-provider-dispatch.ipynb    one embed_texts(), three providers, strict-vs-degrade
├── 05-local-vector-store.ipynb   a local Chroma store this stage can write to and search
└── requirements.txt
```

## Design notes

The base module handles multi-provider dispatch (`04-provider-dispatch.ipynb`,
ported from `terrier-ta/services/embedding.py`), the
`EMBEDDING_MODEL_DIMENSIONS` table, and `_hash_embed()`, the deterministic
offline fallback this stage's whole "no key" promise rests on. The OpenAI
`text-embedding-3-large` configuration and `get_embedding_dimension()` logic
cover the model a production corpus would actually be built with.
`05-local-vector-store.ipynb` (ported from `clinical-search`'s
`local_stack/chroma_store.py`, branch `pr-1`) is the store notebooks 01-04
never had — write and search a real Chroma index, offline.

Not wired up as a runnable notebook in this stage (recorded in the dimension
table above only): Pinecone index creation, a BM25 sparse encoder for hybrid
retrieval, standalone embedding/reindex CLIs, and Ollama's `nomic-embed-text`
— these depend on a live Pinecone index, a material directory, or a running
Ollama daemon, none of which travels into this public repo. `04-retrieve` is
where hybrid retrieval and live index querying are demonstrated.
