# Contributing to the Anacodic Agentic Cookbook

Thank you for your interest in contributing. Whether it's a bug report, a new
experiment, a documentation fix, or a new use case, we value contributions
from the community.

Please read through this document before opening an issue or a pull request.

## Ways to contribute

1. **Add an experiment** under `02-experiments/` — the one door in for new
   work. Try anything: a new approach to a stage, an alternative to something
   in `01-modules/`, or an attempt at a benchmark number. Not required to win
   — see "the promotion path" below for what happens next. New notebooks here
   follow
   [`02-experiments/NOTEBOOK_STANDARD.md`](02-experiments/NOTEBOOK_STANDARD.md)
   — read it before you open a blank notebook.
2. **Add a use case** under `03-use-cases/` — a finished, demoable application
   of the stages.
3. **Fix bugs, improve documentation, or clarify a README.**

No contribution is too small.

## How work is organized

```
01-modules/        maintained by the lab. read these, don't edit them in your
                   first PR — see "the promotion path" below.
  01-tools/          how the agent DOES things. six sub-stages that together
                     build one retrieval tool, plus 07-as-a-tool.
  02-memory/         what it carries forward, short-term and long-term.
  03-guardrails/     what it may never do.
  04-orchestrate/    what happens next — the decision loop.
  05-observe/        what actually happened — cost, artifacts, tracing.
02-experiments/    your attempts. one folder per contribution:
                     02-experiments/<your-name>-<topic>/
03-use-cases/      finished, demoable applications. same rule: one folder.
04-benchmarks/     frozen inputs, hand-checked gold answers, and a
                   LEADERBOARD.md per benchmark.
```

Two people are never asked to edit the same file. Add a new folder for your
work; do not modify someone else's.

### Which part to take

Each of the five parts under `01-modules/` is owned by one person at a time —
that's the unit of work here, not a file and not a whole repo. You need to
understand your part, not all of them.

| Part | Read first | Depends on |
|---|---|---|
| `01-tools` | `01-tools/04-retrieve/` | nothing — but it's the largest |
| `02-memory` | `01-tools/03-embed/` | nothing. Good standalone start. |
| `03-guardrails` | `01-tools/05-gate/` | nothing. Correctness matters more than volume here. |
| `04-orchestrate` | `01-tools/04-retrieve/08-backend-cascade.ipynb`, `01-tools/05-gate/` | `01-tools/07-as-a-tool` |
| `05-observe` | `nbio.py` | nothing. Self-contained; a good first part. |

`02-memory`, `03-guardrails` and `05-observe` have no dependency on unfinished
work and can be picked up immediately.

## Where a contribution can go next

A folder in `02-experiments/` is the start, not the end. Depending on what it
does, it can lead to up to three places — and it can lead to more than one of
them at once:

- **A leaderboard row in `04-benchmarks/*/LEADERBOARD.md`**, if it beats or
  measures a benchmark number. This is self-serve: run the benchmark's
  `eval.py`, open a PR appending your row with the evidence behind it (see
  the benchmark's own README) — no promotion or lab review needed to report a
  real result.
- **Hand-checked gold answers in `04-benchmarks/*/gold/`**, if you can supply
  them. This needs real domain judgment (a benchmark's `gold/README.md`
  states what kind) and is treated as its own contribution, not a step
  toward one of the other two.
- **Promotion into `01-modules/` or `03-use-cases/`**, decided by the lab, not
  self-serve. `01-modules/` is not closed to new work — it is a destination:
  if something in `02-experiments/` is a better reference way to do a stage,
  the lab promotes it into the relevant `01-modules/` notebook, crediting the
  original folder and its author in the commit and in `CONTRIBUTORS.md`. A
  finished, demoable application is promoted into `03-use-cases/` instead.
  Either way, open a PR against `02-experiments/` first — `01-modules/` and
  `03-use-cases/` change only as promotions, reviewed with extra care because
  every stage folder is read by newcomers as the reference implementation.

## Fork and pull request workflow

We use a fork workflow for everyone, including lab members — the repo is
public, and one path is one less thing to explain.

1. **Fork** the repository.
2. **Branch** from `main` on your fork: `<your-name>/<topic>`, e.g.
   `your-name/handwriting-ocr`.
3. **Make your changes**, inside your own folder under `02-experiments/` or
   `03-use-cases/`.
4. **Run `nbstripout`** before committing (installed via `pre-commit`, see
   below) so notebook outputs — which can carry a stray key or an identifier
   printed during debugging — never reach the diff.
5. **Commit** with clear, informative messages.
6. **Stay up to date** with `main` before opening a pull request.
7. **Push to your fork and open a pull request.** Describe what you tried and
   what the benchmark showed, if applicable.

Install the commit hooks once, locally:

```bash
pip install pre-commit nbstripout
pre-commit install
```

## What must never be in a pull request

- A `.env` file, or any real API key, in code or in a notebook's output cells.
- Any dataset containing patient data, real student work, or another
  identifiable person's information.
- Files over 5 MB. The pre-commit hook rejects these; if your contribution
  genuinely needs a larger asset, open an issue first so we can discuss where
  it belongs.

## Credit

Decided and written down before anyone joins, not negotiated at submission:

- **Moved a benchmark number that lands in a paper** → named in that paper's
  Methods section, and co-authorship on it.
- **Maintained a stage** (had work promoted into `01-modules/`, or actively
  reviews contributions in an area) → maintainer credit in `CONTRIBUTORS.md`,
  permanent.
- **All contributed work stays public and attributable** to you, regardless of
  what happens to any product built on top of it.

## Reporting issues

Found a problem or have a suggestion? Open a GitHub issue with as much detail
as you can — a reproducible example, what you expected, and what happened
instead.

## Code of Conduct

This project has adopted the Contributor Covenant. See `CODE_OF_CONDUCT.md`.

## Licensing & contributor agreement

You keep the copyright to your contribution and are credited for it. By opening
a pull request, you agree that:

1. Your contribution is licensed to everyone under the **Apache License, Version
   2.0** (see `LICENSE`) — inbound equals outbound.
2. You additionally grant **Anacodic AI Labs** a perpetual, worldwide,
   royalty-free, irrevocable, sublicensable licence to use, adapt, and
   **relicense** your contribution, including in other Anacodic materials such
   as courses and publications, with attribution to you.
3. The contribution is your own original work, you have the right to submit it,
   and it does not knowingly infringe anyone else's rights.

We will ask you to confirm this on your first pull request with a one-line
comment: *"I have read and agree to the CONTRIBUTING terms."*

This is a lightweight contributor agreement so the project can be reused and
relicensed cleanly; it is not legal advice.
