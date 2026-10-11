"""Analyze table-QA result CSVs: accuracy by reasoning type + ablation delta + a figure.

Reads every *.csv in results-input/ (columns: question, gold, pred, correct,
reasoning_type, model, config). Prints per-config accuracy and, if both a
'naive' and a 'table_aware' config are present, the ablation delta. Saves a bar
chart to results/accuracy_by_type.png. No model calls — pure analysis of outputs.
"""
import glob
import os

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "results-input")
OUT = os.path.join(HERE, "results")


def load() -> pd.DataFrame:
    files = glob.glob(os.path.join(IN, "*.csv"))
    if not files:
        raise SystemExit(
            f"no CSVs found in {IN}. Put a result file there first "
            f"(a sample file is provided — see START_HERE.md)."
        )
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    df = load()
    configs = sorted(df["config"].unique())
    print(f"loaded {len(df)} rows across configs: {configs}\n")

    for cfg in configs:
        d = df[df["config"] == cfg]
        acc = d["correct"].mean()
        print(f"[{cfg}] overall accuracy = {d['correct'].sum()}/{len(d)} = {acc:.1%}")
        by = d.groupby("reasoning_type")["correct"].agg(["sum", "count"])
        for rt, row in by.iterrows():
            print(f"    {rt:28s} {int(row['sum'])}/{int(row['count'])}")
        print()

    # ablation delta if both configs present
    if "naive" in configs and "table_aware" in configs:
        print("=== ABLATION: naive -> table_aware (accuracy by reasoning type) ===")
        piv = df[df.config.isin(["naive", "table_aware"])].pivot_table(
            index="reasoning_type", columns="config", values="correct", aggfunc="mean")
        print((piv * 100).round(1))

    # figure: accuracy by reasoning type, one bar group per config
    piv = df.pivot_table(index="reasoning_type", columns="config",
                         values="correct", aggfunc="mean")
    ax = piv.plot(kind="bar", figsize=(10, 5))
    ax.set_ylabel("accuracy"); ax.set_ylim(0, 1)
    ax.set_title("Accuracy by reasoning type")
    plt.tight_layout()
    fig_path = os.path.join(OUT, "accuracy_by_type.png")
    plt.savefig(fig_path, dpi=120)
    print(f"\nsaved figure -> {fig_path}")


if __name__ == "__main__":
    main()
