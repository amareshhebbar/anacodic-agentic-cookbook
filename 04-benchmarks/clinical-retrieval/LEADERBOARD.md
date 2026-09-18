# Clinical-retrieval leaderboard

**Current best: flaky.** The most recent configuration retrieves real papers
on most runs of the same question, and nothing on some of them, with no
identified cause yet for the difference. See `README.md` for what that means
and why this benchmark ships with it unfixed.

## Runs

| run | date | config | papers retrieved | faithfulness | note |
|---|---|---|---|---|---|
| baseline | 2026-06-08 | model no longer default (`claude-3-5-sonnet-20241022-v2:0`) | 3/20 rows filled (B01, W01 only) | not recorded | **superseded** — see snapshot below |
| six-run check, question B01 | 2026-09 | `burn-corpus-v3` (see task 1 for the other index names still in play) | **5/6 retrieved papers** (3, 4, 4, 5, 3), **1/6 retrieved 0** | not recorded | same question, same config, six runs — one came back empty with no citation and no runtime error |

Nothing here has a passing faithfulness number yet — that needs DeepEval run
against a real answer, which needs the one-in-six gap closed first so a
faithfulness score isn't averaging in the empty-retrieval case.

### Superseded: the 2026-06-08 snapshot

Copied as history, dated 2026-06-08 against `claude-3-5-sonnet-20241022-v2:0`
— a model the project no longer defaults to. Three of 20 retrieval rows are filled; the pass-rate line
was left as `_/20 (_%)` in the original; the answer-quality and
citation-validity tables were never filled in at all. **Do not read this as a
current number.** It predates the zero-retrieval failure below and was never
finished.

| ID | Query (truncated) | Keywords found | RCS >=5 | Evidence level |
|----|-------------------|----------------|--------|----------------|
| B01 | Timing for skin grafting... | Y | Y | Y |
| B02 | Parkland formula for fluid... | | | |
| W01 | NPWT for diabetic foot... | Y | Y | Y |
| W02 | NPUAP pressure injury staging... | | | |
| BR01 | DIEP flap versus TRAM flap... | | | |
| BR02 | Capsular contracture after... | | | |
| H01 | Flexor tendon repair zone II... | | | |
| H02 | Dupuytren's contracture... | | | |
| C01 | Cleft palate repair timing... | | | |
| C02 | Distraction osteogenesis Pierre Robin... | | | |
| O01 | Sentinel lymph node biopsy melanoma... | | | |
| O02 | Mohs micrographic surgery BCC... | | | |
| N01 | Sunderland classification... | | | |
| N02 | Nerve transfer versus graft... | | | |
| T01 | ADM in breast reconstruction... | | | |
| T02 | PRP for wound healing... | | | |
| M01 | Free flap failure rates... | | | |
| M02 | Smoking on free flap outcomes... | | | |
| M03 | Lymphedema surgical management... | | | |
| M04 | Perforator flap selection... | | | |

Pass rate: _/20 (_%) — left unfinished in the original, reproduced as-is.

### 2026-09: six runs, one question, one still empty

A later check ran the same question (B01, skin-grafting timing) six times
against `burn-corpus-v3`, a newer index than the ones the zero-retrieval
runs above used. Five of six retrieved real papers — three, four, four,
five, and three respectively. The sixth retrieved zero papers and produced a
confident clinical answer anyway, with no citation and no runtime error —
the same failure shape as before, just no longer the outcome every time.

This is the state the benchmark ships with. Nobody has explained the
one-in-six gap, and closing it is explicitly out of scope for this cookbook
stage — it is the first thing a contributor gets to work on instead.

## The three open tasks — how to add the next row

Each is independent, each is scoped to be doable without owning the whole
retrieval pipeline, and each is a `good first issue`.

### Task 1 — Name the cause of the one-in-six empty result

Six runs, same question, same configuration, same index (`burn-corpus-v3`):
five retrieved papers, one retrieved zero. That rules out the simplest
explanations — a wrong index name, a missing key, a dimension mismatch would
all fail every time, not five-sixths of the time. Something intermittent is
in play: a timeout, a transient upstream error swallowed rather than raised,
a race in how the query reaches the index, or a retry path that gives up
silently on one attempt in six.

Two earlier, older indexes are still referenced in config and worth ruling
out as a separate confound: `index-v2` and `burn-corpus-v1` both appear in
older run artifacts alongside `burn-corpus-v2`, and it is not yet confirmed
that the six-run check above used only `burn-corpus-v3` throughout.

**Deliverable (DoD):** one sentence naming the cause, and the run id (of the
six) that demonstrates it. Plausible causes to check first: a transient
upstream timeout or error caught and swallowed rather than raised, a retry
policy that gives up after one failed attempt, or a race between the query
embedding and index readiness on a subset of calls.

### Task 2 — Report how many chunks each index holds

One line per index — `index-v2`, `breast-guidelines`, `burn-corpus-v1`,
`burn-corpus-v2`, `burn-corpus-v3` — giving its vector count, or stating
plainly that the index does not exist.

**Deliverable (DoD):** counts only. This is a read-only inventory task, not a
re-index — do not populate or modify any index to produce this number.

### Task 3 — Run one question end to end and report every break

Pick one question from `questions.py`, wire up a real retrieval + generation
backend (see `eval.py`'s `EVAL_RETRIEVAL_BACKEND` / `EVAL_GENERATION_BACKEND`
hooks), and run it.

**Deliverable (DoD):** every setup problem hit along the way, each with its
fix. Two are already known and documented in the stage README so you don't
lose a day to them — see
`01-modules/01-tools/06-bench/README.md` for the domain-routing test defect and the
Groq/Cloudflare User-Agent rejection. Report whatever else you hit that isn't
already listed there.

## How a new row gets added

Run `python eval.py` (optionally with `EVAL_RETRIEVAL_BACKEND` /
`EVAL_GENERATION_BACKEND` pointed at a real implementation, and `--deepeval`
if you have a judge model key configured), then open a PR that appends a row
to the **Runs** table above with the date, the config, `papers retrieved`,
and `faithfulness` if DeepEval ran. Include the raw `eval.py --json` output
or link to it — a row with no evidence behind it is exactly the failure this
benchmark exists to catch.
