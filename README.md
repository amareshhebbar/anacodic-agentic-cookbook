# Anacodic Agentic Cookbook

Document → structured text → chunks → retrieval → evaluation. The core
engines behind document-search and retrieval-augmented generation systems,
built so anyone can learn them, run them, and improve them.

> **Disclaimer.** Nothing in this repository is a medical device, a clinical
> decision-support tool, or validated for patient care. The clinical-domain
> notebooks and benchmark exist to teach and measure retrieval-system design,
> using published literature and synthetic or public-domain examples only. Do
> not use any output here to inform a real clinical, educational, or legal
> decision.

## Run in 60 seconds

No account, no API key, no GPU required for the first pass — every stage ships
an offline path.

```bash
git clone https://github.com/anacodicAI-labs/anacodic-agentic-cookbook.git
cd anacodic-agentic-cookbook && pip install -r requirements.txt
jupyter notebook 01-modules/03-embed/01-offline-embeddings.ipynb
```

That notebook runs end to end with no key: it uses the deterministic hash-based
embedding fallback (real wiring, not semantically meaningful vectors — the
notebook says so up front). Once it runs, add a free key (see each stage's
`README.md` for which one) to move to a real model.

## The six stages

| # | Stage | In → out |
|---|---|---|
| [01-extract](01-modules/01-extract/) | Extraction | a document (PDF, scanned page, photo) → structured text and tables |
| [02-chunk](01-modules/02-chunk/) | Chunking | structured text → token-aware chunks, tables intact |
| [03-embed](01-modules/03-embed/) | Embedding | chunks → vectors, in a store of your choice |
| [04-retrieve](01-modules/04-retrieve/) | Retrieval | a query → ranked, deduplicated, scored results |
| [05-gate](01-modules/05-gate/) | Grounding | a query, an answer, and retrieved context → refuse, or prove it |
| [06-bench](01-modules/06-bench/) | Evaluation | questions + gold answers → a score table |

Each stage folder is self-contained: its own `README.md` (what goes in, what
comes out, and the current benchmark number), its own notebooks with the real,
runnable code — not a scaffold — and its own `requirements.txt`.

## Contributions

| # | Folder | Contributor | Stage | Result |
|---|---|---|---|---|
| _(none yet)_ | | | | |

Add your own folder under `02-experiments/` (an attempt) or `03-use-cases/`
(a finished demo) — see [CONTRIBUTING.md](CONTRIBUTING.md).

## What you get

- **Credit that lasts.** Move a benchmark number that lands in a paper →
  named in that paper's Methods section, and co-authorship on it. Maintain a
  stage → permanent maintainer credit in [CONTRIBUTORS.md](CONTRIBUTORS.md).
- **Public, attributable work.** What you build here is yours to show,
  regardless of what happens to any product built on top of it.

Full detail in [CONTRIBUTING.md](CONTRIBUTING.md).

## What's not here

Partner and user data, prompts, deployment configuration, and application
code (APIs, frontends, auth) stay out of this repo. This is the engines, not
the applications.

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE). Includes a
patent grant: contributing here also grants everyone a license to any patent
claim your contribution would otherwise trigger.
