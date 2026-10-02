# ClinicalSearch Extraction Quality Benchmark

Date: 2026-09-18
Papers: 20  |  Chunks: 680

## Structural Integrity

| Check | Result |
|---|---|
| Papers with page gaps | 0 / 20 |
| Empty/near-empty chunks | 16 / 680 (2.4%) |
| Chunks with shrunk embed_text | 0 |
| Suspicious glyph hits (encoding corruption) | 33 |
| Table chunks missing table_md | 0 / 202 |
| Table chunks missing table_cells | 0 / 202 |
| Table cells_status distribution | {'ok': 202} |
| Table row-count mismatches (table_data vs table_n_data_rows) | 6 |
| Duplicate chunk pairs | 8 |

## Embedding Health

| Check | Result |
|---|---|
| Shape | [680, 3072] |
| NaN values | 0 |
| Zero-norm vectors | 0 |
| Norm mean / std | 1.0000 / 0.0003 |
| Within-paper cosine mean | 0.6337 |
| Across-paper cosine mean | 0.5537 |
| Semantic separation | 0.0801 |
| Near-duplicate embedding pairs (cos>0.995) | 2 |

## Metadata Fidelity (vs. CrossRef)

| Check | Result |
|---|---|
| Papers checked | 20 |
| Pass (title sim ≥ 0.80) | 3 |
| Title mismatch | 10 |
| No DOI found in text | 6 |
| CrossRef lookup failed | 1 |
| Pass rate | 15.0% |

### Per-paper detail

| Paper | Status | Title sim | Author overlap |
|---|---|---|---|
| 00000637_201506000_00005 | pass | 1.0 | 0.4 |
| 00006534_201403000_00008 | title_mismatch | 0.61 | 0.0 |
| 00006534_202107000_00005 | title_mismatch | 0.101 | 0.0 |
| 00006534_202112000_00001 | title_mismatch | 0.058 | 0.0 |
| 00006534_202402000_00003 | title_mismatch | 0.642 | 0.0 |
| an_inferolateral_approach_to_nipple_spar | pass | 1.0 | 0.0 |
| careful_where_you_cut_strategies_for_suc | title_mismatch | 0.137 | 0.0 |
| inframammary_versus_periareolar_incision | title_mismatch | 0.076 | 0.0 |
| nipple_pathology_in_total_skin_sparing_m | pass | 1.0 | 0.2 |
| piis0748798318310564 | no_doi_found | None | - |
| piis0960977620301399 | title_mismatch | 0.068 | 0.0 |
| s00595_020_01975_y | crossref_lookup_failed | None | - |
| s10434_012_2362_y | no_doi_found | None | - |
| s10434_015_4734_6 | no_doi_found | None | - |
| s12282_018_0908_y | no_doi_found | None | - |
| s12957_023_02898_x | no_doi_found | None | - |
| safety_of_incision_placement_with_nipple | title_mismatch | 0.048 | 0.0 |
| the_breast_journal_2019_ng_mastectomy_fl | title_mismatch | 0.0 | 0.0 |
| total_skin_sparing_mastectomy_complicati | title_mismatch | 0.213 | 0.143 |
| znad107 | no_doi_found | None | - |
