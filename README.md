# Anacodic Agentic Cookbook

The five parts of a working AI agent — tools, memory, guardrails, an
orchestrator, and observability — each built in plain Python, so you can see
what a framework would otherwise be doing for you.

One of those parts, tools, is built all the way down: document → structured
text → chunks → retrieval → grounding → evaluation, the full machinery behind
a production document-search system. From the agent's side, all of that is a
single function it can choose to call.

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
jupyter notebook 01-modules/01-tools/03-embed/01-offline-embeddings.ipynb
```

That notebook runs end to end with no key: it uses the deterministic hash-based
embedding fallback (real wiring, not semantically meaningful vectors — the
notebook says so up front). Once it runs, add a free key (see each stage's
`README.md` for which one) to move to a real model.

## The five parts

```
                    ┌──────────────────────────────────┐
                    │          ORCHESTRATOR             │
                    │      decides WHAT happens next     │
                    └───────────────┬──────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
      │    TOOLS      │      │    MEMORY     │      │  GUARDRAILS   │
      │ how it DOES   │      │ what it KNOWS │      │ what it MAY   │
      │ things        │      │ from before   │      │ NOT do        │
      └──────────────┘      └──────────────┘      └──────────────┘
              └─────────────────────┼─────────────────────┘
                                    ▼
                    ┌──────────────────────────────────┐
                    │          OBSERVABILITY            │
                    │   what actually HAPPENED (after)   │
                    └──────────────────────────────────┘
```

| # | Part | Answers |
|---|---|---|
| [01-tools](01-modules/01-tools/) | Tools | how does it *do* anything? |
| [02-memory](01-modules/02-memory/) | Memory | what does it carry forward? |
| [03-guardrails](01-modules/03-guardrails/) | Guardrails | what may it never do? |
| [04-orchestrate](01-modules/04-orchestrate/) | Orchestrator | what happens next? |
| [05-observe](01-modules/05-observe/) | Observability | what actually happened? |

**`01-tools` builds one tool, all the way down. The other four stages build the
agent that decides when to use it.**

The folders are numbered in build order, not architecture order — an
orchestrator cannot be built before the tools it calls. See
[`01-modules/README.md`](01-modules/) for why the numbers and the diagram
deliberately disagree.

### Inside 01-tools — six stages, one tool

| # | Stage | In → out |
|---|---|---|
| [01-extract](01-modules/01-tools/01-extract/) | Extraction | a document (PDF, scanned page, photo) → structured text and tables |
| [02-chunk](01-modules/01-tools/02-chunk/) | Chunking | structured text → token-aware chunks, tables intact |
| [03-embed](01-modules/01-tools/03-embed/) | Embedding | chunks → vectors, in a store of your choice |
| [04-retrieve](01-modules/01-tools/04-retrieve/) | Retrieval | a query → ranked, deduplicated, scored results |
| [05-gate](01-modules/01-tools/05-gate/) | Grounding | a query, an answer, and retrieved context → refuse, or prove it |
| [06-bench](01-modules/01-tools/06-bench/) | Evaluation | questions + gold answers → a score table |
| [07-as-a-tool](01-modules/01-tools/07-as-a-tool/) | Tool interface | all of the above → one callable tool, plus a second to choose between |

Those six sub-stages are the deepest part of this repo, and to an agent they
are a single function. That relationship — not a flattening of it — is what
`07-as-a-tool` makes concrete. With one tool there is no choice to make; with
two, something has to make it, and that is the difference between a retrieval
pipeline and an agent.

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

## License & ownership

Created and maintained by **Anacodic AI Labs** (https://anacodicai.org).
Copyright 2026 Anacodic AI Labs and contributors — see [NOTICE](NOTICE).

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE). Includes a
patent grant: contributing here also grants everyone a license to any patent
claim your contribution would otherwise trigger.

Contributors keep the copyright to their work and are credited; by contributing
you also grant Anacodic AI Labs a licence to reuse and relicense it (e.g. in
courses and publications) — see [CONTRIBUTING.md](CONTRIBUTING.md).
