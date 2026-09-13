"""Shared notebook plumbing for every stage in this repo.

One file, used the same way from 01-extract through 06-bench. It does four
jobs and nothing else:

1. **Bootstrap** — put the repo root on ``sys.path`` and load ``.env``, so a
   notebook two levels down (``01-modules/<stage>/*.ipynb``) can ``import nbio``
   and reach whatever module it needs, regardless of the working directory it
   was launched from.
2. **Real runs** — a notebook reads the same ``runs/<run_id>/`` artifacts a
   pipeline actually wrote, rather than a value restated inline. A number in a
   notebook cell can then never drift from the number the code produced.
3. **Visibility** — ``show_json``, ``lines``, ``table``, ``delta`` and ``io``
   print the actual record, or what a stage changed, computed from the record
   itself rather than hand-described.
4. **Spend ceiling** — ``cost_meter`` measures real cost against a budget and
   raises before a mistake turns into a bill, for the notebooks that call a
   paid model.

No pipeline logic lives here. If a function starts doing the work a stage
notebook should be doing, it has grown past what this file is for.

Usage in a notebook — this exact walk-up must be the first code cell, before
``import nbio``. Jupyter starts a notebook's kernel with its working
directory set to the notebook's own folder (confirmed both for interactive
Jupyter and for headless ``nbconvert``), not the repo root, and not the
directory the server was launched from. A bare ``import nbio`` therefore
fails from any notebook under ``01-modules/<stage>/`` unless the repo root is
already on ``sys.path`` — which ``bootstrap()`` itself cannot arrange, since
it can't run until after the import that needs it has already succeeded::

    import sys
    from pathlib import Path

    _root = Path.cwd().resolve()
    for _ in range(6):
        if (_root / "nbio.py").is_file():
            break
        _root = _root.parent
    else:
        raise RuntimeError("could not locate nbio.py above the current directory")
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

    import nbio
    nbio.bootstrap()
    run = nbio.load_run()             # most recent run, or nbio.load_run("<id>")
    nbio.show_json(run["manifest"])

Kept deliberately minimal: a stage that needs something more specific than
bootstrap/load/show writes it locally in its own notebook rather than
growing this file.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


# ---------------------------------------------------------------- path bootstrap

def _find_repo_root() -> Path:
    """Walk up from CWD until this file is found, so a notebook two levels
    down (01-modules/<stage>/) resolves the same repo root regardless of where
    Jupyter was launched from."""
    root = Path(os.getcwd()).resolve()
    for _ in range(6):
        if (root / "nbio.py").is_file():
            return root
        root = root.parent
    raise RuntimeError("could not locate nbio.py above the current directory")


def bootstrap() -> Path:
    """Put the repo root on sys.path and load .env. Returns the repo root.

    Call this once, in a notebook's first cell.
    """
    root = _find_repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from dotenv import load_dotenv

        load_dotenv(root / ".env", override=False)
    except ImportError:
        pass
    return root


#: setup() is an alias kept for readability in notebooks that treat "point me
#: at this repo" as a distinct step from "and load an environment."
setup = bootstrap


# ---------------------------------------------------------------- environment

#: The keys any stage in this repo might read. A stage notebook that needs a
#: key not listed here should extend this tuple locally, not silently assume
#: the key is present.
KNOWN_KEYS = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "PINECONE_API_KEY",
    "SEMANTIC_SCHOLAR_API_KEY",
    "TAVILY_API_KEY",
)


def show_environment(extra_keys: Iterable[str] = ()) -> dict:
    """Print which keys are loaded — never their values.

    A notebook that silently falls back to an offline path when a key is
    missing is a notebook whose output looks identical whether or not the key
    was ever set. This is the one line that tells a reader which case they are
    actually in.
    """
    info = {k: bool(os.environ.get(k)) for k in (*KNOWN_KEYS, *extra_keys)}
    for k, v in info.items():
        print(f"{k:>28} : {'loaded' if v else 'MISSING — offline/fallback path will run'}")
    return info


# ---------------------------------------------------------------- run artifacts

def runs_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _find_repo_root()) / "runs"


def list_run_ids() -> list[str]:
    """Run ids, OLDEST FIRST.

    Sorted by mtime, not by name — run ids are frequently uuid4 or timestamped
    ad hoc, so lexicographic order has no reliable relationship to recency, and
    picking ``[-1]`` without this sort would return an arbitrary run.
    """
    d = runs_dir()
    if not d.is_dir():
        return []
    dirs = [p for p in d.iterdir() if p.is_dir()]
    return [p.name for p in sorted(dirs, key=lambda p: p.stat().st_mtime)]


def load_run(run_id: str | None = None) -> dict | None:
    """Load a real run artifact bundle; defaults to the most recent run.

    Returns ``{"run_id": ..., "manifest": ..., "papers": ..., "answer": ...}``,
    reading whichever of those three files exist for the run and leaving the
    rest ``None``. A notebook that displays a number should read it from here,
    not restate it, so nothing in the notebook can drift from what the code
    actually produced.
    """
    ids = list_run_ids()
    if not ids:
        return None
    rid = run_id or ids[-1]
    base = runs_dir() / rid
    out: dict[str, Any] = {"run_id": rid}
    for name in ("manifest", "papers", "answer"):
        p = base / f"{name}.json"
        out[name] = json.loads(p.read_text()) if p.exists() else None
    return out


def page(run_id: str, stage: str, page_key: str) -> dict:
    """One record from a real run, for stages (extract, chunk) that write one
    file per page/document rather than one bundle per run."""
    p = runs_dir() / run_id / stage / f"{page_key}.json"
    if not p.is_file():
        raise FileNotFoundError(f"no {stage} record for {page_key} in {run_id}")
    return json.loads(p.read_text())


def pages(run_id: str, stage: str) -> list[dict]:
    d = runs_dir() / run_id / stage
    return [json.loads(p.read_text()) for p in sorted(d.glob("*.json"))] if d.is_dir() else []


# ---------------------------------------------------------------- visibility

def show_json(obj: Any, *, limit: int = 1600, drop: tuple[str, ...] = ()) -> None:
    """Print a record, truncated rather than summarised, minus any fields
    named in `drop` that would bury it (e.g. a raw `regions` blob)."""
    data = {k: v for k, v in obj.items() if k not in drop} if isinstance(obj, dict) else obj
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    print(text if len(text) <= limit else text[:limit] + f"\n… (+{len(text) - limit} chars)")


def lines(rec: dict, n: int = 12, width: int = 76) -> None:
    """Print a page's transcribed lines with their length — the shape that
    most often reveals a table cut mid-row or a line dropped entirely."""
    text = "\n".join(
        ln["text"] for region in rec.get("regions", []) for ln in region.get("lines", [])
    )
    kept = [ln for ln in text.splitlines() if ln.strip()]
    for ln in kept[:n]:
        print(f"  [{len(ln):3d}] {ln[:width]}")
    if len(kept) > n:
        print(f"  … (+{len(kept) - n} more lines)")


def table(rows: list[tuple], headers: tuple) -> None:
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(str(h))
              for i, h in enumerate(headers)]
    print("  " + "  ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    print("  " + "  ".join("-" * w for w in widths))
    for r in rows:
        print("  " + "  ".join(str(c).ljust(w) for c, w in zip(r, widths)))


def counts(records: list[dict], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in records:
        out[str(r.get(field))] = out.get(str(r.get(field)), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def delta(before: Iterable[dict], after: Iterable[dict], label: str = "") -> None:
    """What a stage changed, at the collection level: counts in, counts out,
    and which keys appeared or disappeared across the whole set."""
    before, after = list(before), list(after)
    keys_before = set().union(*[set(d) for d in before]) if before else set()
    keys_after = set().union(*[set(d) for d in after]) if after else set()
    print(f"{label}: {len(before)} in -> {len(after)} out")
    new, gone = sorted(keys_after - keys_before), sorted(keys_before - keys_after)
    if new:
        print(f"  keys ADDED  : {new}")
    if gone:
        print(f"  keys REMOVED: {gone}")


def io(before: dict | None, after: dict, *, title: str = "") -> None:
    """What a single record's stage read, added and changed — computed from
    the record, not hand-written, so it cannot drift from the code."""
    before = before or {}
    added = [k for k in after if k not in before]
    changed = [k for k in after if k in before and before[k] != after[k]]
    if title:
        print(f"── {title} " + "─" * max(0, 58 - len(title)))
    print(f"IN  ▶ {', '.join(sorted(before)) or '(nothing)'}")
    print(f"ADD ▶ {', '.join(added) or '(none)'}")
    print(f"CHG ▶ {', '.join(changed) or '(none)'}")


# ---------------------------------------------------------------- spend ceiling

#: USD per token, ``(input, output)``. Ported from the private product's
#: ``llm_cost_meter.PRICES`` — Groq entries are invoice-derived, OpenAI
#: entries are list prices. Both drift from the provider's actual billed
#: rate over time; check against your own bill before quoting a figure from
#: this table as current.
PRICES: dict[str, tuple[float, float]] = {
    # Groq — invoice-derived
    "llama-3.3-70b-versatile": (0.00000059, 0.00000079),
    "llama-3.1-8b-instant": (0.00000005, 0.00000008),
    "meta-llama/llama-4-scout-17b-16e-instruct": (0.00000011, 0.00000034),
    "openai/gpt-oss-120b": (0.00000015, 0.00000060),
    "openai/gpt-oss-20b": (0.000000075, 0.00000030),
    "qwen/qwen3-32b": (0.00000029, 0.00000059),
    # OpenAI — list prices
    "gpt-4o": (0.00000250, 0.00001000),
    "gpt-4o-mini": (0.00000015, 0.00000060),
    "gpt-4.1": (0.00000200, 0.00000800),
    "gpt-4.1-mini": (0.00000040, 0.00000160),
    "text-embedding-3-large": (0.00000013, 0.0),
    "text-embedding-3-small": (0.00000002, 0.0),
}


class BudgetExceeded(RuntimeError):
    """Raised when a call has carried spend past the ceiling. The run should stop."""


class UnpricedModel(RuntimeError):
    """Raised when a budget is set but a model's rate is unknown, so $ cannot be
    trusted. A silent $0 would make the ceiling unenforceable for exactly the
    model that would need it most — so this is a hard stop, not a fallback."""


def price_for(model_id: str) -> tuple[float, float] | None:
    """The (input, output) rate for a model id, or None if unpriced.

    Falls back to the longest table key contained in the id, so a prefixed
    id (e.g. a region- or version-wrapped model name) still resolves.
    """
    mid = (model_id or "").strip()
    if not mid:
        return None
    if mid in PRICES:
        return PRICES[mid]
    matches = [k for k in PRICES if k in mid]
    return PRICES[max(matches, key=len)] if matches else None


class Meter:
    """Measured spend against an optional ceiling, for one notebook's calls.

    Single-threaded and un-itemized by design — a notebook here makes a
    handful of calls in one kernel, not hundreds across a multi-stage
    pipeline, so the product's thread-safe, per-node version would add
    complexity with nothing for it to do. What's kept is the part that
    matters: measured cost, and a hard stop before it runs away.
    """

    def __init__(self, budget_usd: float | None = None):
        self.budget_usd = budget_usd
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost_usd = 0.0
        self._by_model: dict[str, float] = {}
        self._unpriced: set[str] = set()

    def record(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Add one call's usage, then enforce the ceiling.

        The check runs after the call, so a run stops just after the call
        that crosses the ceiling, not before it — set the budget a little
        under any hard external limit if that distinction matters.
        """
        rate = price_for(model_id)
        if rate is None:
            self._unpriced.add(model_id or "(unknown)")
            if self.budget_usd is not None:
                raise UnpricedModel(
                    f"{model_id!r} has no entry in nbio.PRICES, so its spend "
                    f"cannot be counted against the ${self.budget_usd:.2f} "
                    f"ceiling. Add a rate to nbio.PRICES before using this model "
                    f"under a budget."
                )
            rate = (0.0, 0.0)

        cost = prompt_tokens * rate[0] + completion_tokens * rate[1]
        self.calls += 1
        self.prompt_tokens += int(prompt_tokens or 0)
        self.completion_tokens += int(completion_tokens or 0)
        self.cost_usd += cost
        self._by_model[model_id] = self._by_model.get(model_id, 0.0) + cost

        if self.budget_usd is not None and self.cost_usd >= self.budget_usd:
            raise BudgetExceeded(
                f"stopped at ${self.cost_usd:.4f} of a ${self.budget_usd:.2f} "
                f"ceiling after {self.calls} call(s). Raise the ceiling only if "
                f"the spend so far looks right."
            )

    def record_cost(self, model_id: str, cost_usd: float) -> None:
        """Add one call's usage when only a dollar cost is available, not a
        token count — e.g. DeepEval's ``metric.evaluation_cost`` after
        ``.measure()``, which prices its own judge call internally. Enforces
        the same ceiling as `record()`.
        """
        self.calls += 1
        self.cost_usd += float(cost_usd or 0.0)
        self._by_model[model_id] = self._by_model.get(model_id, 0.0) + float(cost_usd or 0.0)

        if self.budget_usd is not None and self.cost_usd >= self.budget_usd:
            raise BudgetExceeded(
                f"stopped at ${self.cost_usd:.4f} of a ${self.budget_usd:.2f} "
                f"ceiling after {self.calls} call(s). Raise the ceiling only if "
                f"the spend so far looks right."
            )

    def report(self) -> str:
        if not self.calls:
            return "no metered calls made — $0.0000"
        lines = [
            f"{'model':<44}{'cost':>10}",
            "-" * 54,
        ]
        for model, cost in sorted(self._by_model.items(), key=lambda kv: -kv[1]):
            tag = "  (unpriced)" if model in self._unpriced else ""
            lines.append(f"{model[:44]:<44}{'$' + format(cost, '.4f'):>10}{tag}")
        lines.append("-" * 54)
        lines.append(
            f"{'TOTAL':<44}{'$' + format(self.cost_usd, '.4f'):>10}"
            f"   ({self.calls} call(s), {self.prompt_tokens:,} in / "
            f"{self.completion_tokens:,} out tokens)"
        )
        if self.budget_usd is not None:
            lines.append(f"{'ceiling':<44}{'$' + format(self.budget_usd, '.2f'):>10}")
        return "\n".join(lines)


@contextlib.contextmanager
def cost_meter(budget_usd: float | None = 0.50):
    """A spend ceiling around real model calls in a notebook.

    Usage::

        with nbio.cost_meter(budget_usd=0.50) as meter:
            response = call_the_model(...)
            meter.record(model_id, prompt_tokens, completion_tokens)
            # raises BudgetExceeded the moment spend >= budget_usd

        print(meter.report())

    The default ceiling (50 cents) is sized to catch a runaway loop or a
    batch-size mistake, not to ration a normal run — a single page, a single
    embedding batch, or a single scoring pass on the priced models above
    costs a small fraction of it.
    """
    meter = Meter(budget_usd=budget_usd)
    yield meter
