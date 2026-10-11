# Your task: audit 60 table questions

**Time:** roughly 2-3 hours. **You need:** no coding, no API key. Just careful reading.

## Why this matters

We are testing whether an AI agent can answer questions whose answers live in a
table. Before we can trust ANY accuracy number, we must know two things that only
a human can judge:

1. **Is the "correct answer" actually findable in the table we were given?**
   We already found one case where the benchmark says the answer is 48, but the
   table only supports 46. If that is common, then accuracy scores are partly
   measuring bad labels instead of a bad model — and the whole study has to
   account for it. **This check is the validity backbone of the paper.**
2. **When the model got it wrong, why?** Knowing *how* it fails is the paper's
   diagnostic contribution.

## How to do it

1. Open `items.md`. It has 60 blocks, `item_001` ... `item_060`. Each block shows:
   the question, the gold ("correct") answer, the table, and what each model answered.
2. Open `audit_sheet.csv` (Excel / Google Sheets / any editor). One row per item.
3. For each item, read the table and fill in three columns. Do not change the
   `item_id`, `question_short` or `gold` columns.

## The three columns

### `gold_in_table__yes_no_partial`
Can you find the gold answer in the table, or work it out from the table?
- `yes` — it is there, or it follows directly from the numbers in the table.
- `partial` — close but not exact (e.g. gold says `3.5 years`, the table cell
  says `3.5`; or gold rounds differently).
- `no` — you cannot get the gold from this table at all, even doing the maths
  yourself. **These are the important ones.**

### `gold_looks_correct__yes_no_unsure`
Ignoring the model: do YOU think the gold answer is right?
- `yes` — you checked and the gold is correct.
- `no` — you worked it out and got a different answer (write yours in `notes_optional`).
- `unsure` — you cannot tell.

### `why_model_wrong__category`
Only if at least one model was marked WRONG. Pick ONE:
- `label_wrong` — the model was actually right, the gold is wrong.
- `wrong_cell` — the model used the wrong row/column.
- `math_error` — right cells, wrong arithmetic.
- `format_only` — same answer, written differently (`0.0 %` vs `0%`, `48` vs
  `48 nucleotides`). The meaning matches.
- `unanswerable` — the table genuinely does not contain the answer.
- `other` — anything else; explain in `notes_optional`.
- leave blank if all models were correct.

## A worked example (real, from our data)

> **Question:** total length of the forward + reverse primers for Promoter & Exon 1
> **Gold:** `48 nucleotides`
> **Table:** forward `GAAACCTAATAAAGCTCCACCTTC` (24 characters),
> reverse `TTGCTCAGCATATATCTGGGGC` (22 characters)
> **Model answered:** `46`

Count the letters: 24 + 22 = 46. The model is right; the gold of 48 cannot come
from this table. So you would write:

| gold_in_table | gold_looks_correct | why_model_wrong | notes |
|---|---|---|---|
| `no` | `no` | `label_wrong` | table gives 24+22=46, gold says 48 |

## Rules

- **Judge the table in front of you**, not what you think the original paper said.
- If an item takes more than ~5 minutes, mark `unsure` and move on. Note it.
- It is completely fine — and useful — if many items come out `yes`/`yes`. A clean
  result is as valuable as a messy one. Do not try to find problems.
- Do not edit anything outside the `laasya-table-eval/` folder.

## When you finish

1. Save `audit_sheet.csv`.
2. Write 5-8 sentences in `../results/NOTES.md`: how many were `no`, what the most
   common failure category was, and anything that surprised you.
3. Commit and open a Pull Request (see `../SETUP_FIRST.md`).

Ask a maintainer if anything is ambiguous. Record ambiguous cases; they are
findings in their own right.
