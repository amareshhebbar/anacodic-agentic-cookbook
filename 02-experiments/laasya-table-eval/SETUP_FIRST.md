# Do this once, before anything else

You need your own copy of the cookbook on GitHub, then this folder opens inside it.

## One-time setup (~10 min)

```bash
# 1. On github.com, open anacodicAI-labs/anacodic-agentic-cookbook and click "Fork".
#    That makes YOUR OWN copy at github.com/<your-username>/anacodic-agentic-cookbook

# 2. Download your copy to your computer:
git clone https://github.com/<your-username>/anacodic-agentic-cookbook.git
cd anacodic-agentic-cookbook

# 3. Make a branch to work on (keeps your work tidy and separate):
git checkout -b laasya/table-eval
```

## Each time you work

```bash
cd anacodic-agentic-cookbook
# edit files only inside 02-experiments/laasya-table-eval/
git add 02-experiments/laasya-table-eval/
git commit -m "describe what you did in one line"
git push origin laasya/table-eval
# then on GitHub, open a Pull Request so Rashan can review + merge
```

## Running the analysis script

```bash
# from the repo root:
python 02-experiments/laasya-table-eval/analyze_results.py
```
If it says "no CSVs found", you just need to put result files in `results-input/`
first — see `FIRST_TASK.md`. A real sample file is already there so you can try
it right now.

## If you get stuck

Nothing here can break the shared project — you only ever touch your own folder,
and nothing is final until a pull request is reviewed. Ask a maintainer if
anything is unclear.
