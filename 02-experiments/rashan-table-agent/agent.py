"""Table-QA agent (Groq-backed) — naive-text vs table-aware configurations.

Two configs form the paper's core ablation:
  - naive      : the raw CSV text is dumped into the prompt (no table tool)
  - table_aware: the CSV is rendered as a clean markdown table (table_tools)

Reasoning step: a single grounded Groq chat call that must answer ONLY from the
table (the plan-act-reflect retry loop from 01-modules/04-orchestrate is layered
on in M2+; M1 is the one-call baseline). Fail loud if GROQ_API_KEY is absent —
no silent offline substitute in an evaluation path.
"""
import os
import re
import time

from table_tools import csv_to_markdown

# Defaults per provider (override via OPENAI_MODEL / GROQ_MODEL in .env).
OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
GROQ_MODEL = os.environ.get("GROQ_MODEL") or "openai/gpt-oss-20b"

SYSTEM = (
    "You answer questions using ONLY the provided table. Reason step by step if "
    "needed, but reply with ONLY the final answer on the last line, as short as "
    "possible (a number with its unit, or the exact cell text). If the table does "
    "not contain the answer, reply exactly: INSUFFICIENT."
)


def _load_env_file():
    """Minimal .env loader so a key added to the cookbook root is picked up."""
    root = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(root):
        for line in open(root):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def build_prompt(question: str, table_csv: str, table_aware: bool) -> str:
    table = csv_to_markdown(table_csv) if table_aware else table_csv.strip()
    kind = "a markdown table" if table_aware else "a raw CSV table"
    return f"Here is {kind}:\n\n{table}\n\nQuestion: {question}\nAnswer:"


def resolve_provider() -> str:
    """Pick the provider. Explicit LLM_PROVIDER wins; else prefer OpenAI when its
    key is present, else Groq. Works for anyone who has EITHER key."""
    _load_env_file()
    forced = (os.environ.get("LLM_PROVIDER") or "").strip().lower()
    have_openai = bool(os.environ.get("OPENAI_API_KEY"))
    have_groq = bool(os.environ.get("GROQ_API_KEY"))
    if forced in ("openai", "groq"):
        key = "OPENAI_API_KEY" if forced == "openai" else "GROQ_API_KEY"
        if not os.environ.get(key):
            raise RuntimeError(f"LLM_PROVIDER={forced} but {key} is not set in .env.")
        return forced
    if have_openai:            # prefer OpenAI when both are present
        return "openai"
    if have_groq:
        return "groq"
    raise RuntimeError(
        "No LLM key found. Add OPENAI_API_KEY and/or GROQ_API_KEY to the "
        "cookbook-root .env. This is an evaluation path — it will not fall back "
        "to a stub. (Set LLM_PROVIDER=openai|groq to force one when both exist.)"
    )


def _client_and_model():
    provider = resolve_provider()
    if provider == "openai":
        from openai import OpenAI
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"]), OPENAI_MODEL, provider
    from groq import Groq
    return Groq(api_key=os.environ["GROQ_API_KEY"]), GROQ_MODEL, provider


def _extract_final(text: str) -> str:
    """Last non-empty line, with a leading 'final answer:'-style label removed.
    Fixes the empty-answer case where the model does not end on a clean line."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    last = lines[-1]
    for pre in ("final answer:", "answer:", "final:"):
        if last.lower().startswith(pre):
            last = last[len(pre):].strip()
    return last


def _create_with_retry(client, *, model, messages, temperature=0.0, max_tries=8):
    """Call chat.completions.create, retrying on rate-limit (429) with backoff.

    Providers enforce per-minute request limits. Honour the server's suggested
    wait when present, otherwise back off exponentially. Fails loud after
    max_tries rather than returning a stub."""
    for attempt in range(1, max_tries + 1):
        try:
            return client.chat.completions.create(
                model=model, messages=messages, temperature=temperature)
        except Exception as e:                       # noqa: BLE001
            msg = str(e)
            is_rate = "429" in msg or "rate_limit" in msg.lower()
            # A per-DAY cap (RPD) won't clear within a run — fail loud immediately.
            if is_rate and ("per day" in msg.lower() or "rpd" in msg.lower()):
                raise RuntimeError(
                    "Daily request limit reached for this model. Wait for the "
                    "limit to reset, raise it with the provider, or select "
                    "another provider via LLM_PROVIDER. Original: " + msg)
            if not is_rate or attempt == max_tries:
                raise
            m = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", msg)
            wait = (int(m.group(1) or 0) * 60 + float(m.group(2)) + 1.0
                    if m else min(2 ** attempt, 30))
            time.sleep(wait)


def answer(question: str, table_csv: str, table_aware: bool,
           temperature: float = 0.0) -> dict:
    prompt = build_prompt(question, table_csv, table_aware)
    client, model, provider = _client_and_model()
    resp = _create_with_retry(
        client, model=model,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": prompt}],
        temperature=temperature,
    )
    text = resp.choices[0].message.content.strip()
    final = _extract_final(text)
    usage = getattr(resp, "usage", None)
    return {"final": final, "raw": text,
            "model": f"{provider}:{model}", "model_id": model,
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "config": "table_aware" if table_aware else "naive"}
