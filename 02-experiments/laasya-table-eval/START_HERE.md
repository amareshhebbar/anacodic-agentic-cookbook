# Start here

Read this once, top to bottom. It covers the project, the setup, and the tasks.

---

## 1. What the project is about

Some answers exist only inside a **table**. A paper may never state a number in
its text, but a table shows it:

```
  | Group                     | Donors | Rate   |
  | Female fertility unknown  |   27   | 14.5%  |   <- the answer is this cell
```

The project measures how well an AI answers questions like *"How many donors
were in the fertility-unknown group?"* when the answer is only in a table.

Questions fall into two families, and they are different problems:

```
  LOOKUP   "How many donors?"             -> find the cell
  COMPUTE  "What percentage is that?"     -> find cells, then calculate
```

Results are always reported split this way, never blended.

We built an agent that can call tools - a calculator, and code that queries the
table as a dataframe - instead of computing internally. The open question is
whether those tools improve accuracy.

## 2. Scope of this folder

This folder is the **evaluation** half of the project. The agent itself lives in
`../rashan-table-agent/`. The work here is to run the experiment, analyse the
results, and write up what they show.

## 3. Setting up (about 10 minutes)

```bash
# 1. On GitHub, fork anacodicAI-labs/anacodic-agentic-cookbook
git clone https://github.com/<your-username>/anacodic-agentic-cookbook.git
cd anacodic-agentic-cookbook
git remote add upstream https://github.com/anacodicAI-labs/anacodic-agentic-cookbook.git

# 2. Work on your own branch
git checkout -b laasya/table-eval
```

Put an API key in a file named `.env` at the repository root:

```
OPENAI_API_KEY=sk-...
```

`.env` is gitignored. Never commit a key and never paste one into a message.
Set a spending limit on the account (Settings > Limits). The code also stops at
`BUDGET_USD`, which defaults to $2.

To submit work:

```bash
git add 02-experiments/laasya-table-eval/
git commit -m "describe the change"
git push -u origin laasya/table-eval
# then open a pull request into anacodicAI-labs:main
```

## 4. Background reading (~45 min, no key required)

Outputs are saved in these notebooks, so they can be read without running.

```
../rashan-table-agent/01_the_data.ipynb    the task, and the two question families
../rashan-table-agent/04_the_agent.ipynb   what the agent does and which tools it calls
```

## 5. The tasks

```
 1. RUN             baseline vs cot vs agent on 50 Biology questions
 2. ANALYSE         accuracy per configuration, split Lookup vs Compute,
                    reported as mean +/- spread, plus the bar figure
 3. ERROR ANALYSIS  sort the wrong answers into label_wrong / wrong_cell /
                    math_error / format_only / unanswerable
 4. TRANSFER        the same comparison on CompSci, to show the result is not
                    specific to biology
 5. WRITE           the Results section and the evaluation half of Methods
```

Steps 1-3 correspond to the three notebooks in this folder. Step 4 is step 1
with `--domain CompSci`.

| # | Notebook | Produces |
|---|---|---|
| 01 | `01_run_the_experiment.ipynb` | `results/*.csv` from the real run |
| 02 | `02_analyse_results.ipynb` | accuracy tables and the figure |
| 03 | `03_error_analysis.ipynb` | the failure categories |

A standalone script, `analyze_results.py`, performs the same analysis as
notebook 02 from the command line:

```bash
python 02-experiments/laasya-table-eval/analyze_results.py
```

If it reports no CSVs found, place result files in `results-input/` first; a
sample file is already provided.

## 6. The commands

Run these from `../rashan-table-agent/`:

```bash
# Task 1 - main run (Biology)
BUDGET_USD=2 python run_eval.py --configs baseline,cot,agent \
    --limit 50 --repeats 3 --sample-seed 7 --grounded-only \
    2>&1 | tee results/run_biology.log

# Task 4 - transfer arm (CompSci)
BUDGET_USD=2 python run_eval.py --domain CompSci --configs baseline,agent \
    --limit 50 --repeats 3 --sample-seed 7 --grounded-only \
    2>&1 | tee results/run_compsci.log
```

Why these flags:

```
 --repeats 3      a spread is the variation between runs; one run cannot
                  produce the mean +/- spread that step 2 asks for
 --sample-seed 7  file order groups questions by source table, so the first 50
                  can come from a single table and misrepresent the benchmark
 --grounded-only  keeps items whose gold answer is present in the table
 tee              keeps a log that can be attached to a bug report
```

Both runs together cost well under $1 on `gpt-4o-mini`.

## 7. Where to run what

```
 JUPYTER    a small smoke test (2-5 questions) to confirm the key works, and
            all the analysis (notebooks 02 and 03).
 TERMINAL   the full run. It streams progress, survives, and is easy to
            restart. A notebook buffers subprocess output, and a kernel
            restart loses the run.
```

## 8. Notes

```
 · run_eval.py OVERWRITES results/*.csv - copy them aside or commit before
   re-running, or the previous run is lost
 · notebooks conflict badly in git; commit one only when the change is intended
 · record every run in results/RUN_LOG.md: date, the exact command, the model,
   N questions, repeats, total spend, and anything that went wrong
 · if a run stops early that is the budget ceiling working as intended. It
   saves what finished and prints where it stopped.
```

## 9. Reporting results

```
 · report Lookup and Compute separately
 · report the mean and the spread across repeats
 · do not claim a difference smaller than the run-to-run spread
 · if no configuration improved accuracy, state that
```

A negative result is reported as found. It is useful to anyone deciding where
to invest effort.

## 10. The one rule

> Only edit files inside `02-experiments/laasya-table-eval/`.

That boundary is what allows several people to work in the same repository
without conflicts. Nothing inside this folder can break the wider project, and
nothing is final until a pull request is reviewed.

Ask a maintainer if anything is unclear. Record ambiguous cases rather than
guessing; they are findings in their own right.
