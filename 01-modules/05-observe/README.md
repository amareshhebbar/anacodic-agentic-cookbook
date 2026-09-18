# 05 · Observe — what actually happened

**In → out, in 5 lines:** a run that has already finished goes in. Three kinds of
record come out — what it **cost** (tokens, calls, dollars, against a ceiling),
what it **produced** (`runs/<run_id>/*.json`, read back rather than restated),
and **why it did that** (a step-by-step trace of every decision, with the reason
recorded at the decision). This is the stage you reach for after a run, not
during it: nothing here changes what an agent does, and everything here changes
what you can find out about it.

## The three levels, cheapest first

| Level | Question it answers | Cost to add | Notebook |
|---|---|---|---|
| **Counting** | What did it cost? | one context manager | `01-cost-and-budget.ipynb` |
| **Artifacts** | What did it produce? | three JSON writes per run | `02-run-artifacts.ipynb` |
| **Tracing** | Why did it decide that? | one span per step, plus a `why` string | `03-tracing.ipynb` |

They stack. Counting without artifacts gives you a number that scrolls past.
Artifacts without tracing tell you a run abstained but not what emptied the
evidence list. Tracing without the first two tells you the path and leaves you
guessing at the bill. The first two are cheap enough that there is no reason not
to have them on every run; the third is the one you wish you had turned on before
the run that went wrong.

## Notebooks

| # | Notebook | What it teaches | Needs a key? |
|---|---|---|---|
| 01 | [`01-cost-and-budget.ipynb`](01-cost-and-budget.ipynb) | `nbio.cost_meter` taught rather than assumed: the rate table, `price_for`'s longest-key fallback, what `Meter.record()` accumulates, and both `BudgetExceeded` and `UnpricedModel` actually firing — caught, printed, asserted | No. Synthetic token counts throughout; no call is ever made |
| 02 | [`02-run-artifacts.ipynb`](02-run-artifacts.ipynb) | Writing a run's `manifest`/`papers`/`answer` and reading them back with `nbio.load_run()` / `nbio.list_run_ids()`, plus the repo's read-don't-restate rule with drift demonstrated on a real re-run | No. Writes and reads JSON under `runs/` |
| 03 | [`03-tracing.ipynb`](03-tracing.ipynb) | A ~60-line trace recorder in plain Python, a toy multi-step orchestrator run through it, the trace printed as a tree, and the trace used to explain an outcome that looks wrong | No. Stubbed steps; a trace records control flow, not model output |

## Design notes

**`nbio.cost_meter` was used everywhere and explained nowhere.** Five stages in
`01-tools` open a meter around their paid calls. Until this stage, nothing said
what the ceiling does when it fires, or why an unpriced model is an error rather
than a $0 line item. Notebook 01 is that missing page, and it fires both
exceptions for real rather than describing them — a budget check is arithmetic
over a usage block, so it needs no key and no network to be genuine.

**An unknown rate under a budget is a hard stop, not a fallback.** Charging an
unpriced model $0 would make the ceiling unenforceable for exactly the model that
needs it most: the newly swapped-in one nobody has priced yet. `nbio` refuses.
The private product's meter fails closed the same way, for a reason it recorded
in its own docstring — its default model was deprecated by the provider, a
replacement was swapped in, and a $0 fallback would have reported a perfect
`$0.0000` run while spending real money.

**A number displayed in a notebook is read from the artifact, never restated.**
This is the rule the whole artifacts level exists to serve. An inline number is
correct the day it is typed and silently wrong after the next pipeline change;
`nbio.load_run()` cannot go stale, because it is not a claim about the run, it is
the run. Notebook 02 shows both side by side and then re-runs the pipeline so the
restated one goes wrong on screen.

**Tracing is new work in this repo, and deliberately framework-free.** Nothing in
this lab traced anything before this stage. The recorder in notebook 03 is one
dataclass and one context manager, no dependencies — no OpenTelemetry, no
LangSmith, no Langfuse, no vendor SDK. That is not a rejection of those tools; it
is that a reader cannot learn what a trace *is* from an integration. The field
that does the work is `why`: a log line says `branch=narrow`, a span says
`branch=narrow because 2 of 3 required keywords matched`, and no framework can
generate that sentence — only the code taking the branch can.

**Everything runs offline.** No notebook in this stage needs an API key, and none
will use one if it is present.

## Where run artifacts go

Under `nbio.runs_dir()` — `runs/` at the repo root — and nowhere else. Every run
id these notebooks create is prefixed `demo-observe-`, and `runs/` is gitignored,
so nothing written here is committed.

One side effect worth knowing: `nbio.list_run_ids()` sorts by mtime, so after
running this stage the newest run on disk is a demo run, and a bare
`nbio.load_run()` in another notebook will find it instead of that notebook's own
run. Pass an explicit run id, or delete the demo runs when you are done —
notebook 02's last cell prints the three lines that do it.

## Setup

```bash
pip install -r ../../requirements.txt   # repo root, if you haven't already
pip install -r requirements.txt         # from this directory
jupyter notebook 01-cost-and-budget.ipynb
```

## What did not come across

- **Per-node cost itemization, the per-call log, and thread safety** from the
  product's meter — a notebook makes a handful of calls in one kernel, and all
  three would be machinery with nothing to do. Detailed in notebook 01.
- **The S3 mirror, local cleanup after upload, atomic writes, schema versioning
  and retention** from the product's run store. Detailed in notebook 02.
- **Distributed tracing, automatic instrumentation, async-safe span stacks, and
  stored prompt/response bodies.** The last is deliberate as well as unbuilt:
  storing payloads per step is what makes a trace replayable, and is also how
  partner data ends up in a public repo. Detailed in notebook 03.
- **A real orchestrator to trace.** `01-modules/04-orchestrate` is empty, so
  notebook 03 traces a five-step toy with no loop or retry. The recorder is
  stage-agnostic on purpose; it should be pointed at the real thing once there is
  one.
