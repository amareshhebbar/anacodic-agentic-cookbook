# 01 · Extract

A document — a born-digital PDF, or a photo/scan of a page — in. Structured
text out: headings, paragraphs, and tables as tables (not flattened prose),
plus cropped table/figure images. A clean printed PDF goes through docling.
A page image goes through OCR or a vision model instead, never through
docling's PDF pipeline. Chunking that page's structure into retrievable
units is the next stage, not this one.

## Two known constraints

1. **Docling here is scoped to PDF, by this stage's own choice, not a
   technical limit.** `extract_pdf()` in `01-pdf-printed.ipynb` refuses
   anything that isn't a `.pdf`. Docling itself will build a default
   pipeline for an image if you let it (that notebook proves it on
   `sample-data/handwriting-sample.png`). The reason images still go a
   separate way (`03-orientation`, `04-handwriting-ocr`) is a deliberate
   design choice: PDFs go through Docling, individual page images go
   through Google Vision (or, here, RapidOCR/Groq) instead.
2. **The handwriting vision path is broken and stays broken until someone
   fixes it.** `04-handwriting-ocr.ipynb` calls Groq's vision API with the
   model `meta-llama/llama-4-scout-17b-16e-instruct`, which Groq retired on
   2026-08-16. That notebook's first cell says so and the call is expected
   to fail with a stated reason, not a stack trace. Picking a live
   replacement model and proving it on the sample page is this stage's
   posted first issue.

## Data

`sample-data/` holds two files, both authored for this repo rather than
sourced from any real document, scan, or student work:

- `printed-page.pdf` — a synthetic, one-page, born-digital PDF: a title,
  two short original paragraphs describing this pipeline, and a five-row
  ruled table. Built with PyMuPDF.
- `handwriting-sample.png` — **not real handwriting.** A machine-rendered
  page (an italic system font, a few pixels of per-line jitter) shaped like
  a worked maths answer, so the vision-OCR notebook has something to point
  at that carries no privacy or licensing question. Built with Pillow.

No real document, scan, or partner/student data of any kind is present here.

## How to run

```bash
cd anacodic-agentic-cookbook
pip install -r requirements.txt
pip install -r 01-modules/01-tools/01-extract/requirements.txt
jupyter notebook 01-modules/01-tools/01-extract/01-pdf-printed.ipynb
```

Each notebook's first code cell walks up from its own directory to find
`nbio.py` and puts the repo root on `sys.path` before `import nbio` runs, so
it works whether you open it from `jupyter notebook`/`jupyter lab`, run it
headlessly with `nbconvert`, or launch Jupyter from any working directory —
no `PYTHONPATH` needed:

```bash
jupyter nbconvert --execute --to notebook --inplace \
  01-modules/01-tools/01-extract/01-pdf-printed.ipynb
```

No API key or GPU is required for `01`, `02`, or `03`. `04` runs with no
key too — it fails cleanly at the Groq call, which is the point.

## What each notebook actually did, last run in this environment

This environment has no GPU and an older CPU (no AVX2/FMA — some torch
kernels print harmless `NNPACK` warnings as a result; `TORCH_CPP_LOG_LEVEL
=ERROR` quiets them). Kraken is not installed and no Kraken model is on
disk. Given that:

| Notebook | Ran clean, top to bottom? | Needs |
|---|---|---|
| `01-pdf-printed.ipynb` | Yes, all cells | Nothing. First cell ~30s (docling model load). |
| `02-tables-and-layout.ipynb` | Yes, all cells | Nothing. |
| `03-orientation.ipynb` | Yes, all cells | Nothing to run. |
| `04-handwriting-ocr.ipynb` | Yes, all cells — the vision call fails on purpose | `GROQ_API_KEY` (still won't transcribe until `GROQ_VISION_MODEL` names a live model) |

### 03's rotation-correction finding

This notebook measures how much rotation costs OCR quality, and how much
correcting it recovers, using RapidOCR on `sample-data/printed-page.pdf`.
Last run:

| | mean confidence | characters |
|---|---|---|
| upright | 0.985 | 956 |
| rotated 180°, uncorrected | 0.920 | 706 |
| rotated, then corrected | 0.985 | 956 |

Rotation costs confidence and yield; correcting it recovers both. The
notebook's wrap-up cell notes that a segmenter with its own text-direction
classifier (like RapidOCR's) partially self-corrects rotated crops, while a
segmenter without one can also propose the wrong reading order on rotated
input, compounding into worse recognition — a failure mode this clean,
synthetic example doesn't reproduce.

## Notebooks

| Notebook | What it does |
|---|---|
| [`01-pdf-printed.ipynb`](01-pdf-printed.ipynb) | Docling on a clean, born-digital PDF — the baseline path. |
| [`02-tables-and-layout.ipynb`](02-tables-and-layout.ipynb) | What survives a table (structured `table_markdown`) versus what silently flattens (a text-only walk that skips `TableItem`s entirely). |
| [`03-orientation.ipynb`](03-orientation.ipynb) | The rotation-correction finding, demonstrated with RapidOCR. |
| [`04-handwriting-ocr.ipynb`](04-handwriting-ocr.ipynb) | The vision/handwriting path, marked broken, with the exact ask for a contributor. |

## Not in scope here

- Fixing the vision path (`04`'s posted first issue).
- Measuring extraction accuracy against a gold set — that's `06-bench`.
- Turning this stage's output into retrievable chunks — that's `02-chunk`.
