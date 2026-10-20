import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "embedder_comparison.ipynb"
CATALOG = json.loads((HERE / "embedders.json").read_text(encoding="utf-8"))


def load_dotenv_file():
    path = HERE / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().removeprefix("export ").strip()
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))


def menu(title, options, default):
    print(f"\n{title}")
    for k, v in options:
        print(f"  {k:>3}. {v}")
    raw = input(f"Choose [{default}]: ").strip()
    return raw or default


def main():
    load_dotenv_file()
    rows = []
    for e in CATALOG:
        status = ""
        if e["provider"] == "api" and not e.get("key_optional"):
            status = "ready" if os.environ.get(e["key_env"]) else f"needs {e['key_env']}"
        rows.append((str(e["id"]), f"{e['name']:<36} {e['provider']:<6} {e['family']:<8} {status}"))
    rows.append(("", "groups: all, local, medical, general, api   ranges: 7..11   mix: 1,6,9"))

    embedders = menu("Embedders", rows, os.environ.get("BENCH_EMBEDDERS", "1,6"))
    mode = menu("Run mode", [("1", "quick: easy corpus only, 300 questions, 2 runs"),
                             ("2", "standard: both corpora, all questions, 3 runs"),
                             ("3", "full: both corpora, all questions, 5 runs")], os.environ.get("BENCH_MODE", "2"))
    device = menu("Device", [("1", "auto"), ("2", "cuda"), ("3", "cpu"), ("4", "mps")], os.environ.get("BENCH_DEVICE", "1"))
    store = menu("Vector store", [("1", "local FAISS"), ("2", "Pinecone (needs PINECONE_API_KEY)")], "2" if os.environ.get("USE_PINECONE", "").lower() == "true" else "1")
    action = menu("Action", [("1", "run the notebook now and save outputs into it"),
                             ("2", "only print the export commands")], "1")

    chosen = {
        "BENCH_EMBEDDERS": embedders,
        "BENCH_MODE": mode,
        "BENCH_DEVICE": device,
        "USE_PINECONE": "true" if store == "2" else "false",
    }
    if store == "2" and not os.environ.get("PINECONE_API_KEY"):
        print("\nPINECONE_API_KEY is not set. Export it or add it to .env first.")
        sys.exit(1)

    print("\nEquivalent non interactive run:")
    for k, v in chosen.items():
        print(f'export {k}="{v}"')
    print(f"jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 {NOTEBOOK.name}")
    if action == "2":
        return

    if not shutil.which("jupyter"):
        print("\njupyter is not installed: pip install jupyter nbconvert ipykernel")
        sys.exit(1)
    env = dict(os.environ, **chosen)
    cmd = ["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=-1", NOTEBOOK.name]
    print("\nRunning, outputs will be written into the notebook...")
    sys.exit(subprocess.call(cmd, cwd=HERE, env=env))


if __name__ == "__main__":
    main()
