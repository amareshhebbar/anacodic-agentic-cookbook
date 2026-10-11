# Start here, Laasya

Read this once, top to bottom. It explains the project, your role, and exactly
what to do. Then go to `FIRST_TASK.md`.

---

## 1. What the project is about

Some answers only exist inside a **table**. For example, a medical paper might
never say in its text how many patients were in a group, but a table shows it:

```
  | Group                     | Donors | Rate   |
  | Female fertility unknown  |   27   | 14.5%  |   <- the answer is this cell
```

We are testing how well AI can answer questions like
*"How many donors were in the 'fertility unknown' group?"*
when the answer is only in a table.

There are two kinds of question, and they are very different:

```
  LOOKUP   "How many donors?"            -> just FIND the cell          (easy)
  COMPUTE  "What percentage is that?"    -> find cells, then CALCULATE  (hard)
```

We built an **AI agent** that can call tools - a calculator, or code that reads
the table - instead of doing maths in its head. We are measuring whether those
tools actually help.

## 2. What we are trying to find out

Honestly: **we do not know yet, and that is fine.** So far the plain AI and the
tool-using agent score about the same. Before we can trust any of those numbers,
we hit a problem that only a human can solve - and that problem is your job.

## 3. The problem being addressed

The benchmark we use ships a "correct answer" for each question. We found a case
where that correct answer **cannot be obtained from the table we were given**:

```
  Question: total length of the forward + reverse primers for Promoter & Exon 1
  The table gives:  forward = 24 characters,  reverse = 22 characters
                    24 + 22 = 46
  The benchmark says the correct answer is:  48
```

So the AI answered 46 - which is right - and was marked **wrong**.

If that happens often, then every accuracy score we report is partly measuring
**bad labels** instead of a bad AI. That would change how the entire paper
reports its results.

This requires a person to read each table and judge.

## 4. Your tasks, in order

Only task 1 is ready now. The others come later - do not start them yet.

```
  T1  MANUAL AUDIT (now, ~2-3 hours, no coding)
      60 questions. For each: can the "correct answer" actually be obtained
      from the table? And if the AI was wrong, why?
      -> audit/AUDIT_INSTRUCTIONS.md has definitions + a worked example

  T2  SUMMARISE the audit into a small table (~1 hour)

  T3  ACCURACY TABLES + FIGURES from the experiment results (light coding;
      a script that already works is in this folder)

  T4  SECOND-RATER CHECK: Rashan re-does 20% of your items independently, and
      you measure how often you two agree. Reviewers always ask for this.

  T5  WRITE the Methods paragraph describing your audit protocol - in your own
      words, because it is your protocol.
```

## 5. Setting up (about 10 minutes)

```bash
# 1. On GitHub, fork anacodicAI-labs/anacodic-agentic-cookbook  (your own copy)
git clone https://github.com/<your-username>/anacodic-agentic-cookbook.git
cd anacodic-agentic-cookbook

# 2. Make your own branch
git checkout -b laasya/table-eval

# 3. Your folder is:  02-experiments/laasya-table-eval/
```

Each time you finish some work:

```bash
git add 02-experiments/laasya-table-eval/
git commit -m "one line describing what you did"
git push origin laasya/table-eval
# then open a Pull Request on GitHub so Rashan can review it
```

## 6. About the API key

An API key lets code call an AI model, and **calls cost real money**. A key is
in the project's `.env` file at the repo root.

```
  · NEVER commit a key, and never paste one into chat, a notebook, or a file
    that gets committed. `.env` is already gitignored - leave it that way.
  · You do NOT need the key for your audit (T1). It needs no AI calls at all.
  · Do not run large experiments. Those are run separately; spending is capped by the code at a set dollar
    limit.
  · If a key may have been exposed, report it immediately so it can be revoked.
```

## 7. The one rule

> **Only edit files inside `02-experiments/laasya-table-eval/`.**
> Never change anyone else's folder.

That single rule is what lets several people work in the same project without
breaking each other's work. Nothing you do inside your own folder can damage
anything, and nothing becomes final until a Pull Request is reviewed.

## 8. How to ask for help

Ask early and often - that is normal here, not a sign of struggling.

- If an audit item is confusing after ~5 minutes, mark it `unsure`, add a note,
  and move on. **Ambiguous cases are findings, not mistakes.**
- If something is broken, nothing is your fault: say what you ran and paste the
  error.
- If a result looks boring (e.g. everything checks out fine), that is a real and
  publishable result. Do not try to find problems that are not there.

---

Next: open `FIRST_TASK.md`, then `audit/AUDIT_INSTRUCTIONS.md`.
