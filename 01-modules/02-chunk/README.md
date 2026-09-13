# 02-chunk

Structured text and tables (stage 01's output) → chunk records ready to
embed. In: a document's text, optionally with real heading/table structure.
Out: a list of chunk records, each independently retrievable, each carrying
enough metadata to be cited back to its source. This stage does not decide an
embedding model or a store — see 03-embed and the store-backend flag in
`03-store-backends.ipynb`.

## Why one chunker isn't enough

Chunk boundaries decide what can ever be retrieved, so different document
shapes need different chunking strategies — a single approach gives one
answer to "what came back for this query" when several are actually needed.
This stage puts three approaches in one place so they're directly
comparable:

| Notebook | Approach |
|---|---|
| `01-character-splitting.ipynb` | `RecursiveCharacterTextSplitter`, medical section separators, ~400 words/chunk, `--adaptive` sentence-similarity variant |
| `02-token-aware-chunking.ipynb` | Docling `HybridChunker` — structure-aware, prose/table/figure tagged |
| `03-store-backends.ipynb` | Same chunker as `02`, store selected by a flag (Pinecone / S3 Vectors / local Chroma), resume + dry-run |

Also included, in `02` and `03`: heading-driven structure handling that shows
up as the `section_path` field and the `always_emit_headings=True` chunker
setting — Docling's own heading walk gives a clean split by heading, so
`section_path` carries that breadcrumb without needing any custom heading
logic.

**Design decisions, kept deliberately out of scope:**

1. No department- or corpus-specific configuration of any kind is included
   in this cookbook — that belongs to a deployer, not the pipeline.
2. Deciding the embedding model is stage 03's job, so every `embed_fn` here
   is either a clearly marked stub or a deterministic, **not semantically
   meaningful** hash-based stand-in written locally in each notebook (per
   `nbio.py`'s own rule that stage-specific logic doesn't belong in the
   shared module).

No `.env` file or API key value was read into any file or notebook output.
The only "data" in this stage is a synthetic five-to-eight-row outcomes
table, invented for this cookbook — no patient, student, or manuscript data
of any kind.

## The chunk metadata contract

Every chunk-producing function in this stage returns records of this shape
(this table is the first place the contract is written down explicitly):

| Field | Type | Meaning |
|---|---|---|
| `chunk_id` | `str` | Stable, globally unique id — `f"{doc_id}::chunk::{chunk_index}"` here. |
| `doc_id` | `str` | The source document's id (paper id, PMCID, course-material filename stem — whatever stage 01 assigned). |
| `chunk_index` | `int` | 0-based position of this chunk within its document, in the order it was produced. |
| `chunk_type` | `str` | One of `"prose"`, `"table"`, `"figure"`. Character-splitting output is always `"prose"` (it has no way to tag anything else). |
| `is_table` / `is_figure` | `bool` | The same fact as `chunk_type`, as two booleans instead of one string — ported from `docling/chunking.py`'s original field names. **Currently emitted only by `02-token-aware-chunking.ipynb`**; `01-character-splitting.ipynb` and `03-store-backends.ipynb` don't set them yet, so this is not yet a guarantee across all three chunkers. Closing that is the drift-check / shared `Chunk` type work already named as still missing, not done here. |
| `text` | `str` | Citation/display text. For a table, this is a clean markdown export (`TableItem.export_to_markdown`), never the flattened "row, col=val" serialization — that reads badly for a human and no better for an embedder. |
| `embed_text` | `str` | What would actually be sent to an embedder — `text`, or `text` with a heading breadcrumb prepended (`HybridChunker.contextualize()`) where the chunker supports it, or (in `02-token-aware-chunking.ipynb`, when `overlap > 0`) with the previous chunk's own tail prepended ahead of that — `HybridChunker` has no native overlap between chunks, so this is reconstructed rather than provided. Equal to `text` when there's no contextualization and no overlap. |
| `token_count` | `int \| None` | Token count under the chunker's own tokenizer. `None` for the character splitter, which sizes chunks by word count, not tokens — a number here would imply a precision the splitter doesn't have. |
| `section_path` | `str` | Heading breadcrumb, e.g. `"Results > Outcomes Table"`. `""` when the source has no heading structure to walk (e.g. plain, unheaded text). |
| `pages` | `list[int]` | Source page numbers this chunk's content came from. `[]` when unknown — always empty for the markdown-sourced synthetic examples in this stage, since markdown carries no page provenance; a PDF-sourced document (stage 01's real output) populates this. |
| `metadata` | `dict` | Document-level bibliographic passthrough (title, doi, pmcid, year, journal, …) — attached once per document, not recomputed per chunk. `{}` when the caller supplies nothing. |

Retrieval (stage 04) depends on this shape being the same regardless of which
notebook produced the chunks — that's the entire point of one shared
contract across all three chunkers.

## How to run

```bash
cd anacodic-agentic-cookbook
pip install -r requirements.txt -r 01-modules/02-chunk/requirements.txt
jupyter notebook 01-modules/02-chunk/01-character-splitting.ipynb
```

No API key, no account, no network access is needed for any of the three
notebooks. `03-store-backends.ipynb`'s Chroma path is fully local
(file-based, no server); its Pinecone path only activates once
`PINECONE_API_KEY` is set in `.env` and otherwise stops at a named error
instead of a stack trace.

## Execution report

All three notebooks were executed with
`jupyter nbconvert --execute --to notebook --inplace <file>.ipynb` and ran
**every cell cleanly, no errors**, on this machine (Python 3.12, the versions
pinned in `requirements.txt`).

One environment note, not specific to this stage: `nbconvert` (and, per
`jupyter_server`'s `cwd_for_path`, interactive Jupyter too) sets a notebook's
working directory to the notebook's *own* folder, not the directory Jupyter
was launched from. `import nbio` therefore needs the repo root on `sys.path`
*before* `nbio.bootstrap()` can run — which `bootstrap()` itself can't
provide, since it can't be called until after the bare `import nbio`
succeeds. Every notebook's first code cell now does that walk-up itself
(mirroring `nbio.py`'s own `_find_repo_root()`) before `import nbio`, so no
`PYTHONPATH` or special launch directory is needed — this applies to every
stage that uses `nbio`, not something specific to chunking.

- `01-character-splitting.ipynb` — clean. The tuned synthetic table (14
  repeats of one sentence + an 8-row table) reliably reproduces the cut: the
  splitter's 400-word budget lands inside the table, chunk 0 keeps the header
  and the first six rows, chunk 1 resumes mid-table with **no header row at
  all**.
- `02-token-aware-chunking.ipynb` — clean. The identical table, converted to
  a `DoclingDocument` via Docling's markdown backend (local, no model
  download), survives `HybridChunker` as a single chunk tagged
  `chunk_type="table"`, header intact — asserted in the notebook's last cell,
  not just printed.
- `03-store-backends.ipynb` — clean. Dry-run counts chunks with no upsert;
  the real run upserts to a local, file-based Chroma collection (patched for
  this environment's older system `sqlite3` via `pysqlite3-binary`); a
  second run with the same progress file correctly skips both already-done
  papers; and calling the `pinecone` backend with no `PINECONE_API_KEY` set
  stops at a named error, not a stack trace.

## Not in scope here

- Choosing an embedding model or vector dimension (stage 03).
- Measuring which chunker retrieves better (stage 05 — this stage only makes
  the comparison possible by putting all three approaches in one place).
