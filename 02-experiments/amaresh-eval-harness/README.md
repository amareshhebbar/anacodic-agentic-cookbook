# amaresh-eval-harness

An eval harness for the clinical-retrieval benchmark: a golden set, a runner
that repeats a run N times, and the numbers that came out.

## Status

| | |
|---|---|
| Owner | Amaresh |
| Part | measurement — scores what the retrieval tools produce |
| Benchmark | `04-benchmarks/clinical-retrieval/` |

## What is here

```
  goldens.json        queries + the clinical terms a correct answer must contain
  01-*.ipynb          the experiments, one per notebook
  results/            one CSV per experiment — raw runs, not summaries
```

## Experiment 1 — model comparison (done)

Two models, identical prompt, **identical retrieval evidence**, scored by
keyword precision against the expected terms.

```
  design   5 queries x 2 models x 3 trials = 30 runs
  models   openai/gpt-oss-120b  ·  qwen3-32b   (both via Groq)
  metric   keyword precision — fraction of expected clinical terms present
  result   both models 0.89-0.93 mean. Effectively tied.
```

**Read this as a generation-quality comparison, not a retrieval study.**
Retrieval evidence was held constant, so nothing here says anything about
whether retrieval repeats.

A null result is still a result: on these five questions, keyword precision
does not separate these two models. That is worth knowing before anyone
spends money on the larger one.

### Configuration, so nothing is compared that should not be

```
  embedding dimension   768
```

Not 3072. This was reduced to fit available hardware. Numbers from this
folder are **not comparable** to any index built at 3072 dimensions — the
vectors live in different spaces and a similarity score from one means
nothing against the other.

## Experiment 2 — retrieval variance (next)

The open question this folder exists for:

```
  six runs of ONE question have returned 4 / 0 / 4 / 5 / 3 / 3 papers
  → so which number goes in the paper?
```

Design: **one query, one model, one configuration, nothing varying but
chance.** Report the spread — minimum, maximum, and how often zero papers
came back — never the mean alone.

On run count: for a failure that occurs about 1 run in 6, the chance of
missing it in 3 runs is `(1 - 0.17)^3 = 0.57`. Seeing it once with 95%
confidence needs `log(0.05) / log(0.83) ~ 16` runs.

```
  runs    chance of missing a 1-in-6 failure entirely
  ----    -------------------------------------------
     3     57%
     8     23%
    16      5%
```

## Reused from the repo — not reimplemented here

| what | where |
|---|---|
| keyword precision | `04-benchmarks/clinical-retrieval/eval.py` |
| the 20 questions and their `required_keywords` | `04-benchmarks/clinical-retrieval/questions.py` |
| pass/fail thresholds | `04-benchmarks/clinical-retrieval/pass_rubric.py` |
| judge abstraction, incl. the judge-shares-model check | `04-benchmarks/clinical-retrieval/judge_model.py` |

Import these rather than copying them. Two scorers in one repo drift apart
and then disagree, and nobody can tell which number was right.

## Reading

- `01-modules/01-tools/06-bench/` — the bench notebooks this scores against
- `04-benchmarks/clinical-retrieval/README.md` — what the benchmark claims
- `02-experiments/NOTEBOOK_STANDARD.md` — read before opening a blank notebook

---

## Verified on the real corpus, 2026-09-20

The notebook was run inside the repo with the real 680-chunk corpus present.
It works, and it demonstrates the topic mismatch with numbers:

```
  corpus : local corpus (chunk_meta.jsonl)   680 chunks

  retrieval is HEALTHY — real papers, plausible scores:
    +0.3736  s12282-018-0908-y.pdf
    +0.3565  The Breast Journal 2019 - Ng - Mastectomy flap necrosis...
    +0.3524  00000637-201506000-00005.pdf

  but scored against the BURNS benchmark:
    id    papers  kw_prec
    B01        3     0.00
    B02        3     0.00
    W01        3     0.00
    W02        3     0.00
```

**Three papers retrieved every time, zero keyword precision every time.** The
retriever is working; the questions are about burns and wounds and the corpus
is about breast reconstruction. Nothing is broken.

This is why `goldens.json` exists and why its queries come from the corpus's
own frozen protocol rather than from `questions.py`. Run `goldens.json`'s five
queries against this corpus and the numbers mean something; run the benchmark's
twenty and they do not.

It is also a small lesson worth keeping: **a healthy-looking retrieval score
and a zero downstream score is a topic mismatch, not a bug.** The two failures
look identical from the outside.
