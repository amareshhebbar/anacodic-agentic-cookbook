# 01 · Tools — how the agent DOES things

An agent produces text. A tool is how it produces an *effect* — how it looks
something up, calculates something, or changes something in the world. The
model never runs a tool itself: it reads a tool's name, description and
argument schema, emits a structured request to call it, and code outside the
model does the rest and hands the result back.

This stage teaches that mechanism, and builds one tool all the way down.

## Six stages, one tool

Stages `01-extract` through `06-bench` look like six separate things. From
the agent's point of view they are one:

```
    01-extract   bytes      → text
    02-chunk     text       → pieces
    03-embed     pieces     → vectors           ALL OF THIS
    04-retrieve  question   → evidence     ───────────────────►  ONE function
    05-gate      evidence   → trust verdict
    06-bench     verdict    → a defensible number

                                          search_documents(query, k=5) -> list[dict]
```

That is not a criticism of the depth. It is what a good tool looks like:
enormous care behind a one-line signature. But it is why the stage is
structured this way — the six stages build the tool, and `07-as-a-tool`
is where it becomes one.

## The line where a pipeline becomes an agent

With **one** tool there is no choice to make, so a fixed sequence is the
whole system — that is a retrieval pipeline. With **two**, something has to
decide which to call, and that decider is an agent.

`07-as-a-tool/03-a-second-tool.ipynb` is where this repo crosses that line.
The chooser itself lives in [`04-orchestrate`](../04-orchestrate/).

## Stages

| Stage | In → out |
|---|---|
| [01-extract](01-extract/) | a document (PDF, scanned page, photo) → structured text and tables |
| [02-chunk](02-chunk/) | structured text → token-aware chunks, tables intact |
| [03-embed](03-embed/) | chunks → vectors, in a store of your choice |
| [04-retrieve](04-retrieve/) | a query → ranked, deduplicated, scored results |
| [05-gate](05-gate/) | a query, an answer, and retrieved context → refuse, or prove it |
| [06-bench](06-bench/) | questions + gold answers → a score table |
| [07-as-a-tool](07-as-a-tool/) | all of the above → one callable tool, plus a second one to choose between |

Each stage folder is self-contained: its own `README.md`, its own notebooks
with the real runnable code, and its own `requirements.txt`.

## Where to start

`03-embed/01-offline-embeddings.ipynb` runs with no key, no network and no
model download — it is the fastest way to confirm the repo works on your
machine. Then read the stages in order, or jump straight to `07-as-a-tool`
if what you want is the agent-facing view rather than the internals.

## Boundary with 03-guardrails

`05-gate` judges **evidence that came back** — it scores a produced answer
against retrieved context. [`03-guardrails`](../03-guardrails/) stops an
**action before it happens** — it blocks an input, or a tool call, from
running at all. Different layers, and deliberately in different stages.
