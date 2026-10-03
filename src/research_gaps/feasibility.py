"""Provides evidence-based feasibility assessment for research problems using Claude Opus and OpenAlex."""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Set

from src.research_gaps.models import (
    ResearchProblem,
    ExtractedPaperInfo,
    SupervisorMatch,
    FeasibilityAssessment,
)
from src.research_gaps.llm_client import AnthropicClient, ModelNotFoundError, LLMExecutionError
from src.storage.state_manager import _atomic_write_json
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "research_gaps.yaml"

PROMPT_VERSION = "2026-10-assessor-v1"

OPENALEX_API_URL = "https://api.openalex.org/works"

ASSESSMENT_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "novelty": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Novelty rating based strictly on literature saturation.",
        },
        "novelty_evidence": {
            "type": "string",
            "description": "Rationale citing ONLY supplied evidence numbers or work IDs.",
        },
        "novelty_confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "feasibility": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Feasibility rating based on candidate methods and existing baselines.",
        },
        "feasibility_evidence": {
            "type": "string",
            "description": "Rationale citing ONLY supplied evidence numbers or work IDs.",
        },
        "feasibility_confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "publication_potential": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Publication potential rating based on known limitations and citations.",
        },
        "publication_evidence": {
            "type": "string",
            "description": "Rationale citing ONLY supplied evidence numbers or work IDs.",
        },
        "publication_confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "phd_depth": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "PhD depth rating based on unresolved research questions and thesis scope.",
        },
        "phd_depth_evidence": {
            "type": "string",
            "description": "Rationale citing ONLY supplied evidence numbers or work IDs.",
        },
        "phd_depth_confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
    },
    "required": [
        "novelty",
        "novelty_evidence",
        "novelty_confidence",
        "feasibility",
        "feasibility_evidence",
        "feasibility_confidence",
        "publication_potential",
        "publication_evidence",
        "publication_confidence",
        "phd_depth",
        "phd_depth_evidence",
        "phd_depth_confidence",
    ],
}

FORBIDDEN_EXTERNAL_CITATIONS = [
    "sec", "infocom", "mobicom", "neurips", "icml", "sigcomm", "nsdi", "osdi",
    "top-tier", "conference", "workshop"
]


class FeasibilityAssessor:
    """Provides evidence-based feasibility assessment for research problems."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        llm_client: Optional[AnthropicClient] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.config = config or self._load_config()
        self.cache_dir = cache_dir or (DATA_DIR / "assessment_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cache.json"
        self.openalex_cache_file = self.cache_dir / "openalex_cache.json"

        llm_cfg = self.config.get("llm", {})
        self.assessor_model = llm_cfg.get("assessor_model", "claude-opus-5-5")
        self.temperature = float(llm_cfg.get("temperature", 0.0))
        self.max_retries = int(llm_cfg.get("max_retries", 1))

        assess_cfg = self.config.get("assessment", {})
        self.min_source_count = int(assess_cfg.get("min_source_count", 2))
        self.high_saturation = int(assess_cfg.get("works_count_high_saturation", 100))
        self.low_saturation = int(assess_cfg.get("works_count_low_saturation", 15))

        self.llm_client = llm_client or AnthropicClient()
        self.cache = self._load_json(self.cache_file)
        self.openalex_cache = self._load_json(self.openalex_cache_file)

        # Telemetry
        self.llm_call_count = 0
        self.fallback_count = 0

    def _load_config(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            try:
                import yaml
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Could not load config from {CONFIG_FILE}: {e}")
        return {}

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache from {path}: {e}")
        return {}

    def _save_cache(self, path: Path, data: Dict[str, Any]) -> None:
        try:
            _atomic_write_json(path, data)
        except Exception as e:
            logger.warning(f"Failed to save cache to {path}: {e}")

    # ── OpenAlex Evidence Gathering ────────────────────────────────────

    def gather_openalex_evidence(
        self,
        problem: ResearchProblem,
        papers: List[ExtractedPaperInfo],
    ) -> Dict[str, Any]:
        """Gathers quantitative literature evidence from OpenAlex API or local papers."""
        query = problem.problem_statement
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]

        if query_hash in self.openalex_cache:
            return self.openalex_cache[query_hash]

        # Extract search query tokens (max 6 informative words)
        words = [w for w in re.findall(r"[a-zA-Z]{4,}", query) if w.lower() not in {"this", "that", "with", "from"}]
        search_terms = " ".join(words[:6]) if words else query[:60]

        evidence = {
            "works_count": 0,
            "total_citations": 0,
            "top_works": [],
        }

        try:
            import requests
            params = {
                "search": search_terms,
                "per_page": 5,
                "filter": "type:article|proceedings-article",
            }
            resp = requests.get(OPENALEX_API_URL, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                meta = data.get("meta", {})
                evidence["works_count"] = meta.get("count", 0)
                top_works = []
                for w in data.get("results", [])[:5]:
                    top_works.append({
                        "id": w.get("id", ""),
                        "title": w.get("title", ""),
                        "cited_by_count": w.get("cited_by_count", 0),
                        "year": w.get("publication_year", 0),
                    })
                evidence["top_works"] = top_works
                evidence["total_citations"] = sum(w["cited_by_count"] for w in top_works)
                self.openalex_cache[query_hash] = evidence
                self._save_cache(self.openalex_cache_file, self.openalex_cache)
                return evidence
        except Exception as e:
            logger.debug(f"OpenAlex API call skipped/failed: {e}")

        # Local evidence fallback when network/API is unavailable
        matching_papers = [p for p in papers if p.paper_id in problem.supporting_papers]
        evidence["works_count"] = len(problem.supporting_papers)
        local_top = []
        for p in matching_papers[:5]:
            local_top.append({
                "id": p.paper_id,
                "title": p.title,
                "cited_by_count": p.citation_count,
                "year": p.year,
            })
        evidence["top_works"] = local_top
        evidence["total_citations"] = sum(w["cited_by_count"] for w in local_top)
        return evidence

    # ── Strict Evidence Validation ─────────────────────────────────────

    def _validate_citations(
        self,
        assessment_dict: Dict[str, Any],
        allowed_work_ids: Set[str],
    ) -> bool:
        """Enforces that rationales cite only supplied evidence numbers or work IDs.

        Rejects outputs that cite unauthorized external venues, unlisted conferences, or unlisted IDs.
        """
        evidence_fields = [
            "novelty_evidence",
            "feasibility_evidence",
            "publication_evidence",
            "phd_depth_evidence",
        ]
        for field in evidence_fields:
            text = assessment_dict.get(field, "").lower()
            # Check for forbidden external venue mentions
            for forbidden in FORBIDDEN_EXTERNAL_CITATIONS:
                # Word boundary check
                if re.search(rf"\b{forbidden}\b", text):
                    logger.warning(
                        f"Validation failure in {field}: forbidden external venue '{forbidden}' cited."
                    )
                    return False

            # Check any work IDs cited in the text
            work_matches = re.findall(r"w\d{6,}", text)
            for wid in work_matches:
                full_wid = f"https://openalex.org/{wid.upper()}"
                if wid.upper() not in allowed_work_ids and full_wid not in allowed_work_ids:
                    logger.warning(
                        f"Validation failure in {field}: unlisted work ID '{wid}' cited."
                    )
                    return False

        return True

    # ── Opus LLM Assessment ────────────────────────────────────────────

    def _assess_with_llm(
        self,
        problem: ResearchProblem,
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Performs structured feasibility assessment with Claude Opus, validating evidence citations."""
        allowed_work_ids = {w["id"] for w in evidence.get("top_works", []) if w.get("id")}
        allowed_work_ids.update(problem.supporting_papers)

        system_prompt = (
            "You are an expert PhD thesis assessor in Computer Systems and Edge Computing.\n"
            "Evaluate the provided research problem across 4 core dimensions: Novelty, Feasibility, "
            "Publication Potential, and PhD Depth.\n\n"
            "STRICT RULES:\n"
            "1. Output valid ratings ('high', 'medium', 'low') and confidences ('high', 'medium', 'low').\n"
            "2. In each rationale, you may ONLY cite the numbers, counts, and work IDs provided in the Evidence section.\n"
            "3. DO NOT cite or mention external conferences or venues (e.g. NEVER mention SEC, INFOCOM, MobiCom, NeurIPS).\n"
            "4. DO NOT cite unlisted authors, papers, or external metrics.\n"
            "5. Any output citing unlisted sources or external venues will be rejected."
        )

        works_summary = "\n".join([
            f"  - Work ID: {w.get('id', 'N/A')}, Title: {w.get('title', 'N/A')}, Citations: {w.get('cited_by_count', 0)}, Year: {w.get('year', 0)}"
            for w in evidence.get("top_works", [])
        ]) or "  None"

        user_prompt = (
            f"--- Research Problem ---\n"
            f"Statement: {problem.problem_statement}\n"
            f"Research Area: {problem.research_area}\n"
            f"Candidate Methods ({len(problem.candidate_methods)}): {', '.join(problem.candidate_methods) if problem.candidate_methods else 'None'}\n"
            f"Existing Approaches ({len(problem.existing_approaches)}): {', '.join(problem.existing_approaches) if problem.existing_approaches else 'None'}\n\n"
            f"--- Supplied Quantitative Evidence ---\n"
            f"Supporting Papers in Corpus: {len(problem.supporting_papers)}\n"
            f"Total Related Works Count: {evidence.get('works_count', 0)}\n"
            f"Total Citations Across Top Works: {evidence.get('total_citations', 0)}\n"
            f"Known Limitations Count: {len(problem.known_limitations)}\n"
            f"Unresolved Questions Count: {len(problem.unresolved_questions)}\n"
            f"Top Related Works:\n{works_summary}\n\n"
            f"Evaluate Novelty, Feasibility, Publication Potential, and PhD Depth citing ONLY supplied evidence numbers or work IDs."
        )

        last_error = None
        for attempt in range(self.max_retries + 1):
            self.llm_call_count += 1
            try:
                result = self.llm_client.call_structured(
                    model=self.assessor_model,
                    system=system_prompt,
                    user_prompt=user_prompt,
                    tool_name="assess_phd_feasibility",
                    tool_schema=ASSESSMENT_TOOL_SCHEMA,
                    temperature=self.temperature,
                )
                if self._validate_citations(result, allowed_work_ids):
                    return result
                else:
                    last_error = "Validation error: model cited unsupplied evidence or forbidden external venues."
                    logger.warning(f"Rejecting Opus assessment output: {last_error} (attempt {attempt + 1})")
            except ModelNotFoundError:
                # 404 is a configuration error: must raise immediately per spec
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Opus assessment API call failed: {e}")

        raise LLMExecutionError(f"Opus assessment failed after {self.max_retries + 1} attempts: {last_error}")

    # ── Deterministic Rubric Fallback ──────────────────────────────────

    def _assess_deterministic(
        self,
        problem: ResearchProblem,
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deterministic evidence-based rubric assessment without hardcoded venue rationales."""
        works_count = evidence.get("works_count", len(problem.supporting_papers))
        total_citations = evidence.get("total_citations", 0)

        # Novelty rubric
        if works_count < self.low_saturation:
            novelty = "high"
            novelty_evidence = f"Low literature saturation: only {works_count} related works indexed in literature database."
        elif works_count < self.high_saturation:
            novelty = "medium"
            novelty_evidence = f"Moderate literature saturation: {works_count} related works indexed in literature database."
        else:
            novelty = "low"
            novelty_evidence = f"High literature saturation: {works_count} related works indexed in literature database."

        # Feasibility rubric
        has_methods = len(problem.candidate_methods) > 0
        has_approaches = len(problem.existing_approaches) > 0
        if has_methods and has_approaches:
            feasibility = "high"
            feasibility_evidence = (
                f"Candidate methods identified ({len(problem.candidate_methods)} methods) building on "
                f"{len(problem.existing_approaches)} existing baseline approaches."
            )
        elif has_methods or has_approaches:
            feasibility = "medium"
            feasibility_evidence = f"Partial methodology identified with {len(problem.candidate_methods)} candidate methods."
        else:
            feasibility = "low"
            feasibility_evidence = "Requires developing foundational methodology from scratch."

        # Publication potential rubric
        lim_count = len(problem.known_limitations)
        if lim_count >= 2:
            pub = "high"
            pub_evidence = f"High research gap significance validated by {lim_count} distinct literature claims ({total_citations} citations)."
        elif lim_count >= 1:
            pub = "medium"
            pub_evidence = f"Supported by {lim_count} validated literature limitation claim."
        else:
            pub = "low"
            pub_evidence = "Limited documented literature limitations."

        # PhD depth rubric
        q_count = len(problem.unresolved_questions)
        if q_count >= 2:
            phd = "high"
            phd_evidence = f"Multi-year thesis scope supported by {q_count} distinct unresolved research questions."
        elif q_count == 1:
            phd = "medium"
            phd_evidence = f"Focused scope supported by {q_count} unresolved research question."
        else:
            phd = "low"
            phd_evidence = "Narrow scope without documented unresolved research questions."

        return {
            "novelty": novelty,
            "novelty_evidence": novelty_evidence,
            "novelty_confidence": "high",
            "feasibility": feasibility,
            "feasibility_evidence": feasibility_evidence,
            "feasibility_confidence": "high",
            "publication_potential": pub,
            "publication_evidence": pub_evidence,
            "publication_confidence": "high",
            "phd_depth": phd,
            "phd_depth_evidence": phd_evidence,
            "phd_depth_confidence": "high",
        }

    # ── Secondary Heuristics (Data, Infra, Supervisors) ────────────────

    def _assess_significance(self, problem: ResearchProblem) -> Tuple[str, str]:
        lim_count = len(problem.known_limitations)
        if lim_count >= 2 or len(problem.evidence) >= 2:
            return "high", f"Validated by {lim_count} known limitations across publications."
        elif lim_count == 1:
            return "medium", "Addressed by at least one major limitation identified in recent work."
        return "low", "Limited evidence of critical system bottleneck."

    def _assess_data_availability(
        self,
        problem: ResearchProblem,
        papers: List[ExtractedPaperInfo],
    ) -> Tuple[str, str]:
        datasets_found = [
            p.dataset_testbed for p in papers
            if p.paper_id in problem.supporting_papers and p.dataset_testbed
        ]
        if datasets_found or problem.required_datasets:
            return "high", f"Public datasets/benchmarks identified in literature ({len(datasets_found)} mentioned)."
        return "medium", "May require synthetic workloads or simulated traces."

    def _assess_infrastructure(self, problem: ResearchProblem) -> Tuple[str, str]:
        infra = problem.infrastructure_requirements
        if infra:
            return "medium", f"Requires infrastructure: {', '.join(infra[:2])}."
        return "high", "Can be evaluated with standard GPU workstations and edge emulation testbeds."

    def _assess_supervisor_fit(
        self,
        problem: ResearchProblem,
        matches: List[SupervisorMatch],
    ) -> Tuple[str, str]:
        high_matches = [m for m in matches if m.match_score >= 0.2]
        if len(high_matches) >= 2:
            names = [m.name for m in high_matches[:3]]
            return "high", f"Strong alignment with {len(high_matches)} researchers ({', '.join(names)})."
        elif len(matches) >= 1:
            return "medium", f"Potential fit with {matches[0].name}."
        return "low", "No closely aligned supervisors identified in current database."

    # ── Assessment Orchestration ───────────────────────────────────────

    def assess(
        self,
        problem: ResearchProblem,
        papers: List[ExtractedPaperInfo],
        supervisor_matches: List[SupervisorMatch],
    ) -> FeasibilityAssessment:
        """Assesses feasibility of a research problem using quantitative evidence."""
        # 1. Check minimum source count
        source_count = len(problem.supporting_papers)
        if source_count < self.min_source_count:
            insufficient = f"Insufficient evidence: problem has {source_count} supporting paper(s), minimum required is {self.min_source_count}."
            significance, significance_evidence = self._assess_significance(problem)
            data_rating, data_evidence = self._assess_data_availability(problem, papers)
            infra_rating, infra_evidence = self._assess_infrastructure(problem)
            supervisor_rating, supervisor_evidence = self._assess_supervisor_fit(problem, supervisor_matches)

            return FeasibilityAssessment(
                problem_id=problem.id,
                novelty="unknown",
                novelty_evidence=insufficient,
                significance=significance,
                significance_evidence=significance_evidence,
                feasibility="unknown",
                feasibility_evidence=insufficient,
                data_availability=data_rating,
                data_evidence=data_evidence,
                infrastructure_requirements=infra_rating,
                infrastructure_evidence=infra_evidence,
                supervisor_fit=supervisor_rating,
                supervisor_fit_evidence=supervisor_evidence,
                publication_potential="unknown",
                publication_evidence=insufficient,
                phd_depth="unknown",
                phd_depth_evidence=insufficient,
            )

        # 2. Gather OpenAlex evidence
        evidence = self.gather_openalex_evidence(problem, papers)

        # 3. Check persistent cache for assessment
        cache_key = f"{problem.id}_{PROMPT_VERSION}"
        ratings = None
        if cache_key in self.cache:
            ratings = self.cache[cache_key]

        # 4. LLM assessment if available and not cached
        if ratings is None and self.llm_client.is_available():
            try:
                ratings = self._assess_with_llm(problem, evidence)
                self.cache[cache_key] = ratings
                self._save_cache(self.cache_file, self.cache)
            except ModelNotFoundError:
                # 404 is a configuration error: raise immediately per spec
                raise
            except Exception as e:
                self.fallback_count += 1
                logger.warning(
                    f"Opus assessment failed for '{problem.problem_statement[:40]}...': {e}. "
                    f"Using deterministic rubric fallback."
                )

        # 5. Deterministic fallback if still None
        if ratings is None:
            ratings = self._assess_deterministic(problem, evidence)
            self.cache[cache_key] = ratings
            self._save_cache(self.cache_file, self.cache)

        significance, significance_evidence = self._assess_significance(problem)
        data_rating, data_evidence = self._assess_data_availability(problem, papers)
        infra_rating, infra_evidence = self._assess_infrastructure(problem)
        supervisor_rating, supervisor_evidence = self._assess_supervisor_fit(problem, supervisor_matches)

        return FeasibilityAssessment(
            problem_id=problem.id,
            novelty=ratings.get("novelty", "medium"),
            novelty_evidence=ratings.get("novelty_evidence", ""),
            significance=significance,
            significance_evidence=significance_evidence,
            feasibility=ratings.get("feasibility", "medium"),
            feasibility_evidence=ratings.get("feasibility_evidence", ""),
            data_availability=data_rating,
            data_evidence=data_evidence,
            infrastructure_requirements=infra_rating,
            infrastructure_evidence=infra_evidence,
            supervisor_fit=supervisor_rating,
            supervisor_fit_evidence=supervisor_evidence,
            publication_potential=ratings.get("publication_potential", "medium"),
            publication_evidence=ratings.get("publication_evidence", ""),
            phd_depth=ratings.get("phd_depth", "medium"),
            phd_depth_evidence=ratings.get("phd_depth_evidence", ""),
        )

    def assess_batch(
        self,
        problems: List[ResearchProblem],
        papers: List[ExtractedPaperInfo],
        supervisor_map: Dict[str, List[SupervisorMatch]],
    ) -> Dict[str, FeasibilityAssessment]:
        """Batch assesses problems with summary logging."""
        logger.info(f"Assessing feasibility for {len(problems)} problems")
        results = {}
        for problem in problems:
            matches = supervisor_map.get(problem.id, [])
            try:
                results[problem.id] = self.assess(problem, papers, matches)
            except ModelNotFoundError:
                # 404 is a configuration error: abort batch immediately
                raise
            except Exception as e:
                logger.error(f"Failed to assess problem {problem.id}: {e}")
        return results
