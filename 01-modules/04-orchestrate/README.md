# 04 · Orchestrate

**In → out, in 5 lines:** a question goes in. Out comes an answer, an
abstention, or a decision not to retrieve at all — plus a log of every
decision taken to get there: whether a lookup was needed, which source was
tried first, what the grounding verdict was on each attempt, and why a retry
did or did not happen. This is the layer that turns a fixed pipeline into an
agent: retrieval stops being the workflow and becomes one tool, called or not
called on the evidence.

## Why this stage exists

Every notebook in `01-modules/01-tools/` is a fixed sequence. Step 1, then 2,
then 3, in the same order, for every question.
`04-retrieve/08-backend-cascade.ipynb` tries `pinecone -> pgvector -> local`
because that order is written into the function body.
`04-retrieve/09-multi-query.ipynb` runs every phrasing up front, before it has
seen a single result. `05-gate/01-grounding-check.ipynb` produces a verdict —
`grounded: True / False / None` — that **nothing upstream reads**. It is a
report printed at the end of a pipeline that has already finished.

Those are the three gaps this stage fills, in order: decide *whether* to
retrieve, decide *where from*, and act on the verdict once evidence exists.

## Notebooks

| Notebook | What it decides | Needs a key? |
|---|---|---|
| [`01-should-i-retrieve.ipynb`](01-should-i-retrieve.ipynb) | Whether a document lookup is needed at all, before anything else runs | No. Rule-based throughout. Step 7 adds an optional model-driven router behind `GROQ_API_KEY` / `OPENAI_API_KEY`; with no key it says so and returns the rule verdict unchanged. |
| [`02-source-choice.ipynb`](02-source-choice.ipynb) | Which source to try first, from the question's domain and each source's cost/latency | No. Three in-memory stand-in sources, no network. |
| [`03-retry-on-verdict.ipynb`](03-retry-on-verdict.ipynb) | Whether to retry, based on the grounding verdict on what came back | No. Deterministic generator stand-in and deterministic grounding pass. |
| [`04-plan-act-reflect.ipynb`](04-plan-act-reflect.ipynb) | All three, as one closed cycle that can revise its own plan | No. |

Read them in order. Each builds directly on the previous one's decision, and
`04` is the three of them wired into a single loop.

## How to run

```bash
pip install -r ../../requirements.txt -r requirements.txt
jupyter notebook .
```

All four run end to end with no API key, no network and no GPU.

## Design notes

**Rule-based first, deliberately.** A routing decision made by a model has two
independent ways to fail — broken wiring, or poor judgment — and from the
outside they look identical. A keyword rule has no judgment to blame, so the
first version proves the *wiring*: the decision is read, acted on, and logged,
and retrieval genuinely does not happen when the decision says not to.
`01`'s Step 6 proves that with a call counter, which is the only thing that
distinguishes a wired-up decision from one that is computed, printed, and then
ignored. The rule path is also the offline path this repo's "run in 60
seconds" promise depends on; the model layer in `01`'s Step 7 sits beside it
and never replaces it.

**Every decision returns a reason, not a boolean.** When a routing decision is
wrong, the only useful question is which rule fired, and a bare `True`/`False`
cannot answer it. Every verdict in this stage carries the rule and the reason.

**The three-valued grounding verdict is kept as the gate produces it.**
`grounded: None` means "nothing found wrong, and no judge configured to say
more" — which is not the same as grounded. A retry policy keying only off
`False` would never fire on the most common offline case; one keying off
`None` alone would retry on every clean answer forever. `03`'s `is_weak`
handles both: `False`, or `None` below a score floor.

**Caps are mandatory and demonstrated, not asserted.** A retry loop driven by
a judgment that may never be satisfied is an unbounded loop with a paid model
inside it. Both `03` and `04` cap attempts, and both *prove* the cap by
running the same inputs at two different caps and showing two different
attempt counts — one run stopping at 2 could always have been the data.
`03` proves it against a checker rigged to return `grounded: False` forever;
`04` proves it on a question neither store can answer, with nothing rigged.
Separately, `03`'s Step 8 drives `nbio.cost_meter` until it raises
`BudgetExceeded`, because the attempt cap and the spend ceiling bound
different things and fail independently.

**Every attempt goes through the meter.** On the offline path there is no paid
call, so zero tokens are recorded — the entry still counts the attempt, which
is what makes `meter.calls` a usable count of loop iterations. With a key set,
the same line carries real usage and the ceiling is live.

**The abstention uses the gate's own prefix.** When the cap is reached and the
verdict is still weak, `04` returns a string starting `INSUFFICIENT EVIDENCE`
— exactly what `05-gate`'s `check_grounding` short-circuits on. Step 8 checks
that directly, so the loop's give-up output is one the existing gate already
reads correctly rather than a new convention.

## What these notebooks do not prove

- **A synthetic example that improves is not evidence of improvement.** `03`
  and `04` both improve a result on a two-chunk store, with hand-written
  reformulations chosen to use the store's own vocabulary, against a generator
  stand-in built to over-claim on cue. That proves the *wiring*: a verdict is
  read, a retry happens only when it is weak, the cap holds. Whether retrying
  on a weak verdict improves answers on real questions is an empirical
  question these notebooks do not touch. It needs
  [`04-benchmarks/clinical-retrieval/`](../../04-benchmarks/clinical-retrieval/)
  run across the question set with and without the loop — separate work, not
  done.
- **Eight questions is not an evaluation.** `01`'s labelled set was written
  alongside the rules it tests. 7/8 agreement says the rules are
  self-consistent, nothing more — and the 8th is a documented miss, asserted
  so it cannot silently change.
- **The cost and latency numbers in `02` are written, not measured.** They are
  plausible orders of magnitude for a local store, a hosted index and a
  metered search API. Real numbers belong in a config this policy reads.
- **Nothing here measures whether the loop makes results worse.** A revision
  can surface a higher-scoring chunk that is less relevant. This stage has no
  instrument for that.

## Not in scope

- **A fully general LLM-driven "should I retrieve" classifier.** Rule-based is
  the done condition here. The model layer in `01`'s Step 7 is the seam a real
  classifier would plug into — no prompt tuning, no labelled evaluation set,
  no confidence calibration was done.
- **Multi-agent orchestration.** A supervisor routing to specialist agents is
  a different problem. This stage is the single-agent decision loop.
- **Query rewriting.** The reformulations in `03` and `04` are hand-written,
  exactly as in `04-retrieve/09-multi-query.ipynb`. Generating them with a
  model is a capability this repo does not build anywhere.
- **Memory across questions.** Every loop starts with empty evidence. Carrying
  state between questions belongs in `01-modules/02-memory`, which is empty.
- **A framework.** No LangGraph, no LangChain, no Strands. The loop is about
  forty lines of plain Python, which is the point — a reader can see exactly
  what a framework's graph would be doing for them.
