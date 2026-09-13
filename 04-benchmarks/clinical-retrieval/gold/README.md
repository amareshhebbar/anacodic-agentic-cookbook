# Gold context — TODO, intentionally empty

**Status: empty.** This folder holds no gold answers yet. That is deliberate,
not an oversight — read why below before adding anything here.

## Why this can't be copied, generated, or delegated

Gold context is a hand-checked set of *correct passages* for each of the 20
questions in `../questions.py`, and only someone who can tell a correct
clinical answer from a plausible-sounding wrong one can produce it. Inventing
a passage that merely looks right would be worse than having nothing — it
would let this benchmark quietly certify a wrong answer as correct, in a
benchmark whose whole point is catching that failure mode. So no gold
content is fabricated here, by a model or otherwise.

## What it's for

Scored against retrieved context alone, a low faithfulness score is
ambiguous — it could mean retrieval failed (no relevant passage was ever
found) or generation failed (a relevant passage was found and the model still
didn't use it). A reviewer asking which one happened gets a guess.

Scored against **both** arms — retrieved context and gold context — the
answer is in the table: if the answer looks bad against retrieved context but
good against gold context, retrieval is the problem; if it looks bad against
both, generation is the problem. See `01-modules/06-bench/03-gold-context-arm.ipynb`
for the comparison pattern (demonstrated there on a synthetic example, since
there's no real gold data yet).

It does not need to be complete to be useful. Five questions with gold context
(out of 20) is enough to make the comparison arm meaningful and prove the
harness works end to end.

## Format, once populated

One directory per question id, matching `questions.py`:

```
gold/
  B01/
    passages.json
  B02/
    passages.json
  ...
```

`passages.json`:

```json
{
  "question_id": "B01",
  "passages": [
    {
      "text": "the exact passage text a retrieval system should be able to find",
      "source": "citation or DOI/PMCID this passage came from",
      "verified_by": "name or handle of the domain expert who checked this",
      "verified_at": "2026-09-11",
      "notes": "optional — why this passage answers the question"
    }
  ]
}
```

`passages` is a list because more than one passage may support an answer.
`verified_by` must name a real person who checked the passage against the
source — not a model, and not "TBD".

## How to contribute one

1. Pick a question id from `questions.py` you have real domain knowledge of.
2. Find (or supply) the source passage that actually answers it — an
   open-access paper, a guideline, a textbook passage you can cite.
3. Write `gold/<question_id>/passages.json` in the format above.
4. Open a PR. See the repo's `CONTRIBUTING.md` — this is exactly the kind of
   contribution that gets a permanent credit, because it's the one thing here
   that can't be automated.

Until this folder has entries, `eval.py` and
`01-modules/06-bench/03-gold-context-arm.ipynb` report the gold-context arm as
skipped rather than guessing.
