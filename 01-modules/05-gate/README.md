# 05 · Gate

**In → out, in 5 lines:** a query, an answer, and the retrieved context that
answer was supposed to come from go in. A grounding verdict comes out —
`grounded: True/False/None`, a score, and the specific quotes or citations
that don't check out, if any. This is the deterministic layer between
retrieval and evaluation: refuse to trust an answer, or prove it's earned.

Ported from `specialist-rag`'s `services/grounding.py` (305 L) and its test
suite, branch `origin/fix-completion` at commit `130ff868` — **not on
`main`**. This is the highest-priority item in this stage's copy plan: the
cookbook had no abstention or grounding code anywhere before this notebook
existed, while `06-bench` exists specifically to measure faithfulness — the
exact failure this module is built to catch. The measurement stage shipped
before the thing it measures had a fix; this closes that gap.

## Why this is its own stage, not part of retrieve or bench

It checks an *answer* against *retrieved context* — a job that needs both
sides already in hand, which places it after `04-retrieve` and before
`06-bench`. It is not a retrieval mechanism (it doesn't fetch anything) and
it is not a benchmark (it doesn't score a run against gold data) — it's the
gate a real answer has to pass before either of those neighboring stages'
numbers mean anything.

## Notebooks

| Notebook | Needs a key? |
|---|---|
| [`01-grounding-check.ipynb`](01-grounding-check.ipynb) | No for the deterministic pass (fabricated quotes, orphan citations, the bibliographic false-positive guard, abstention) — that's most of this notebook and needs no network access at all. The optional LLM judge layer needs `GROQ_API_KEY` or `OPENAI_API_KEY`; without one, `check_grounding` degrades to the deterministic signal alone and says so, rather than failing. |

## The one rule that matters most

A deterministic fabrication — a quoted span that isn't in the retrieved
context, or a citation that was never retrieved — caps the final score at
`0.5`, regardless of how confident an LLM judge is about the rest of the
answer. A judge can be talked into optimism about prose; it cannot talk its
way out of a quote that provably isn't in the evidence. Step 11 proves this
directly, with no key needed.

## What did not come across

- `EvidenceTable.tsx` / `evidenceParser.ts` — the product's UI rendering of a
  grounding result. Frontend, not machinery.
- The real LLM judge prompt template (`prompt_manager.render(...,
  "grounding_check", ...)`), which is product-specific YAML. The notebook
  uses a minimal inline prompt instead, the same pattern
  `04-retrieve/04-llm-chunk-scoring.ipynb` already uses for its own inline
  `RCS_PROMPT`.

## Not in scope

- Wiring this into a real generation pipeline. This notebook proves the
  check works in isolation; integrating it into an actual answer-writing
  loop is product-side work.
- Choosing a canonical branch for the donor repo. Both `origin/fix-completion`
  and `origin/grounding-and-validation` carry byte-identical copies of
  `grounding.py`; `fix-completion` is cited here because
  `grounding-and-validation` is already an ancestor of it.
