"""Evaluate table-QA configurations on SciTableQA and score against gold.

Configs:
  baseline  plain single model call (no tools)
  cot       plain call, explicitly prompted to reason step by step (no tools)
  agent     OpenAI Agents SDK agent with calculator + sequence_length tools

Usage:
  python run_eval.py --configs baseline,agent --limit 100 --grounded-only
  python run_eval.py --configs baseline,cot,agent --repeats 3 --temperature 0.4
  BUDGET_USD=2.0 LLM_PROVIDER=groq python run_eval.py ...

Reports overall accuracy and the Lookup/Compute split, as mean +/- spread over N
runs. LABEL AUDIT: only ~80% of Lookup golds and ~50% of Compute golds actually
appear in the provided table, so --grounded-only restricts to verifiable items;
both numbers are reported so the ceiling is explicit. Spend is capped by
BUDGET_USD via nbio.cost_meter.
"""
import argparse
import csv
import os
import statistics
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (HERE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import nbio                                    # noqa: E402
import scitableqa_loader as L                  # noqa: E402
from scorer import is_correct                  # noqa: E402
import agent as base                           # noqa: E402

BUDGET_USD = float(os.environ.get("BUDGET_USD", "2.0"))

COT_SUFFIX = ("\n\nWork through it step by step, then give ONLY the final answer "
              "on the last line.")


def _baseline(q, table, temp):
    return base.answer(q, table, False, temp)


def _cot(q, table, temp):
    out = base.answer(q + COT_SUFFIX, table, False, temp)
    out["config"] = "cot"
    return out


def _agent(q, table, temp):
    import agent_sdk
    return agent_sdk.run_agent(q, table, False, temp)


REGISTRY = {"baseline": _baseline, "cot": _cot, "agent": _agent}


def _write(name, rows, out_dir="results"):
    if not rows:
        return
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{name}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {os.path.join(out_dir, name)}.csv ({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="Biology")
    ap.add_argument("--configs", default="baseline,agent")
    ap.add_argument("--limit", type=int, default=100, help="number of questions")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--out-dir", default="results",
                    help="where to write the result CSVs; point a demo run at a "
                         "scratch directory so it cannot overwrite committed results")
    ap.add_argument("--sample-seed", type=int, default=None,
                    help="randomly sample --limit questions with this seed "
                         "instead of taking the first N in file order")
    ap.add_argument("--grounded-only", action="store_true",
                    help="keep only items whose gold appears in the table")
    args = ap.parse_args()

    trips = L.load_domain(args.domain)
    total_before = len(trips)
    if args.grounded_only:
        trips = [t for t in trips if t.grounded]
    if args.sample_seed is not None:
        # file order groups questions by source table, so the first N can all
        # come from one table and misrepresent the benchmark
        import random
        random.Random(args.sample_seed).shuffle(trips)
    trips = trips[:args.limit]
    fam = Counter(t.task_family for t in trips)
    print(f"{args.domain}: {len(trips)} questions "
          f"(from {total_before}; grounded_only={args.grounded_only}) "
          f"| Lookup {fam['Lookup']} / Compute {fam['Compute']}")

    configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    for c in configs:
        if c not in REGISTRY:
            raise SystemExit(f"unknown config {c!r}; choose from {list(REGISTRY)}")

    acc = {c: [] for c in configs}
    cost_c = {c: 0.0 for c in configs}      # spend attributable to each config
    calls_c = {c: 0 for c in configs}       # model calls per config
    toks_c = {c: [0, 0] for c in configs}   # [input, output] tokens
    famacc = {c: Counter() for c in configs}
    famtot = {c: Counter() for c in configs}
    last_rows = {c: [] for c in configs}
    stopped = False

    print(f"\nceiling ${BUDGET_USD:.2f} | repeats={args.repeats} "
          f"| temp={args.temperature} | configs={configs}\n")
    with nbio.cost_meter(budget_usd=BUDGET_USD) as meter:
        try:
            for r in range(1, args.repeats + 1):
                for cfg in configs:
                    fn, rows, ok = REGISTRY[cfg], [], 0
                    cost0 = meter.cost_usd
                    for i, t in enumerate(trips, 1):
                        out = fn(t.question, t.table_csv, args.temperature)
                        if out.get("prompt_tokens"):
                            meter.record(out["model_id"], out["prompt_tokens"],
                                         out["completion_tokens"])
                            calls_c[cfg] += 1
                            toks_c[cfg][0] += out["prompt_tokens"]
                            toks_c[cfg][1] += out["completion_tokens"]
                        good = int(is_correct(out["final"], t.gold, t.question))
                        ok += good
                        famtot[cfg][t.task_family] += 1
                        famacc[cfg][t.task_family] += good
                        rows.append({"question": t.question, "gold": t.gold,
                                     "pred": out["final"], "correct": good,
                                     "reasoning_type": t.reasoning_type,
                                     "task_family": t.task_family,
                                     "grounded": int(t.grounded),
                                     "tool_calls": out.get("tool_calls", 0),
                                     "model": out["model"], "config": cfg, "run": r})
                        if i % 25 == 0:
                            print(f"    {cfg} run{r}: {i}/{len(trips)} "
                                  f"${meter.cost_usd:.4f}", flush=True)
                    cost_c[cfg] += meter.cost_usd - cost0
                    acc[cfg].append(ok / len(trips))
                    last_rows[cfg] = rows
                    print(f"  run {r} [{cfg}] acc={ok/len(trips):.1%} "
                          f"cost=${meter.cost_usd:.4f}", flush=True)
        except nbio.BudgetExceeded as e:
            stopped = True
            print(f"\n[BUDGET] {e}\n")

    print("\nsaved:")
    for c in configs:
        _write(c, last_rows[c], args.out_dir)
    print("\n=== spend ===")
    print(meter.report())

    print(f"\n=== accuracy (temp={args.temperature}, scorer=normalized, "
          f"grounded_only={args.grounded_only}) ===")
    for c in configs:
        if not acc[c]:
            continue
        m = statistics.mean(acc[c])
        sd = statistics.stdev(acc[c]) if len(acc[c]) > 1 else 0.0
        sp = f" +/- {sd:.1%}" if len(acc[c]) > 1 else ""
        lk = famacc[c]['Lookup'] / famtot[c]['Lookup'] if famtot[c]['Lookup'] else float('nan')
        cp = famacc[c]['Compute'] / famtot[c]['Compute'] if famtot[c]['Compute'] else float('nan')
        print(f"[{c:8s}] overall {m:.1%}{sp}  |  Lookup {lk:.1%}  Compute {cp:.1%}"
              f"   (runs: {', '.join(f'{a:.0%}' for a in acc[c])})")

    print("\n=== cost per configuration (what the agentic overhead buys) ===")
    print(f"  {'config':12s} {'acc':>7s} {'$ total':>9s} {'calls':>7s} "
          f"{'calls/q':>8s} {'$/question':>11s} {'acc per $':>10s}")
    for c in configs:
        if not acc[c]:
            continue
        a = statistics.mean(acc[c])
        n = len(trips) * max(1, len(acc[c]))
        cpq = cost_c[c] / n if n else 0.0
        print(f"  {c:12s} {a:6.1%} {cost_c[c]:9.4f} {calls_c[c]:7d} "
              f"{calls_c[c]/n:8.2f} {cpq:11.5f} "
              f"{(a/cost_c[c] if cost_c[c] else float('nan')):10.1f}")

    if len(configs) >= 2 and all(acc[c] for c in configs):
        b = statistics.mean(acc[configs[0]])
        for c in configs[1:]:
            print(f"\nDELTA {c} - {configs[0]} = {statistics.mean(acc[c]) - b:+.1%}")
    if stopped:
        print("\nNOTE: stopped at budget ceiling — PARTIAL results.")


if __name__ == "__main__":
    main()
