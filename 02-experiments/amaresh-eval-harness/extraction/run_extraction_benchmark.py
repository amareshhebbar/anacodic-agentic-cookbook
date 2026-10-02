from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from metrics import group_by_paper, load_chunks, run_structural_and_embedding_checks
from metadata_fidelity import run_metadata_fidelity

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def write_leaderboard(structural: dict, fidelity: dict | None) -> None:
    lines = ["# ClinicalSearch Extraction Quality Benchmark\n\n"]
    lines.append(f"Date: {time.strftime('%Y-%m-%d')}\n")
    lines.append(f"Papers: {structural['n_papers']}  |  Chunks: {structural['n_chunks']}\n\n")

    lines.append("## Structural Integrity\n\n")
    lines.append("| Check | Result |\n|---|---|\n")
    lines.append(f"| Papers with page gaps | {structural['page_coverage']['papers_with_gaps']} / {structural['page_coverage']['papers_checked']} |\n")
    lines.append(f"| Empty/near-empty chunks | {structural['empty_chunks']['empty_chunks']} / {structural['empty_chunks']['total_chunks']} ({structural['empty_chunks']['empty_ratio']:.1%}) |\n")
    lines.append(f"| Chunks with shrunk embed_text | {structural['context_injection']['chunks_with_shrunk_embed_text']} |\n")
    lines.append(f"| Suspicious glyph hits (encoding corruption) | {structural['suspicious_glyphs']['total_hits']} |\n")
    ts = structural["table_structure"]
    lines.append(f"| Table chunks missing table_md | {ts['missing_table_md']} / {ts['total_table_chunks']} |\n")
    lines.append(f"| Table chunks missing table_cells | {ts['missing_table_cells']} / {ts['total_table_chunks']} |\n")
    lines.append(f"| Table cells_status distribution | {ts['table_cells_status']} |\n")
    lines.append(f"| Table row-count mismatches (table_data vs table_n_data_rows) | {ts['row_count_mismatches']} |\n")
    lines.append(f"| Duplicate chunk pairs | {structural['duplicate_chunks']['duplicate_pairs']} |\n")

    lines.append("\n## Embedding Health\n\n")
    eh = structural["embedding_health"]
    lines.append("| Check | Result |\n|---|---|\n")
    lines.append(f"| Shape | {eh['shape']} |\n")
    lines.append(f"| NaN values | {eh['nan_count']} |\n")
    lines.append(f"| Zero-norm vectors | {eh['zero_norm_vectors']} |\n")
    lines.append(f"| Norm mean / std | {eh['norm_mean']:.4f} / {eh['norm_std']:.4f} |\n")

    esl = structural["embedding_semantic_locality"]
    lines.append(f"| Within-paper cosine mean | {esl['within_paper_cosine_mean']:.4f} |\n")
    lines.append(f"| Across-paper cosine mean | {esl['across_paper_cosine_mean']:.4f} |\n")
    lines.append(f"| Semantic separation | {esl['separation']:.4f} |\n")

    end = structural["embedding_near_duplicates"]
    lines.append(f"| Near-duplicate embedding pairs (cos>0.995) | {end['near_duplicate_pairs']} |\n")

    if fidelity:
        lines.append("\n## Metadata Fidelity (vs. CrossRef)\n\n")
        lines.append("| Check | Result |\n|---|---|\n")
        lines.append(f"| Papers checked | {fidelity['papers_checked']} |\n")
        lines.append(f"| Pass (title sim ≥ 0.80) | {fidelity['passed']} |\n")
        lines.append(f"| Title mismatch | {fidelity['title_mismatch']} |\n")
        lines.append(f"| No DOI found in text | {fidelity['no_doi_found']} |\n")
        lines.append(f"| CrossRef lookup failed | {fidelity['crossref_lookup_failed']} |\n")
        lines.append(f"| Pass rate | {fidelity['pass_rate']:.1%} |\n")
        lines.append("\n### Per-paper detail\n\n")
        lines.append("| Paper | Status | Title sim | Author overlap |\n|---|---|---|---|\n")
        for r in fidelity["detail"]:
            lines.append(
                f"| {r['paper_slug'][:40]} | {r['status']} | "
                f"{r.get('title_similarity', '-')} | {r.get('author_overlap_ratio', '-')} |\n"
            )
    else:
        lines.append("\n## Metadata Fidelity (vs. CrossRef)\n\nSkipped (--skip-crossref).\n")

    (Path(__file__).parent / "LEADERBOARD.md").write_text("".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-meta", default="chunk_meta.jsonl")
    parser.add_argument("--embeddings", default="embeddings.npy")
    parser.add_argument("--mailto", default=None)
    parser.add_argument("--skip-crossref", action="store_true")
    args = parser.parse_args()

    structural = run_structural_and_embedding_checks(args.chunk_meta, args.embeddings)

    fidelity = None
    if not args.skip_crossref:
        chunks = load_chunks(args.chunk_meta)
        papers = group_by_paper(chunks)
        doi_map = structural["dois_by_paper"]
        fidelity = run_metadata_fidelity(papers, doi_map, mailto=args.mailto)

    run_id = time.strftime("%Y%m%d-%H%M%S")
    out = {"structural": structural, "metadata_fidelity": fidelity}
    (RESULTS_DIR / f"{run_id}.json").write_text(json.dumps(out, indent=2, default=str))

    write_leaderboard(structural, fidelity)
    print(f"Wrote results/{run_id}.json and LEADERBOARD.md")


if __name__ == "__main__":
    main()