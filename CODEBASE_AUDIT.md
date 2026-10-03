# Codebase Engineering Audit: AlertMe System

**Date:** October 2026  
**Audited Target:** AlertMe Repository (`src/`, `hk_supervisor_intel/`, `config/`, `.github/workflows/`, `tests/`)  
**Scope:** Architecture, Code Quality & Maintainability, Runtime Bugs & Edge Cases, Error Handling & Resilience, Performance & Complexity, Security, Test Coverage, Dependencies & Configuration, and Technical Debt.

---

## Executive Summary

AlertMe is an ambitious academic intelligence and PhD discovery platform featuring multi-source literature aggregation, multi-factor scoring, multi-country supervisor profiling, academic event tracking, and automated GitHub Pages dashboards. 

While the test suite demonstrates 239 passing unit tests and an overall 71% statement coverage, a comprehensive architectural and engineering audit identified **3 Critical**, **5 High**, **8 Medium**, and **7 Low** severity findings. 

The most urgent issues involve:
1. **Non-deterministic state truncation** via unordered set slicing that silently discards recent historical IDs, causing previously alerted items to be re-alerted.
2. **Gitignored event state** in `.gitignore` that prevents event deduplication state from persisting across GitHub Actions workflow runs, causing duplicate alerts on every daily cron.
3. **Parameter inversion bugs** in the CLI opportunity classifier that breaks family/dependant support classification.
4. **A complete parallel architectural fork** between `hk_supervisor_intel/` and `src/supervisors/`, resulting in duplicate daily cron runs, dual state files, and 1,500+ lines of duplicated code.
5. **Core orchestration pipelines and collectors lacking unit test coverage** (`src/research_gaps/pipeline.py` at 0%, `src/pipeline.py` at 13%, collectors hovering between 18% and 29%).

The findings below are prioritized strictly by severity and provide exact file locations, failure mechanisms, and actionable improvements.

---

## 1. Critical Severity Findings

### [CRIT-01] Non-Deterministic State Truncation via Unordered Set Slicing
* **Location:** `src/storage/state_manager.py` (lines 78–80), `src/events/state_manager.py` (lines 91–94)
* **Problem:**  
  In both `StateManager.record_seen_items()` and `EventsStateManager.record_seen_events()`, the historical seen IDs are maintained in a Python `set`. When enforcing the 2,000 ID retention limit, the code converts the set to a list and slices the last 2,000 elements:
  ```python
  id_list = list(existing_ids)
  if len(id_list) > 2000:
      id_list = id_list[-2000:]
  ```
  Python `set` iteration order is determined by hash table layout and randomized hash seeding between process invocations. Converting a `set` to a `list` does **not** preserve chronological insertion order. Consequently, when `id_list` exceeds 2,000 items, newly added items from today's run can be randomly dropped while items from years ago are retained. Once dropped, items are no longer recognized as seen, causing duplicate alerts, duplicate emails, and repeated processing.
* **Recommended Improvement:**  
  Persist seen items as an ordered structure (e.g., a JSON list of IDs, an `OrderedDict`, or a dictionary mapping `id -> timestamp_added`). When capping to 2,000 entries, sort by timestamp ascending and slice `[-2000:]` or maintain a FIFO queue to guarantee that the oldest items are pruned while recent discoveries are retained.

---

### [CRIT-02] Event Deduplication Broken Across CI Workflows Due to `.gitignore`
* **Location:** `.gitignore` (lines 29–34), `.github/workflows/daily-alert.yml` (line 65)
* **Problem:**  
  The `.gitignore` file explicitly ignores event state files:
  ```gitignore
  # Runtime Event State Files
  data/events.json
  data/events_history.json
  data/ml_iot_events.json
  data/ml_iot_events_history.json
  data/seen_events.json
  data/seen_ml_iot_events.json
  ```
  In GitHub Actions (`daily-alert.yml`), state persistence relies on:
  ```bash
  git add data/ docs/data.json
  git commit -m "chore(data): auto-update research intelligence state [skip ci]"
  ```
  Because `seen_events.json` and `events.json` are gitignored, git silently skips them. On every scheduled GitHub Actions runner invocation (which checks out a clean repository), `seen_events.json` does not exist. The pipeline starts with an empty seen set on every run, re-evaluates all historical events, and dispatches duplicate event alerts in the daily email digest every single day.
* **Recommended Improvement:**  
  Remove `data/seen_events.json`, `data/seen_ml_iot_events.json`, `data/events.json`, and `data/ml_iot_events.json` from `.gitignore` so they are committed and pushed back to the repository alongside `seen_items.json` and `alert_history.json`.

---

### [CRIT-03] Parameter Inversion in CLI Dependant Support Classification
* **Location:** `src/cli.py` (line 341)
* **Problem:**  
  In `debug_opportunity_score()`, the parameters passed to `classify_dependant_support()` are inverted:
  ```python
  # src/cli.py line 341
  dep_status, dep_info = scorer.classify_dependant_support(opp.country, full_text)
  ```
  The method signature in `src/ranking/opportunity_scorer.py` (line 108) is:
  ```python
  def classify_dependant_support(self, text: str, country: str = "") -> Tuple[str, str]:
  ```
  Passing `opp.country` (e.g. `"Germany"`) as `text` and `full_text` as `country` causes:
  1. Financial keyword matching (`"family allowance"`, `"child supplement"`) to search inside the single country word `"germany"`, failing every keyword check.
  2. Country normalization (`country.strip().title() in ["Germany", ...]`) to evaluate the multi-paragraph opportunity description, failing the country visa check.
  This causes valid opportunities with family allowances or legal visas to be classified as `UNKNOWN` in CLI evaluations.
* **Recommended Improvement:**  
  Correct the call in `src/cli.py` to `scorer.classify_dependant_support(full_text, opp.country)`. Add a unit test verifying CLI debug output for opportunity scoring.

---

## 2. High Severity Findings

### [HIGH-01] Parallel Architectural Fork and Dual Scheduled Execution
* **Location:** `hk_supervisor_intel/` (14 files, ~1,500 lines) vs `src/supervisors/` (12 files, ~2,200 lines); `.github/workflows/hk_supervisor_daily_intel.yml` vs `.github/workflows/country_supervisor_intel.yml`
* **Problem:**  
  `src/supervisors/` was built as a multi-country generalization of `hk_supervisor_intel/`, including `hong_kong` under `src/supervisors/data/hong_kong/`. However, `hk_supervisor_intel/` was never deprecated or removed. As a result:
  1. Two separate GitHub Actions workflows run daily: `hk_supervisor_daily_intel.yml` runs at `00:00 UTC`, and `country_supervisor_intel.yml` runs at `05:00 UTC` for `all` countries (which includes Hong Kong).
  2. Hong Kong professors are crawled, scored, and alerted twice every single day.
  3. The two modules maintain separate state files (`hk_supervisor_intel/data/state.json` vs `src/supervisors/data/supervisor_state.json`) with different schemas, leading to split alert histories and divergent seen tracking.
  4. Models, profilers, Excel workbook generators, and scoring algorithms are duplicated across both packages, doubling maintenance overhead and bug surface area.
* **Recommended Improvement:**  
  Consolidate entirely into `src/supervisors/`. Deprecate `hk_supervisor_intel/`, remove `.github/workflows/hk_supervisor_daily_intel.yml`, and ensure `country_supervisor_intel.yml` serves Hong Kong alongside the other target countries.

---

### [HIGH-02] Active Events Overwritten and Lost on Each Pipeline Execution
* **Location:** `src/events/pipeline.py` (lines 67–89), `src/events/state_manager.py` (lines 67–70)
* **Problem:**  
  In `EventsPipeline.run()`:
  ```python
  seen_ids = self.state_manager.load_seen_event_ids() if not dry_run else set()
  unique_events = self.deduplicator.deduplicate(raw_events, seen_ids=seen_ids)
  ...
  if not dry_run and scored_events:
      self.state_manager.save_events(scored_events)
  ```
  `deduplicate` excludes any events previously present in `seen_ids`. Therefore, `scored_events` only contains brand-new events discovered during the current execution. When `save_events(scored_events)` is called, it overwrites `events.json` with only today's new items. Active, upcoming conferences and workshops discovered yesterday that are still 6 months away are completely purged from `events.json`.
* **Recommended Improvement:**  
  In `EventsStateManager.save_events()`, merge newly scored active events with existing active events from `load_events()`, filtering out only events whose end dates have passed (`event.end_date < today`).

---

### [HIGH-03] Non-Atomic State Writes in Supervisor Storage Manager
* **Location:** `src/supervisors/storage.py` (lines 162–171)
* **Problem:**  
  While `src/storage/state_manager.py` provides an atomic write helper (`_atomic_write_json` using a temporary file and `os.replace`), `src/supervisors/storage.py` writes state files directly:
  ```python
  def save_state(self):
      """Atomically saves runtime state to disk."""
      ...
      with open(self.state_file, "w", encoding="utf-8") as f:
          json.dump(self.state_data, f, indent=2, ensure_ascii=False)
  ```
  Despite the docstring claiming atomic persistence, opening a file with `"w"` immediately truncates it to 0 bytes before writing. If the process is terminated (due to GitHub Actions runner timeout, disk full, or SIGTERM), `supervisor_state.json` is corrupted or emptied permanently.
* **Recommended Improvement:**  
  Import and reuse `_atomic_write_json` from `src.storage.state_manager` in `src/supervisors/storage.py`.

---

### [HIGH-04] Unconditional State Recording Despite Email Dispatch Failures
* **Location:** `src/pipeline.py` (lines 347–351, 387–391, 396–400)
* **Problem:**  
  In `ResearchPipeline.run()`:
  ```python
  email_sent = self.email_sender.send(subject, html, text)
  if not dry_run and daily_items:
      self.state_manager.record_seen_items(daily_items)
      self.state_manager.record_alerts_sent(daily_items, alert_mode="daily")
  ```
  State persistence is performed regardless of the return value of `email_sent`. If an external email provider fails (e.g. invalid API key, Resend rate limit, SMTP connection drop), the pipeline still marks all `daily_items` as "seen" and "alerted". On the next daily run, those items are filtered out by the deduplicator and will **never** be delivered to the user.
  Additionally, in urgent mode (line 400), `email_sent = True` is hardcoded even when zero urgent items were sent or when `send()` failed.
* **Recommended Improvement:**  
  Only call `record_seen_items()` and `record_alerts_sent()` if `email_sent is True` (or if explicit dry-run mode was requested). Log an error and retain items in the unnotified pool if delivery fails.

---

### [HIGH-05] Uncaught `ValueError` on Standard RFC HTTP `Retry-After` Header
* **Location:** `src/utils/rate_limiter.py` (lines 60–66)
* **Problem:**  
  When encountering HTTP 429, 503, or 504 status codes:
  ```python
  if response.status_code in [429, 503, 504]:
      retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
      time.sleep(retry_after)
      continue
  ```
  Under RFC 7231 / 9110, `Retry-After` can be either an integer number of seconds OR an HTTP-date string (e.g., `"Wed, 21 Oct 2026 07:28:00 GMT"`). Passing an HTTP-date string to `int()` raises `ValueError`. Because the surrounding `try/except` block only catches `requests.exceptions.RequestException`, the `ValueError` propagates unhandled and crashes the collector.
* **Recommended Improvement:**  
  Safely parse `Retry-After` by attempting `int()`, falling back to `email.utils.parsedate_to_datetime()`, and defaulting to exponential backoff `2 ** attempt` if parsing fails. Catch generic `Exception` inside the backoff handler.

---

## 3. Medium Severity Findings

### [MED-01] Potential `TypeError` on Missing Topics in Academic Researcher Discovery
* **Location:** `src/collectors/academic_researcher_discovery.py` (lines 55–56, 75)
* **Problem:**  
  Lines 55–56 and 75 contain:
  ```python
  research_areas=list(set(item.topics or item.score.matched_topics))
  ...
  for t in (item.topics or item.score.matched_topics):
  ```
  If `item.topics` is an empty list `[]` and `item.score.matched_topics` is `None` (or empty), the Python expression `[] or None` evaluates to `None`. Calling `set(None)` or iterating `for t in None` raises `TypeError: 'NoneType' object is not iterable`.
* **Recommended Improvement:**  
  Use `(item.topics or (item.score.matched_topics if item.score else [])) or []` or a dedicated helper to ensure a list is always returned.

---

### [MED-02] Security Risk: LLM API Key Transmitted as HTTP Query Parameter
* **Location:** `src/summarization/intelligence.py` (line 135)
* **Problem:**  
  In `_analyze_with_ai()`:
  ```python
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
  res = self.requester.session.post(url, json=payload, timeout=20)
  ```
  Placing API keys in query parameters exposes them in web proxy logs, HTTP client debug logs, referrer headers, and error tracebacks.
* **Recommended Improvement:**  
  Pass the API key via the HTTP header `x-goog-api-key: {self.api_key}` as recommended by Google Cloud security standards.

---

### [MED-03] Insecure Plaintext HTTP Protocol for arXiv Queries
* **Location:** `src/collectors/arxiv.py` (line 10)
* **Problem:**  
  `ARXIV_API_URL = "http://export.arxiv.org/api/query"` uses unencrypted HTTP. Plaintext queries are susceptible to eavesdropping, MITM payload tampering, and proxy redirection issues.
* **Recommended Improvement:**  
  Change `ARXIV_API_URL` to `"https://export.arxiv.org/api/query"`.

---

### [MED-04] Core Orchestration Pipelines and Collectors Lack Unit Test Coverage
* **Location:** `src/research_gaps/pipeline.py` (0% coverage), `src/pipeline.py` (13% coverage), `src/cli.py` (22% coverage), `src/collectors/` (18%–29% coverage)
* **Problem:**  
  The pytest coverage report reveals major blind spots in end-to-end integration:
  * `src/research_gaps/pipeline.py`: 193 statements, **0% tested**.
  * `src/pipeline.py`: 239 statements, **13% tested** (207 statements untouched).
  * `src/collectors/semantic_scholar.py`: **20% tested**.
  * `src/collectors/crossref.py`: **26% tested**.
  * `src/collectors/openalex.py`: **29% tested**.
  * `src/collectors/rss_collector.py`: **18% tested**.
  * `src/email/sender.py`: **27% tested** (provider integrations are untested with mocked HTTP).
* **Recommended Improvement:**  
  Add mock-based integration tests for `ResearchPipeline.run()` (modes daily, weekly, urgent) and `ResearchGapPipeline.run()`. Add response-fixture tests for `OpenAlexCollector`, `CrossrefCollector`, and `SemanticScholarCollector`.

---

### [MED-05] Quadratic $O(N^2)$ Complexity and Linear Scanning in Deduplicator
* **Location:** `src/deduplication/deduplicator.py` (lines 85–107)
* **Problem:**  
  In `Deduplicator.is_duplicate()`, incoming items are checked against `seen_pool` by performing a linear scan over every existing item. Inside the loop, it performs string normalizations on DOIs, arXiv IDs, and URLs, and computes `difflib.SequenceMatcher.ratio()` (which is $O(L_1 \cdot L_2)$ for title lengths). As the batch grows, deduplication scales at $O(N^2 \cdot L^2)$.
* **Recommended Improvement:**  
  Maintain fast in-memory hash sets or lookup dictionaries for normalized DOIs, arXiv IDs, and URLs for $O(1)$ exact match lookups. Only evaluate `title_similarity` for items that pass a preliminary token-blocking or first-character indexing filter.

---

### [MED-06] In-Place Mutation of Input Dictionaries in Deserializer
* **Location:** `src/models.py` (lines 151–159)
* **Problem:**  
  `ResearchItem.from_dict(data)` uses `data.pop("score", None)` and `data.pop("intelligence", None)`. Calling `.pop()` mutates the caller's input dictionary in place. If `from_dict` is called on a cached dictionary, the cache loses `"score"` and `"intelligence"`.
* **Recommended Improvement:**  
  Make a shallow copy `data = dict(data)` before popping keys.

---

### [MED-07] Monolithic Architecture and Mixed Concerns in CLI
* **Location:** `src/cli.py` (818 lines)
* **Problem:**  
  `src/cli.py` handles argument parsing, interactive user wizards with direct console input, table rendering, opportunity scoring logic, supervisor campaign execution, event formatting, and Markdown export. It mixes presentation, orchestration, and business logic into a single monolithic file.
* **Recommended Improvement:**  
  Refactor `src/cli.py` into subcommands under a `src/commands/` module (e.g., `src/commands/pipeline.py`, `src/commands/events.py`, `src/commands/supervisors.py`, `src/commands/wizard.py`), keeping `src/cli.py` as a lightweight dispatcher.

---

### [MED-08] Inconsistency Between Transparency Reason and Applied PhD Score Boost
* **Location:** `src/ranking/scorer.py` (lines 226, 238)
* **Problem:**  
  In `_compute_phd_boost()`:
  ```python
  if item.item_type == ItemType.PHD_OPPORTUNITY.value:
      boost += 1.0 if not is_application_season else 1.2
      reasons.append(f"✓ PhD / Fellowship Opportunity (+{boost:.1f})")
  ...
  return min(1.0, boost)
  ```
  When `is_application_season` is `True`, `boost` is set to `1.2` and the audit log records `(+1.2)`. However, the return statement caps the boost at `1.0`. The logged transparent reasons do not match the actual arithmetic applied to the score.
* **Recommended Improvement:**  
  Align the boost calculation with the cap: either allow the boost to return `1.2` if configured, or cap `boost = min(1.0, ...)` before formatting the audit reason string.

---

## 4. Low Severity Findings

### [LOW-01] Unused Dependency in `requirements.txt`
* **Location:** `requirements.txt` (line 11)
* **Problem:**  
  `ebooklib>=0.18` is specified in `requirements.txt`. A repository-wide code search reveals zero imports or usages of `ebooklib` across the entire codebase.
* **Recommended Improvement:**  
  Remove `ebooklib` from `requirements.txt` to reduce install time and container footprint.

---

### [LOW-02] Dead and Malformed Code in Configuration Loader
* **Location:** `src/utils/config_loader.py` (lines 23–28)
* **Problem:**  
  The function `get_yaml_loader()` is never called anywhere in the codebase. Furthermore, its regex contains a syntax error:
  `loader.add_implicit_resolver('!env_var', re.compile(r'.*\$\{[^}^{]+(?:;-[^}]*)?\}.*'), None)`
  Notice the semicolon `(?:;-[^}]*)?` where a colon `(?::-[^}]*)` was intended.
* **Recommended Improvement:**  
  Remove `get_yaml_loader()` and its unused custom constructor, since `load_yaml_file()` already handles variable substitution via regex pre-substitution.

---

### [LOW-03] Duplicate Back-to-Back Import Blocks
* **Location:** `src/collectors/lab_recruitment.py` (lines 5–14 and lines 16–29)
* **Problem:**  
  The exact same symbols (`ResearcherProfile`, `PhDOpportunity`, `OpportunityScorer`, `ConfigManager`, `PoliteRequester`) are imported twice in consecutive import statements.
* **Recommended Improvement:**  
  Deduplicate imports in `src/collectors/lab_recruitment.py`.

---

### [LOW-04] Test Suite Coupled to Non-Module Ad-Hoc Scripts
* **Location:** `tests/test_existing_system_regression.py` (lines 13–18)
* **Problem:**  
  `test_existing_system_regression.py` manipulates `sys.path` dynamically to load `build_edge_curriculum.py` from `scratch/` or `scripts/`:
  ```python
  for p in [os.path.join(PROJECT_ROOT, "scratch"), os.path.join(PROJECT_ROOT, "scripts")]:
      if p not in sys.path:
          sys.path.insert(0, p)
  from build_edge_curriculum import create_edge_computing_workbook
  ```
  Unit tests should test packaged code under `src/` rather than depending on loose script files in scratch folders.
* **Recommended Improvement:**  
  Move `build_edge_curriculum.py` into a proper package namespace (e.g. `src/curriculum/`) or update the test to test the production module.

---

### [LOW-05] Redundant Full Test Runs in Scheduled Production Workflows
* **Location:** `.github/workflows/country_supervisor_intel.yml` (lines 50–52), `.github/workflows/hk_supervisor_daily_intel.yml` (lines 40–42)
* **Problem:**  
  Every daily scheduled run executes `pytest tests/ -v`. Running the full 239-test suite in a production cron job adds ~70 seconds of execution time and risks failing operational daily emails due to unrelated transient test flakiness. CI tests are already run on push and PR via `.github/workflows/tests.yml`.
* **Recommended Improvement:**  
  Remove the `pytest` step from scheduled cron workflows, keeping test execution dedicated to `tests.yml`.

---

### [LOW-06] Hardcoded Example Contact Addresses in Production Code
* **Location:** `src/utils/rate_limiter.py` (line 9), `src/collectors/crossref.py` (line 44), `src/cli.py` (line 104)
* **Problem:**  
  Hardcoded strings like `"mailto:obaro.moses.phd@example.com"` and `"user@example.com"` are embedded directly in HTTP headers and API parameters rather than reading from configuration or environment variables.
* **Recommended Improvement:**  
  Centralize API contact information in `config/profile.yaml` and pass it dynamically into `PoliteRequester` and `CrossrefCollector`.

---

### [LOW-07] Inconsistent Data Paths for Static Dashboards
* **Location:** `src/storage/dashboard_generator.py` vs `src/research_gaps/dashboard_generator.py`
* **Problem:**  
  General AlertMe dashboard data is saved to `docs/data.json`, whereas the PhD Research Gap dashboard data is saved to `docs/data/research_gap_data.json`.
* **Recommended Improvement:**  
  Standardize dashboard data outputs into `docs/data/` (e.g., `docs/data/alert_data.json` and `docs/data/research_gap_data.json`) and update the front-end fetch calls accordingly.

---

## 5. Summary of Top Improvements to Make First

To achieve the highest immediate impact on system stability, reliability, and maintainability, address the findings in the following prioritized order:

| Priority | Finding ID | Title | Impact |
|:---:|:---:|:---|:---|
| **1** | **CRIT-01** | Fix unordered set slicing in `StateManager` | Stops arbitrary loss of seen items and prevents duplicate alerts. |
| **2** | **CRIT-02** | Remove event state from `.gitignore` | Restores event deduplication across scheduled GitHub Actions runs. |
| **3** | **CRIT-03** | Fix inverted arguments in `src/cli.py:341` | Restores proper family/dependant support classification in CLI. |
| **4** | **HIGH-04** | Guard state persistence behind `email_sent` | Prevents suppressed alerts when email delivery fails. |
| **5** | **HIGH-01** | Consolidate `hk_supervisor_intel` into `src/supervisors` | Eliminates 1,500 lines of duplicated code and halts double-alerting of HK supervisors. |
| **6** | **HIGH-02** | Merge active events instead of overwriting `events.json` | Retains active upcoming conferences/events across runs. |
| **7** | **HIGH-03** | Use atomic writes in `src/supervisors/storage.py` | Eliminates state file corruption risk on interrupted runs. |
| **8** | **HIGH-05** | Safely parse `Retry-After` header in `PoliteRequester` | Prevents unhandled crashes when external APIs return HTTP dates. |
| **9** | **MED-04** | Add unit tests for `ResearchPipeline` and `ResearchGapPipeline` | Brings test coverage to the core orchestrators currently at 0%–13%. |
