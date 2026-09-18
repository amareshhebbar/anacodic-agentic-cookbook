# 01 · Modules — the five parts of an agent

One folder per part. Together they are a working agent, built in plain
Python so you can see what a framework would otherwise be doing for you.

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

## The stages

| # | Stage | Answers |
|---|---|---|
| [01-tools](01-tools/) | Tools | how does it *do* anything? |
| [02-memory](02-memory/) | Memory | what does it carry forward? |
| [03-guardrails](03-guardrails/) | Guardrails | what may it never do? |
| [04-orchestrate](04-orchestrate/) | Orchestrator | what happens next? |
| [05-observe](05-observe/) | Observability | what actually happened? |

**`01-tools` builds one tool, all the way down. The other four stages build
the agent that decides when to use it.**

## Why the numbers disagree with the diagram

The diagram puts the orchestrator on top, because that is where it sits
architecturally — it contains everything else. The folders are numbered in
**build order** instead, and that is deliberate: an orchestrator cannot be
built before the tools it calls, and numbering it `01` would mean the first
folder a newcomer opens is the one that depends on all the others.

Read the folders in number order. Read the diagram to understand the shape.

## Six stages inside one

`01-tools` contains seven sub-stages — extract, chunk, embed, retrieve, gate,
bench, and `07-as-a-tool` — the first six of which together build a single
retrieval tool, with the seventh turning that tool into something an agent
can actually call. That is where most of this repo's depth lives. See
[`01-tools/README.md`](01-tools/) for why that is the right relationship
rather than a flattening.

## Status

All five parts are built and verified — every notebook listed runs, offline
by default, with real executed output rather than a scaffold. Each stage's
own `README.md` states any known gap plainly rather than leaving it implicit.

## House rules every stage keeps

- **Offline first.** Every stage has a path that runs with no API key, no
  network and no GPU. Where a real model is genuinely required, the notebook
  reports "not set, skipping" rather than crashing.
- **Real output, not described output.** A number shown in a notebook is
  read from what the code produced, never restated inline.
- **Known gaps are stated in the notebook itself**, not left implicit.
- **No framework.** Plain Python throughout, on purpose.
