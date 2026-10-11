# laasya-table-eval — Evaluation & failure analysis for the table-QA agent

**Scope:** evaluation and analysis
**Status:** scaffolded 2026-10-02.

## What this folder is

This is the **evaluation half** of the table-QA agent paper. The agent itself is
built in `../rashan-table-agent/`. Your job here is to take the agent's answers
and turn them into the paper's **results**:

1. **Accuracy by reasoning type** — how often the agent is right, split by
   question type (Cell Selection, Arithmetic, Counting, ...).
2. **Ablation delta** — naive-text vs table-aware: how much the table tool helps.
3. **Failure analysis** — of the wrong answers, where did it go wrong.

You do all of this by reading CSV files (the agent's outputs) and computing
numbers + a figure from them. You do **not** need to run the model yourself.

## The one rule

> **Only ever edit files inside THIS folder (`laasya-table-eval/`).**
> Never change anything in `rashan-table-agent/` or elsewhere.

That rule is what lets several people work in the same repo without breaking
each other's work.

## What's in here

| file / folder | what it is |
|---|---|

| `START_HERE.md` | the project, the setup and the tasks - read this first |
| `analyze_results.py` | reads result CSVs and prints accuracy + makes a figure |
| `results-input/` | result CSVs produced by the agent runs |
| `results/` | your outputs land here (tables, figures) |

Written to [NOTEBOOK_STANDARD.md](../NOTEBOOK_STANDARD.md) when you add notebooks:
one action per cell, look at the output before the next step.

## Notebooks — read these in order

| # | Notebook | What you do | Needs a key |
|---|---|---|---|
| 01 | `01_run_the_experiment.ipynb` | how to run the matrix, and what to record | yes |
| 02 | `02_analyse_results.ipynb` | accuracy by family, spread, the figure | no |
| 03 | `03_error_analysis.ipynb` | why the wrong answers were wrong | no |

For background on the data and the agent, read
`../rashan-table-agent/01_the_data.ipynb` and `04_the_agent.ipynb` first.
