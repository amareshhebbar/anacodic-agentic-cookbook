# Your first task

**Task:** run the experiment, then analyse it. **Time:** a couple of hours,
most of it waiting while the run executes.
**You need:** an OpenAI key in a `.env` file at the repo root.

## Read these first (~45 min, no key needed)

The outputs are saved, so you can read them without running anything.

```
../rashan-table-agent/01_the_data.ipynb    what the task is, and the two kinds of question
../rashan-table-agent/04_the_agent.ipynb   what the agent actually does
```

## Then work through your own notebooks, in order

| # | Notebook | What you produce |
|---|---|---|
| 01 | `01_run_the_experiment.ipynb` | `results/*.csv` from the real run |
| 02 | `02_analyse_results.ipynb` | accuracy tables + the figure |
| 03 | `03_error_analysis.ipynb` | why the wrong answers were wrong |

## The five tasks

```
 1. RUN             baseline vs cot vs agent on 50 Biology questions
 2. ANALYSE         accuracy per setting, split Lookup vs Compute,
                    reported as mean +/- spread, plus the bar figure
 3. ERROR ANALYSIS  sort the wrong answers into label_wrong / wrong_cell /
                    math_error / format_only / unanswerable  (human judgement)
 4. TRANSFER        the same comparison on CompSci, to show it is not
                    biology-only
 5. WRITE           the Results section and the evaluation half of Methods
```

Steps 1-3 map onto your three notebooks. Step 4 is step 1 again with
`--domain CompSci`. Step 5 is writing.

## Where to run what

```
 JUPYTER    good for a small smoke test (2-5 questions) to confirm your key
            works, and for all the analysis (notebooks 02 and 03).
 TERMINAL   better for the full run. It streams progress, survives, and is
            easy to restart. A notebook buffers subprocess output, so you
            would stare at a blank cell, and a kernel restart loses the run.
```

## What "done" looks like

```
 · results/*.csv committed for all three settings, three repeats each
 · an accuracy table split by Lookup and Compute, with spreads
 · one figure: accuracy by question type
 · the error-category counts from step 3
 · the CompSci comparison from step 4
 · a Results section draft
```

## The one rule

> Only edit files inside `laasya-table-eval/`. Never change anyone else's folder.

Ask a maintainer if anything is unclear. Record ambiguous cases rather than
guessing; they are findings in their own right.
