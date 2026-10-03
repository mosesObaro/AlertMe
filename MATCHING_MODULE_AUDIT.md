# Matching Module Audit & Enhancement Report

*Generated: 2026-10-03*

---

## Summary

This document records the findings of the professor–research-problem matching module audit and all changes made to improve it.

---

## 1. Pre-Enhancement Audit Findings

### Critical

| # | File | Problem | Fix Applied |
|---|------|---------|-------------|
| C1 | `src/research_gaps/supervisor_matcher.py` | Only read `data/supervisors.json` and `data/researcher_watchlist.json` — completely ignored the 62 curated professors in `src/supervisors/data/*/professors.json` | ✅ `_load_per_country_professors()` now reads all 7 country directories |
| C2 | `src/research_gaps/supervisor_matcher.py` | No match explanations generated — outputs were impossible to interpret or validate | ✅ `_build_explanation()` generates human-readable rationale for every match |

### High

| # | File | Problem | Fix Applied |
|---|------|---------|-------------|
| H1 | `src/research_gaps/supervisor_matcher.py` | Keyword matching only used `research_areas`/`topics` fields; ignored `research_summary`, `edge_relevance`, `research_trajectory` free-text fields | ✅ Bio text fields now contribute 40% of keyword score via `_overlap_ratio()` |
| H2 | `src/research_gaps/supervisor_matcher.py` | Publication inline records from professors.json (`recent_papers`, `publications` as dicts) were not being loaded at all | ✅ `_get_professor_publications()` reads inline publications first |
| H3 | `src/research_gaps/supervisor_matcher.py` | Composite score formula ignored recruitment status entirely | ✅ `_recruitment_bonus()` adds up to 5% weight for `CONFIRMED_ACTIVE` professors |
| H4 | `src/research_gaps/models.py` | `SupervisorMatch` had no `match_explanation` field | ✅ Added `match_explanation: str = ""` to the dataclass |
| H5 | `src/research_gaps/pipeline.py` | After matching, no outputs were written; results only existed in transient memory | ✅ `export_matches()` called after `match_all()` — writes JSON/CSV/MD to `outputs/` |
| H6 | `src/research_gaps/dashboard_generator.py` | `supervisor_map` payload was a nested dict keyed by problem_id; dashboard JS had to manually flatten and deduplicate | ✅ `supervisor_list` flat array added to payload; `professor_matches.json` written separately |

### Medium

| # | File | Problem | Fix Applied |
|---|------|---------|-------------|
| M1 | `src/research_gaps/supervisor_matcher.py` | `max_matches` default was 5 — insufficient diversity for a 62-professor dataset | ✅ Default raised to 10 |
| M2 | `src/research_gaps/supervisor_matcher.py` | Matching keywords were raw intersecting word tokens, not readable phrases | ✅ Now returns matching `research_interests` phrases rather than single tokens |
| M3 | `src/research_gaps/supervisor_matcher.py` | No paper cache persistence | ✅ `professor_paper_cache.json` loaded/saved via `_load_paper_cache()` / `_save_paper_cache()` |
| M4 | `src/research_gaps/dashboard_generator.py` | Supervisor tab had no country/area/score filters | ✅ Four filter controls added to HTML |
| M5 | `docs/research-gaps.html` | Supervisor table showed 5 plain columns, no match explanation or match-strength indicator | ✅ Expandable rows with match_explanation, publication list, and match-score visual bar |
| M6 | `tests/test_research_gaps.py` | `SupervisorMatcher` had only 2 tests, covering basic match/no-match | ✅ 10 new tests added covering: per-country loading, explanation field, score range, recruitment bonus, publication boost, max_results, match_all, model roundtrip, export files, and no-match threshold |

### Low

| # | File | Problem | Fix Applied |
|---|------|---------|-------------|
| L1 | `src/research_gaps/supervisor_matcher.py` | No output to `outputs/` directory meant results could not be reviewed externally | ✅ `problem_professor_matches.{json,csv,md}` written to `outputs/` |
| L2 | `docs/research-gaps.html` | Mock data for offline preview had wrong supervisor format | ✅ Updated to use `supervisor_list` with all enhanced fields |

---

## 2. Changes Made

### `src/research_gaps/models.py`
- Added `match_explanation: str = ""` field to `SupervisorMatch` dataclass.

### `src/research_gaps/supervisor_matcher.py` (full rewrite)

**Data loading:**
- `_load_per_country_professors()` — loads all professors from `src/supervisors/data/{country}/professors.json` for 7 configured countries (62 total)
- `load_supervisor_data()` — merges per-country professors with legacy `data/supervisors.json` and `data/researcher_watchlist.json`, with caching via `_professor_cache`
- `_load_paper_cache()` / `_save_paper_cache()` — persistent JSON cache at `data/professor_paper_cache.json`

**Improved scoring (multi-factor composite):**
```
composite = keyword_score × 0.45 + pub_relevance × 0.20 + recruitment_bonus × 0.05
```
Where:
- `keyword_score` = Jaccard similarity on `research_interests` + 40% overlap on bio text fields
- `pub_relevance` = token overlap between problem terms and recent paper titles/abstracts, with 1.2× recency multiplier for papers ≤3 years old
- `recruitment_bonus` = 1.0 for `CONFIRMED_ACTIVE`, 0.75 for `STRONG_EVIDENCE`, 0.4 for `POSSIBLE`

**Match explanation generation (`_build_explanation`):**
- States which research interests matched the problem
- Cites a specific recent publication as evidence
- Quotes the professor's research bio
- Notes active recruitment evidence if available
- Lists potential PhD topics in the lab

**Export methods (`export_matches`):**
- `outputs/problem_professor_matches.json` — full structured data with all match fields
- `outputs/problem_professor_matches.csv` — flat table for spreadsheet analysis
- `outputs/problem_professor_matches.md` — human-readable Markdown report with stats and grouped detail cards

### `src/research_gaps/pipeline.py`
- Added `max_matches=10` to `match_all()` call
- Added `export_matches()` call after matching step (with error guard)

### `src/research_gaps/dashboard_generator.py`
- Enriches each problem dict with `supervisor_matches` inline (for fast rendering)
- Builds `supervisor_list` flat array (problem_id, problem_statement, research_area + all match fields)
- Adds `total_supervisor_matches` and `supervisor_matches_by_country` to meta
- Writes `docs/data/professor_matches.json` separately (for lazy-load use)

### `docs/research-gaps.html`
**New CSS:**
- `.match-bar-wrap`, `.match-bar-bg`, `.match-bar-fill` — visual match-strength bar
- `.match-bar-high/medium/low` — colour-coded by score threshold
- `.filter-select` — consistent styled dropdowns
- `.sup-detail`, `.sup-detail-grid`, `.sup-detail-section` — expandable professor card layout

**New HTML (Supervisors tab):**
- Country filter dropdown (populated from live data)
- Research Area filter dropdown (populated from live data)
- Score threshold filter (High ≥0.35 / Medium ≥0.20 / Low ≥0.10)
- Sort dropdown (by score, name, institution, area)
- Stats banner (count by confidence tier)
- 7-column table with expandable rows
- Expandable row shows: research areas, matching keywords, match explanation, relevant publications, full score

**New JS:**
- `getSupervisorList()` — prefers `supervisor_list`, falls back to flattening legacy `supervisors` map
- `populateSupervisorFilters()` — dynamically fills country/area dropdowns
- `matchScoreBar(score)` — renders visual bar with colour coding
- `filterSupervisors()` — multi-filter + multi-sort logic with stats banner
- `toggleSupDetail(rowId)` — accordion expand/collapse for detail rows
- `renderSupervisors()` — calls both filter population and rendering

### `tests/test_research_gaps.py`
Added 10 new tests in section `# 13. Enhanced SupervisorMatcher`:
1. `test_supervisor_match_explanation_field` — non-empty explanation produced
2. `test_supervisor_match_score_range` — scores in [0, 1]
3. `test_supervisor_recruitment_bonus` — CONFIRMED_ACTIVE ≥ UNKNOWN
4. `test_supervisor_pub_relevance_boosts_score` — pub match raises score
5. `test_supervisor_match_max_results` — respects `max_matches`
6. `test_supervisor_match_all_returns_dict` — correct return type
7. `test_supervisor_match_model_roundtrip` — to_dict/from_dict preserves all fields including `match_explanation`
8. `test_supervisor_export_matches_creates_files` — all 3 output files created with correct structure
9. `test_supervisor_no_match_below_threshold` — unrelated professor filtered out
10. `test_supervisor_per_country_data_loads` — `_load_per_country_professors()` reads from configured directories

---

## 3. Precision / Coverage Analysis (Structural)

| Metric | Before | After |
|--------|--------|-------|
| Professor sources loaded | 2 (runtime JSON files) | 9 (7 country static files + 2 runtime) |
| Professor profiles available | ~0–few (runtime only) | 62 curated professors |
| Matching factors | 2 (keyword Jaccard + pub titles) | 4 (keyword, bio text, publication relevance, recruitment bonus) |
| Match explanation | None | Generated for every match |
| Output files | 0 | 3 (JSON, CSV, MD) |
| Test coverage (SupervisorMatcher) | 2 tests | 12 tests (2 existing + 10 new) |
| Dashboard filter controls | 1 (text search) | 4 (search + country + area + score threshold) |
| Dashboard sort options | 1 (score only) | 4 (score, name, institution, area) |
| Match strength indicator | Text score only | Visual bar + confidence badge (High/Med/Low) |
| Match explanation in UI | Not shown | Shown in expandable row |
| Relevant publications in UI | Not shown | Up to 3 publications per match with links |

---

## 4. Recommendations for Further Improvement

1. **Live paper retrieval (future enhancement):** Add optional network calls in `_get_professor_publications()` to query OpenAlex for recent papers by professor name + institution. Cache results to `professor_paper_cache.json`. This would significantly improve publication relevance scoring for professors whose JSON profiles don't include `recent_papers` as dicts.

2. **Semantic embedding similarity:** Replace token-overlap Jaccard with TF-IDF cosine or sentence-transformer embeddings for better semantic matching (e.g., "neural network inference" matches "deep learning model deployment" even without shared tokens).

3. **Missing `research_gaps` field:** The professor JSON files include a `research_gaps` field (e.g., `"Heterogeneous device communication latency"`). These should be compared directly against `problem.problem_statement` for an additional scoring signal.

4. **Research-group pages:** The `config/research_groups.yaml` includes lab web pages. Scraping these periodically (in `lab_recruitment.py`) and storing findings in `professor_paper_cache.json` would provide richer matching evidence.

5. **Weak-confidence flagging in pipeline:** Problems where all matches score < 0.20 should be flagged in `pipeline_meta` and surfaced in the dashboard as needing keyword enrichment.
