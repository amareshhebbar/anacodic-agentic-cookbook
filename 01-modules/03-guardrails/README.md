# 03 · Guardrails

**In → out, in 5 lines:** a user input, or a proposed tool call, goes in. A
permit/refuse decision comes out — *before* anything is spent or executed. A
refusal carries codes (`scope_gate:out_of_domain`) or a JSON blob the model
reads mid-turn, never a bare `False`. This is the "what the agent may NOT do"
part of an agent: the layer that costs almost nothing, runs first, and is the
only layer whose failure is unrecoverable.

Three notebooks, in order: refuse an input before paying for it, refuse a tool
call before it executes, and — the one that matters most — decide what a guard
does when the guard itself breaks.

## The boundary against `01-tools/05-gate`

Both stages get called "the check", and contributors reliably build one when
they meant the other. Writing this down is why this section exists:

> **`01-tools/05-gate` judges EVIDENCE THAT CAME BACK.** It inspects a produced
> answer against retrieved context and scores whether it is grounded. By the
> time it runs, the retrieval has happened and the model has been paid. Its
> output is a verdict *about* finished work.
>
> **`03-guardrails` — this stage — STOPS AN ACTION BEFORE IT HAPPENS.** It
> blocks an input from being processed, or a tool call from running at all.
> When it says no, there is no answer to judge, because nothing ran.

| | `01-tools/05-gate` | `03-guardrails` (here) |
|---|---|---|
| Runs | **after** the work | **before** the work |
| Input | an answer + the context it should have come from | a query + a proposed action |
| Output | grounding score, flagged quotes, orphan citations | permit / refuse |
| Cost when it fires | the answer was already generated and paid for | zero — the thing never ran |
| Worst case if wrong | a bad answer is shown, or a good one withheld | an unsafe action executes, or a safe one is blocked |
| Reversible? | yes — withhold the answer | **no** — an executed tool call has already touched the world |

That last row is why these are two stages and not one. A grounding check can
afford to be late: withholding an answer after generating it still works. A
tool guard cannot, because a tool call that has already run has already sent
the email, written the row, or produced the clinical number someone will act
on. "Undo" is not a feature a guardrail gets to rely on.

Rule of thumb: **wrong output → `05-gate`. Wrong action → here.**

## Notebooks

| Notebook | Needs a key? |
|---|---|
| [`01-input-guard.ipynb`](01-input-guard.ipynb) | No. The model is a deterministic stand-in whose token counts are priced by `nbio.Meter` against the real rate table, so the guard-on/guard-off bill is arithmetic on published rates, not a guess. Step 10 makes one real metered call if `GROQ_API_KEY` or `OPENAI_API_KEY` is set, and prints "not set, skipping" if not. |
| [`02-tool-guard.ipynb`](02-tool-guard.ipynb) | No. No model is called anywhere. Pure regex, set membership, and a local tool with a side-effect counter. |
| [`03-fail-closed.ipynb`](03-fail-closed.ipynb) | No. No model is called anywhere. Every failure is injected deliberately; every dish, student and payload is synthetic. |

### `01-input-guard.ipynb` — reject before spending

A cheap deterministic scope check that runs *before* anything else, measured
three ways on the same six questions: no check, check first, and check last.
The three placements produce identical verdicts and two different bills.

> A guard that runs after the expensive thing is not a guard, it is a report.

Ported from `guidelines-generator`'s `nodes/room_a/gate_scope.py` and
`strands/planning/tools/scope_tools.py`, for two shape decisions worth
copying: the validator returns **error codes**, not a bool, and the gate
**raises** rather than returning a verdict someone can forget to read.

### `02-tool-guard.ipynb` — block a tool call

Ported from `clinical-search`'s `services/tool_guardrails.py`, with its two
dependencies (`tool_intent.py`, `query_context.py`) carried across, since the
guard is meaningless without them. Two layers: never offer a tool that the
query's intent doesn't warrant, and refuse the call anyway if the model emits
one. The second layer also checks **argument provenance** — a permitted tool
called with a BMI the user never mentioned is still blocked.

The refusal is proved, not asserted: the tool body increments a counter as its
first statement, and the counter stays at `0`.

### `03-fail-closed.ipynb` — the most valuable notebook here

Two gates from the same lab that fail in opposite directions, side by side.

| | `safe-bite` safety gate | `terrier-ta` human-review gate |
|---|---|---|
| Guards | which dishes an allergic diner sees | whether a low-confidence grade is released |
| On an error / malformed input | returns **nothing** | returns **`{"approved": True}`** |
| Direction | **fails closed** | **fails open** |
| Status | correct | **a real defect, ported unfixed** |

The rule the contrast teaches, stated in the notebook and repeated here:

> **When a guard errors, the safe default is to deny. Any guard whose error
> path grants permission is a guard in name only.**

## A known defect, carried across without correction

`terrier-ta`'s human-review gate turns a malformed resume payload into an
approval, and it is reproduced here **unaltered**, with a CAUTION comment in
the same convention as the `overall_pass` note in
`04-benchmarks/clinical-retrieval/pass_rubric.py`. Two independent routes:

- `nodes/grading/gate_human_review.py`, last line —
  `decision if isinstance(decision, dict) else {"approved": True}`. Any
  non-dict resume (a timeout resolving to `None`, a bare string, a list, or a
  literal `False`) becomes approval. `False` is the sharpest case: it is not a
  dict, so it takes the `else` branch and is converted into its own opposite.
- `nodes/grading/apply_override.py`, line 14 — `override.get("approved", True)`.
  A payload that merely *omits* the key is approved. So is `{}`, so is a
  misspelled key, so is the string `"no"` (truthy).

Composed, a resume that times out releases an unreviewed grade with no error
recorded and nothing in the final state indicating a human was meant to look.
Verified by execution in Steps 7–9.

Neither line looks wrong in review — `x if isinstance(x, dict) else <default>`
and `.get(key, True)` are everyday defensive shapes, and the eye slides over
the default. The direction of that default is the entire defect. Fixing it is
a decision for whoever owns `terrier-ta`'s grading pipeline; Step 10 shows what
the fix looks like, **separately**, without touching the port. Carrying the
flaw across honestly is the lesson, and it is a bounded first contribution for
somebody.

## No framework

Plain Python throughout — no Bedrock Guardrails, no framework guardrail
abstraction, no policy DSL. A reader should be able to see exactly what those
products would be doing on their behalf, which is: regex, set membership, an
`isinstance` check, and one decision about which way the `else` branch points.

## How to run

```bash
pip install -r ../../requirements.txt -r requirements.txt
jupyter notebook .
```

Run them in order. `01` motivates why a guard runs first, `02` shows the same
idea one level in where being late is unrecoverable, and `03` is what both of
them are worth when they break.

## What did not come across

- **`langgraph.types.interrupt` and the human-in-the-loop resume path.** Both
  donor gate families suspend a running graph against a checkpointer and are
  resumed by a separate call, possibly days later. That needs a LangGraph
  runtime this stage refuses on purpose. What is ported is what works without
  it: validate, raise, and the malformed-resume handling — which is where the
  defect above lives.
- **`guideline_auto_approve_gates`.** The donor's settings flag that skips
  gates in batch runs. Shipping a documented switch for turning the lesson off
  would be an odd thing for this stage to do.
- **The Strands `@tool` decorator and real tool registration.** `02` uses plain
  functions. This stage shows what a guard does, not what a framework does.
- **The real clinical calculators, the real domain vocabulary, and the real
  food-domain filters.** `DOMAIN_TERMS` is nine lines, `tram_flap_selection_tool`
  is a three-line risk count, and `is_nonveg_text` is a word list — all written
  for the notebooks. The genuine versions are domain content maintained by
  people with domain training, not guardrail machinery.
- **Production logging.** Every donor logs rejections to a real pipeline;
  notebook-local lists stand in so cells can assert on what was blocked.
- **A semantic scope check.** An embedding or small-classifier gate would fix
  `01`'s false rejections (Step 11: two spellings of the same question, one
  hyphen apart, get opposite verdicts) — and would cost a model call per
  request, which is the thing `01` exists to avoid. The honest arrangement is
  both, in order: free string check, then cheap model check, then the
  expensive model.

## Not in scope

- **Output filtering / PII redaction on the way out.** Real, and a different
  shape: it inspects something already produced, which puts it on `05-gate`'s
  side of the boundary above, not this one.
- **Jailbreak and prompt-injection detection as a discipline.** `01` catches a
  few literal override phrases with a regex and says plainly that a fixed
  pattern list cannot enumerate an adversary. Doing it properly is a research
  area, not a port.
- **Rate limiting and spend ceilings.** Already built —
  `01-tools/04-retrieve/07-rate-limiting.ipynb` caps rate, `nbio.cost_meter`
  caps spend. `01` here uses the meter rather than reimplementing it.
- **Fixing `terrier-ta`'s fail-open gate.** Deliberately left open. See above.
