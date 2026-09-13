# Notebook authoring standard

This is the shape a new notebook in `02-experiments/` should take. It's a
different rhythm from `01-modules/`, on purpose — read why below before you
open a blank notebook.

## Why this isn't just "however `01-modules/` does it"

`01-modules/` notebooks are a finished lesson, read top to bottom once —
bundling several related functions into one cell is fine there. A notebook
someone is about to **copy from, debug, or extend** needs a different
rhythm: one action per cell, so a reader can find the one line that broke
instead of un-bundling five functions first to find it. That's exactly the
situation a `02-experiments/` notebook is written for — someone else will
read it planning to reuse or build on it, not just read it once.

Concrete example of the problem this avoids: a notebook that defines
`upsert_chunks`, `_score_chunks`, `retrieve`, `max_score`, and `is_grounded`
together in one cell, before anything is run, forces a reader to hold all
five in their head before seeing any of them work. Splitting that into five
small, run-and-look steps is what this standard asks for.

## The standard

1. **One action per code cell.** A cell either defines one function, or
   calls one function and looks at its output — never both, never several
   functions bundled together.
2. **A capabilities table before the first code cell.** Name | what it does
   | one example — so a reader knows what they're about to see before they
   see it.
3. **A markdown "Step N" header immediately before each code cell**, stating
   what that one cell is about to do and why.
4. **Look at real output before writing the next step.** No cell should
   chain into a second, unseen transformation before the first one's result
   has been printed and read.
5. **Keep the house rules `01-modules/` already gets right, unchanged:** a
   real anchor example (never invented mid-write), the offline/no-key path
   named explicitly, and any known gap stated in the notebook itself — not
   left implicit.
6. **Build the whole notebook incrementally, not just its cells.** Start
   with the smallest working version, test it, add exactly one capability,
   test that, then add the next. Each version is a strictly larger,
   separately-run piece of the notebook — never a rewrite of what came
   before it.
7. **Any safety/guardrail check is set up first, before capability-building
   starts.** Nothing is added on top of a system that hasn't already been
   shown to refuse the thing it should refuse.

## Worked example — the before/after this standard targets

**Before** (one cell, five functions, nothing run until all five exist):
```python
def upsert_chunks(course_id, chunks): ...
def _score_chunks(chunks, qvec, course_id): ...
def retrieve(course_id, query, k=5): ...
def max_score(chunks): ...
def is_grounded(chunks): ...
```

**After**, under this standard (five cells, not one):
```
[markdown] Step 1 — store chunks for one course
[code]     def upsert_chunks(course_id, chunks): ...
[code]     upsert_chunks("bio201", bio201_chunks)   # <- look: how many stored?

[markdown] Step 2 — score a query against that course's chunks
[code]     def _score_chunks(chunks, qvec, course_id): ...

[markdown] Step 3 — the retrieve function this notebook will actually reuse
[code]     def retrieve(course_id, query, k=5): ...
[code]     retrieve("bio201", "what do mitochondria do?", k=3)  # <- real output

[markdown] Step 4 — is the top hit good enough to trust?
[code]     def max_score(chunks): ...
            def is_grounded(chunks): ...
```

## Not yet — exporting to a standalone `.py` file

Exporting a working notebook into a standalone `.py` module (so it can be
wired into `eval.py`'s `EVAL_RETRIEVAL_BACKEND`, for example) is a real
pattern worth knowing about, but it's a separate, explicit step for later —
not part of what this standard asks of a first notebook. Get the notebook
right first.

## Where this applies

- **Applies to every new notebook** written under
  `02-experiments/<your-name>-<topic>/`.
- **Does not apply retroactively.** `01-modules/` is not rewritten by this
  standard. If a contributor's cleaner version later beats a benchmark or is
  judged clearly more teachable, it is promoted into `01-modules/` through
  the existing [promotion path](../CONTRIBUTING.md#the-promotion-path) — any
  rewrite happens as part of that promotion, not as a separate cleanup pass
  now.

## Not in scope

- Rewriting any existing `01-modules/` notebook to this standard — that's a
  promotion-path decision, made per notebook.
- A pre-commit lint that enforces "one action per cell" mechanically. Worth
  naming as a future option; not required for this standard to take effect,
  since near-term enforcement is review, not tooling.
