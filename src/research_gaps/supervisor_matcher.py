"""Enhanced supervisor–research-problem matching module.

Improvements over the original:
- Loads all per-country professor JSON files from src/supervisors/data/
- Also reads data/supervisors.json and data/researcher_watchlist.json (legacy sources)
- Builds rich match explanations (why a professor matches a problem)
- Scores by: keyword overlap (research_interests), research_summary / edge_relevance
  text match, recent paper title overlap, and recruitment activity bonus
- Per-professor paper lookups are cached in data/professor_paper_cache.json
- Exports problem_professor_matches.json, .csv, .md to outputs/
- Keeps the original public API: match_supervisors(), match_all()
"""

import csv
import json
import re
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from src.research_gaps.models import ResearchProblem, SupervisorMatch, LinkStatus
from src.utils.logger import logger

# ── Paths ──────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = _REPO_ROOT / "data"
SUPERVISORS_DATA_DIR = _REPO_ROOT / "src" / "supervisors" / "data"
OUTPUTS_DIR = _REPO_ROOT / "outputs"
PROFESSOR_PAPER_CACHE_FILE = DATA_DIR / "professor_paper_cache.json"

# Countries to load (matches src/supervisors/data/ subdirectory names)
_COUNTRY_DIRS = [
    "hong_kong", "canada", "uk", "germany", "us", "japan", "sweden",
]

# Minimum composite score to include in results
_MIN_SCORE_THRESHOLD = 0.05

# Keyword categories mapped to score weight
_KEYWORD_WEIGHT = 0.45
_TEXT_MATCH_WEIGHT = 0.30
_PUB_RELEVANCE_WEIGHT = 0.20
_RECRUITMENT_BONUS_WEIGHT = 0.05


class SupervisorMatcher:
    """Matches research problems with potential supervisors.

    Data sources loaded (in priority order):
    1. Per-country professor JSON files (src/supervisors/data/<country>/professors.json)
    2. Legacy data/supervisors.json (runtime-discovered researchers)
    3. Legacy data/researcher_watchlist.json
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or DATA_DIR
        self._professor_cache: Dict[str, Any] = {}  # key → professor dict (loaded once)
        self._paper_cache: Dict[str, List[Dict]] = {}  # researcher_id → recent papers

    # ── Text helpers ───────────────────────────────────────────────────────────

    def _normalize_text(self, text: str) -> str:
        return text.lower().translate(str.maketrans("", "", string.punctuation)).strip()

    def _tokenize(self, text: str) -> Set[str]:
        """Return unique meaningful tokens (≥3 chars) from text."""
        words = re.findall(r"\b[a-z]{3,}\b", self._normalize_text(text))
        return set(words)

    def _tokens_from_list(self, items: List[str]) -> Set[str]:
        result: Set[str] = set()
        for item in items:
            if item:
                result.update(self._tokenize(item))
        return result

    # ── Data loading ───────────────────────────────────────────────────────────

    def _load_per_country_professors(self) -> Dict[str, Any]:
        """Load all professor records from src/supervisors/data/<country>/professors.json."""
        professors: Dict[str, Any] = {}
        for country_dir in _COUNTRY_DIRS:
            json_path = SUPERVISORS_DATA_DIR / country_dir / "professors.json"
            if not json_path.exists():
                continue
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    continue
                for prof in data:
                    if not isinstance(prof, dict):
                        continue
                    researcher_id = prof.get("researcher_id") or prof.get("name", "")
                    if researcher_id:
                        professors[researcher_id] = prof
            except Exception as exc:
                logger.error(f"Failed to load {json_path}: {exc}")
        return professors

    def _load_legacy_supervisors(self) -> Dict[str, Any]:
        """Load runtime-discovered supervisors from data/supervisors.json."""
        supervisors: Dict[str, Any] = {}
        sup_file = self.data_dir / "supervisors.json"
        if sup_file.exists():
            try:
                with open(sup_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    supervisors.update(data)
            except Exception as exc:
                logger.error(f"Error loading {sup_file}: {exc}")

        watchlist_file = self.data_dir / "researcher_watchlist.json"
        if watchlist_file.exists():
            try:
                with open(watchlist_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "researchers" in data:
                    researchers = data["researchers"]
                    if isinstance(researchers, dict):
                        supervisors.update(researchers)
            except Exception as exc:
                logger.error(f"Error loading {watchlist_file}: {exc}")
        return supervisors

    def load_supervisor_data(self) -> Dict[str, Any]:
        """Load all supervisor data from all sources, merging without duplication."""
        if self._professor_cache:
            return self._professor_cache

        all_profs = self._load_per_country_professors()
        # Legacy sources may add runtime-discovered researchers not in static files
        legacy = self._load_legacy_supervisors()
        for rid, data in legacy.items():
            if rid not in all_profs:
                all_profs[rid] = data

        self._professor_cache = all_profs
        logger.info(f"Loaded {len(all_profs)} supervisor profiles from all sources")
        return all_profs

    def _load_paper_cache(self) -> Dict[str, List[Dict]]:
        """Load the persistent per-professor paper cache."""
        if PROFESSOR_PAPER_CACHE_FILE.exists():
            try:
                with open(PROFESSOR_PAPER_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_paper_cache(self, cache: Dict[str, List[Dict]]) -> None:
        """Persist the paper cache atomically."""
        try:
            import os, tempfile
            PROFESSOR_PAPER_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(
                dir=PROFESSOR_PAPER_CACHE_FILE.parent, prefix="ppcache_", suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            os.replace(tmp, PROFESSOR_PAPER_CACHE_FILE)
        except Exception as exc:
            logger.warning(f"Could not save professor paper cache: {exc}")

    # ── Scoring helpers ────────────────────────────────────────────────────────

    def _jaccard(self, set_a: Set[str], set_b: Set[str]) -> float:
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0

    def _overlap_ratio(self, problem_tokens: Set[str], text_tokens: Set[str]) -> float:
        """Fraction of problem tokens that appear in text_tokens."""
        if not problem_tokens or not text_tokens:
            return 0.0
        return len(problem_tokens & text_tokens) / len(problem_tokens)

    def _compute_keyword_score(
        self,
        problem_keywords: List[str],
        supervisor_areas: List[str],
        supervisor_summary: str,
        supervisor_edge_rel: str,
        supervisor_trajectory: str,
    ) -> Tuple[float, List[str]]:
        """
        Compute keyword match score and return matching keyword phrases.
        Uses Jaccard on research_interests PLUS overlap on free-text bio fields.
        """
        prob_tokens = self._tokens_from_list(problem_keywords)

        # Part 1: Jaccard over research_interests list
        sup_area_tokens = self._tokens_from_list(supervisor_areas)
        jaccard = self._jaccard(prob_tokens, sup_area_tokens)

        # Part 2: Overlap over text bio fields
        bio_text = f"{supervisor_summary} {supervisor_edge_rel} {supervisor_trajectory}"
        bio_tokens = self._tokenize(bio_text)
        bio_overlap = self._overlap_ratio(prob_tokens, bio_tokens) * 0.4

        combined = min(1.0, jaccard + bio_overlap)

        # Collect human-readable matching phrases from research_interests
        matching_phrases: List[str] = []
        prob_norm = set(self._normalize_text(k) for k in problem_keywords)
        for area in supervisor_areas:
            area_norm = self._normalize_text(area)
            # Substring match (e.g. "Edge AI" matches "edge" keyword)
            if any(kw in area_norm or area_norm in kw for kw in prob_norm):
                matching_phrases.append(area)

        return combined, matching_phrases

    def _compute_publication_score(
        self, problem: ResearchProblem, publications: List[Dict]
    ) -> Tuple[float, List[Dict]]:
        """Score publication relevance; return score + matched publications."""
        if not publications:
            return 0.0, []

        prob_tokens = self._tokens_from_list(
            list(problem.supervisor_keywords)
            + [problem.research_area]
            + problem.limitation_texts()[:3]
            + problem.question_texts()[:3]
        )

        matching: List[Dict] = []
        total_score = 0.0

        current_year = datetime.now().year

        for pub in publications:
            if not isinstance(pub, dict):
                continue
            title = pub.get("title", "") or pub.get("name", "")
            topics = pub.get("topics", []) or pub.get("keywords", []) or []
            abstract = pub.get("abstract", "") or pub.get("research_problem", "") or ""
            pub_year = pub.get("year") or pub.get("publication_year") or 0

            pub_tokens = self._tokenize(f"{title} {abstract} {' '.join(topics)}")
            overlap = len(prob_tokens & pub_tokens)
            if overlap <= 0:
                continue

            # Recency bonus: papers from last 3 years get 1.2×
            try:
                year_int = int(pub_year)
                recency_mult = 1.2 if (current_year - year_int) <= 3 else 1.0
            except (ValueError, TypeError):
                recency_mult = 1.0

            score = min(1.0, (overlap / max(4, len(prob_tokens) * 0.3))) * recency_mult
            matching.append({**pub, "_relevance_score": round(score, 3)})
            total_score += score

        if not matching:
            return 0.0, []

        matching.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
        avg = total_score / len(matching)
        return min(1.0, avg), matching[:5]

    def _recruitment_bonus(self, prof_data: Dict) -> float:
        """Return small bonus for actively-recruiting professors."""
        recruitment = prof_data.get("recruitment") or {}
        if not isinstance(recruitment, dict):
            return 0.0
        status = str(recruitment.get("status", "")).upper()
        bonus_map = {
            "CONFIRMED_ACTIVE": 1.0,
            "STRONG_EVIDENCE": 0.75,
            "POSSIBLE": 0.4,
            "UNKNOWN": 0.0,
            "NOT_CURRENTLY_RECRUITING": 0.0,
            "RECRUITMENT_STALE": 0.1,
        }
        return bonus_map.get(status, 0.0)

    def _build_explanation(
        self,
        prof_data: Dict,
        problem: ResearchProblem,
        keyword_score: float,
        pub_score: float,
        matching_keywords: List[str],
        matching_pubs: List[Dict],
    ) -> str:
        """Build a human-readable match explanation string."""
        parts: List[str] = []

        name = prof_data.get("name", "This professor")
        uni = prof_data.get("university", "their institution")

        if matching_keywords:
            kws = ", ".join(f'"{k}"' for k in matching_keywords[:4])
            parts.append(
                f"{name} ({uni}) directly researches {kws}, which closely aligns with "
                f'the problem: "{problem.problem_statement[:100]}..."'
            )
        else:
            parts.append(
                f"{name} ({uni}) has broadly relevant expertise in "
                f"{problem.research_area} that partially overlaps this research problem."
            )

        if matching_pubs:
            top = matching_pubs[0]
            pub_title = top.get("title") or top.get("name", "")
            pub_year = top.get("year", "")
            if pub_title:
                parts.append(
                    f"Recent publication evidence: '{pub_title[:80]}' ({pub_year}) "
                    f"demonstrates active work in this space."
                )

        summary = prof_data.get("research_summary", "") or prof_data.get("edge_relevance", "")
        if summary:
            parts.append(f"Research bio: {summary[:140].strip()}...")

        recruitment = prof_data.get("recruitment") or {}
        rec_status = str(recruitment.get("status", "")).upper()
        rec_text = recruitment.get("evidence_text", "")
        if rec_status in ("CONFIRMED_ACTIVE", "STRONG_EVIDENCE") and rec_text:
            parts.append(f"Actively recruiting: {rec_text[:120].strip()}...")

        if prof_data.get("potential_phd_topics"):
            topics_str = "; ".join(prof_data["potential_phd_topics"][:2])
            parts.append(f"Suggested PhD topics in their lab: {topics_str}.")

        return " | ".join(parts)

    # ── Core matching ──────────────────────────────────────────────────────────

    def _get_professor_publications(self, researcher_id: str, prof_data: Dict) -> List[Dict]:
        """
        Return publications for a professor.
        Prefers: in-profile 'publications' (if list of dicts), else cached papers.
        Does NOT make live network calls — that is reserved for future enhancement
        to avoid slowing down the synchronous pipeline.
        """
        # 1. Inline publications in profile (if they are dicts, not just IDs)
        inline = prof_data.get("recent_papers") or prof_data.get("publications") or []
        if isinstance(inline, list) and inline and isinstance(inline[0], dict):
            return inline

        # 2. Paper cache (filled by prior run or external pre-fetch)
        file_cache = self._load_paper_cache()
        if researcher_id in file_cache:
            return file_cache[researcher_id]

        return []

    def match_supervisors(
        self,
        problem: ResearchProblem,
        max_matches: int = 10,
    ) -> List[SupervisorMatch]:
        """Match a single research problem against all supervisor profiles."""
        supervisors = self.load_supervisor_data()
        if not supervisors:
            logger.warning("No supervisor data found for matching.")
            return []

        # Build problem search terms
        problem_keywords: List[str] = list(problem.supervisor_keywords) or []
        if problem.research_area:
            problem_keywords.append(problem.research_area)
        # Add first 3 cluster tokens
        if problem.problem_cluster:
            problem_keywords.extend(problem.problem_cluster.split()[:3])

        matches: List[Tuple[float, SupervisorMatch]] = []

        for researcher_id, data in supervisors.items():
            if not isinstance(data, dict):
                continue

            supervisor_areas = (
                data.get("research_interests")
                or data.get("research_areas")
                or data.get("topics")
                or []
            )
            summary = data.get("research_summary", "") or ""
            edge_rel = data.get("edge_relevance", "") or ""
            trajectory = data.get("research_trajectory", "") or ""

            # ── Score 1: keyword match ─────────────────────────────────
            kw_score, matching_keywords = self._compute_keyword_score(
                problem_keywords, supervisor_areas, summary, edge_rel, trajectory
            )

            # ── Score 2: publication relevance ─────────────────────────
            publications = self._get_professor_publications(researcher_id, data)
            pub_score, matching_pubs = self._compute_publication_score(problem, publications)

            # ── Score 3: recruitment activity bonus ────────────────────
            rec_bonus = self._recruitment_bonus(data)

            # ── Composite score ────────────────────────────────────────
            if publications:
                composite = (
                    kw_score * _KEYWORD_WEIGHT
                    + pub_score * _PUB_RELEVANCE_WEIGHT
                    + rec_bonus * _RECRUITMENT_BONUS_WEIGHT
                    # text match already folded into kw_score via bio_overlap
                )
            else:
                # No publications: rely on keyword + text match
                composite = kw_score * (_KEYWORD_WEIGHT + _PUB_RELEVANCE_WEIGHT) + rec_bonus * _RECRUITMENT_BONUS_WEIGHT

            composite = min(1.0, composite)

            if composite < _MIN_SCORE_THRESHOLD:
                continue

            explanation = self._build_explanation(
                data, problem, kw_score, pub_score, matching_keywords, matching_pubs
            )

            # Strip internal _relevance_score before storing
            clean_pubs = [{k: v for k, v in p.items() if k != "_relevance_score"} for p in matching_pubs]

            match = SupervisorMatch(
                name=data.get("name", "Unknown"),
                institution=data.get("university", data.get("institution", "Unknown")),
                country=data.get("country", ""),
                relevant_research_areas=supervisor_areas,
                relevant_publications=clean_pubs,
                matching_keywords=matching_keywords,
                profile_url=(
                    data.get("official_profile_url", "")
                    or data.get("personal_website", "")
                    or data.get("profile_url", "")
                ),
                google_scholar_url=(
                    data.get("google_scholar", "")
                    or data.get("google_scholar_url", "")
                ),
                semantic_scholar_url=data.get("semantic_scholar_url", "") or data.get("semantic_scholar", ""),
                link_status=LinkStatus.UNKNOWN,
                match_score=round(composite, 4),
                match_explanation=explanation,
            )
            matches.append((composite, match))

        matches.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in matches[:max_matches]]

    def match_all(
        self,
        problems: List[ResearchProblem],
        max_matches: int = 10,
    ) -> Dict[str, List[SupervisorMatch]]:
        """Match all research problems against supervisor dataset."""
        logger.info(f"Matching supervisors for {len(problems)} problems")
        result: Dict[str, List[SupervisorMatch]] = {}
        for p in problems:
            result[p.id] = self.match_supervisors(p, max_matches=max_matches)
        return result

    # ── Export helpers ─────────────────────────────────────────────────────────

    def export_matches(
        self,
        problems: List[ResearchProblem],
        supervisor_map: Dict[str, List[SupervisorMatch]],
    ) -> None:
        """Export match results to JSON, CSV, and Markdown in outputs/."""
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

        # ── JSON ────────────────────────────────────────────────────────
        json_rows = []
        for prob in problems:
            matches = supervisor_map.get(prob.id, [])
            prob_entry = {
                "problem_id": prob.id,
                "problem_statement": prob.problem_statement,
                "research_area": prob.research_area,
                "problem_cluster": prob.problem_cluster,
                "frequency": prob.frequency,
                "status": prob.status,
                "supervisor_keywords": prob.supervisor_keywords,
                "matches": [],
            }
            for m in matches:
                match_dict = m.to_dict()
                match_dict["match_explanation"] = m.match_explanation
                prob_entry["matches"].append(match_dict)
            json_rows.append(prob_entry)

        try:
            import os, tempfile
            out_json = OUTPUTS_DIR / "problem_professor_matches.json"
            fd, tmp = tempfile.mkstemp(dir=OUTPUTS_DIR, prefix="ppm_", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(json_rows, f, indent=2, ensure_ascii=False)
            os.replace(tmp, out_json)
            logger.info(f"Exported problem-professor matches → {out_json}")
        except Exception as exc:
            logger.error(f"Failed to write JSON matches: {exc}")

        # ── CSV ─────────────────────────────────────────────────────────
        csv_rows = []
        for prob in problems:
            for m in supervisor_map.get(prob.id, []):
                csv_rows.append({
                    "problem_id": prob.id,
                    "problem_statement": prob.problem_statement[:120],
                    "research_area": prob.research_area,
                    "status": prob.status,
                    "professor_name": m.name,
                    "institution": m.institution,
                    "country": m.country,
                    "match_score": m.match_score,
                    "matching_keywords": "; ".join(m.matching_keywords[:5]),
                    "profile_url": m.profile_url,
                    "google_scholar_url": m.google_scholar_url,
                    "match_explanation": m.match_explanation[:200],
                })

        if csv_rows:
            try:
                out_csv = OUTPUTS_DIR / "problem_professor_matches.csv"
                with open(out_csv, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_rows)
                logger.info(f"Exported problem-professor matches → {out_csv}")
            except Exception as exc:
                logger.error(f"Failed to write CSV matches: {exc}")

        # ── Markdown ────────────────────────────────────────────────────
        self._write_markdown_report(problems, supervisor_map)

    def _write_markdown_report(
        self,
        problems: List[ResearchProblem],
        supervisor_map: Dict[str, List[SupervisorMatch]],
    ) -> None:
        """Write a structured Markdown report to outputs/problem_professor_matches.md."""
        lines = [
            "# Professor–Research Problem Matching Report",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            f"**Total research problems:** {len(problems)}  ",
            f"**Total unique matches:** {sum(len(v) for v in supervisor_map.values())}  ",
            "",
            "---",
            "",
        ]

        # Group problems by research area
        by_area: Dict[str, List[ResearchProblem]] = {}
        for prob in problems:
            by_area.setdefault(prob.research_area or "Uncategorized", []).append(prob)

        for area, area_problems in sorted(by_area.items()):
            lines.append(f"## {area}")
            lines.append("")
            for prob in area_problems:
                matches = supervisor_map.get(prob.id, [])
                lines.append(f"### {prob.problem_statement[:120]}")
                lines.append("")
                lines.append(f"- **Status:** `{prob.status}`")
                lines.append(f"- **Cluster:** {prob.problem_cluster or 'N/A'}")
                lines.append(f"- **Frequency:** {prob.frequency}")
                lines.append(f"- **Keywords:** {', '.join(prob.supervisor_keywords[:8]) or 'N/A'}")
                lines.append("")

                if not matches:
                    lines.append("*No supervisor matches found for this problem.*")
                    lines.append("")
                    continue

                lines.append(f"**Top {len(matches)} Matched Professors:**")
                lines.append("")
                lines.append("| Professor | Institution | Country | Score | Matching Keywords |")
                lines.append("|-----------|-------------|---------|-------|-------------------|")
                for m in matches:
                    kws = ", ".join(m.matching_keywords[:3]) or "—"
                    profile = f"[Profile]({m.profile_url})" if m.profile_url else "—"
                    lines.append(
                        f"| [{m.name}]({m.profile_url}) | {m.institution} | {m.country} "
                        f"| {m.match_score:.3f} | {kws} |"
                    )
                lines.append("")

                # Detailed cards for top 3
                for i, m in enumerate(matches[:3]):
                    explanation = m.match_explanation
                    lines.append(f"#### {i + 1}. {m.name}")
                    lines.append("")
                    lines.append(f"- **Institution:** {m.institution} ({m.country})")
                    lines.append(f"- **Match Score:** {m.match_score:.4f}")
                    lines.append(f"- **Research Areas:** {', '.join(m.relevant_research_areas[:5])}")
                    if m.matching_keywords:
                        lines.append(f"- **Matching Keywords:** {', '.join(m.matching_keywords)}")
                    if m.profile_url:
                        lines.append(f"- **Profile:** [{m.profile_url}]({m.profile_url})")
                    if m.google_scholar_url:
                        lines.append(f"- **Google Scholar:** [{m.google_scholar_url}]({m.google_scholar_url})")
                    if m.relevant_publications:
                        lines.append("- **Relevant Publications:**")
                        for pub in m.relevant_publications[:3]:
                            pub_title = pub.get("title") or pub.get("name", "")
                            pub_year = pub.get("year", "")
                            pub_url = pub.get("doi_or_url") or pub.get("url", "")
                            if pub_title:
                                if pub_url:
                                    lines.append(f"  - [{pub_title[:80]} ({pub_year})]({pub_url})")
                                else:
                                    lines.append(f"  - {pub_title[:80]} ({pub_year})")
                    if explanation:
                        lines.append(f"- **Why this match:** {explanation[:300]}")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # ── Precision / Coverage Stats ─────────────────────────────────
        total_probs = len(problems)
        matched_probs = sum(1 for pid, ms in supervisor_map.items() if ms)
        high_conf = sum(
            1 for ms in supervisor_map.values() if any(m.match_score >= 0.35 for m in ms)
        )
        low_conf = sum(
            1 for ms in supervisor_map.values() if ms and all(m.match_score < 0.2 for m in ms)
        )

        lines += [
            "## Matching Statistics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total problems | {total_probs} |",
            f"| Problems with ≥1 match | {matched_probs} ({100 * matched_probs // max(1, total_probs)}%) |",
            f"| High-confidence matches (≥0.35) | {high_conf} |",
            f"| Low-confidence matches (<0.20) | {low_conf} |",
            f"| Total match pairs | {sum(len(v) for v in supervisor_map.values())} |",
            "",
            "> **Note:** Low-confidence matches (<0.20) may indicate a research problem "
            "not yet well-represented in the professor dataset. Consider adding more "
            "professors or refining problem keywords.",
            "",
        ]

        try:
            out_md = OUTPUTS_DIR / "problem_professor_matches.md"
            with open(out_md, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            logger.info(f"Exported problem-professor matches → {out_md}")
        except Exception as exc:
            logger.error(f"Failed to write Markdown matches: {exc}")
