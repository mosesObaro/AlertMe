"""Manages the persistent research problem tracker with two-stage semantic problem grouping."""

import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Tuple

from src.research_gaps.models import (
    ResearchProblem,
    ExtractedPaperInfo,
    ProblemStatus,
    EvidenceClaim,
    Confidence,
)
from src.research_gaps.llm_client import AnthropicClient, ModelNotFoundError, LLMExecutionError
from src.storage.state_manager import _atomic_write_json
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "research_gaps.yaml"

PROMPT_VERSION = "2026-10-grouper-v1"

GROUPING_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "matching_problem_id": {
            "type": ["string", "null"],
            "description": (
                "The exact ID of the existing candidate problem that addresses the same core technical "
                "research bottleneck, or null if this is a distinct research problem."
            ),
        },
        "reasoning": {
            "type": "string",
            "description": "Brief explanation of whether the incoming problem matches an existing candidate or addresses a distinct problem.",
        },
    },
    "required": ["matching_problem_id", "reasoning"],
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "as", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "that", "this", "these", "those", "such", "not", "can", "could", "will", "would",
    "paper", "propose", "presents", "approach", "system", "method", "framework", "work"
}


def extract_problem_tokens(
    statement: str,
    keywords: Optional[List[str]] = None,
    candidate_methods: Optional[List[str]] = None,
    research_area: Optional[str] = None,
) -> Set[str]:
    """Extracts informative domain tokens from a problem statement, keywords, and methods."""
    tokens: Set[str] = set()
    components = [statement or ""]
    if keywords:
        components.extend(keywords)
    if candidate_methods:
        components.extend(candidate_methods)
    if research_area:
        components.append(research_area)

    for comp in components:
        words = re.findall(r"[a-zA-Z]{3,}", comp.lower())
        tokens.update(w for w in words if w not in STOP_WORDS)
    return tokens


def compute_token_jaccard(tokens1: Set[str], tokens2: Set[str]) -> float:
    """Computes Jaccard similarity between two token sets."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    return intersection / union if union > 0 else 0.0


class ProblemTracker:
    """Manages persistent research problems with two-stage semantic grouping."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None,
        llm_client: Optional[AnthropicClient] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.problems_file = self.data_dir / "research_problems.json"

        self.config = config or self._load_config()
        llm_cfg = self.config.get("llm", {})
        self.grouping_model = llm_cfg.get("grouping_model", "claude-sonnet-5-5")
        self.temperature = float(llm_cfg.get("temperature", 0.0))
        self.max_retries = int(llm_cfg.get("max_retries", 1))

        grp_cfg = self.config.get("grouping", {})
        self.shortlist_max = int(grp_cfg.get("shortlist_max", 5))
        self.shortlist_threshold = float(grp_cfg.get("shortlist_threshold", 0.20))
        self.fallback_threshold = float(grp_cfg.get("fallback_threshold", 0.28))

        self.llm_client = llm_client or AnthropicClient()
        self.cache_dir = cache_dir or (self.data_dir / "grouping_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cache.json"
        self.cache = self._load_cache()

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

    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load grouping cache: {e}")
        return {}

    def _save_cache(self) -> None:
        try:
            _atomic_write_json(self.cache_file, self.cache)
        except Exception as e:
            logger.warning(f"Could not save grouping cache: {e}")

    def _pair_cache_key(self, stmt: str, cand_id: str) -> str:
        pair_str = f"{stmt.strip().lower()}:::{cand_id.strip()}"
        pair_hash = hashlib.sha256(pair_str.encode("utf-8")).hexdigest()[:16]
        return f"{pair_hash}_{PROMPT_VERSION}"

    def load_problems(self) -> List[ResearchProblem]:
        """Load problems from the JSON data file."""
        if not self.problems_file.exists():
            return []
        try:
            with open(self.problems_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [ResearchProblem.from_dict(p) for p in data]
        except Exception as e:
            logger.error(f"Failed to load problems from {self.problems_file}: {e}")
            return []

    def save_problems(self, problems: List[ResearchProblem]) -> None:
        """Save the list of problems to the JSON data file using an atomic write."""
        try:
            data = [p.to_dict() for p in problems]
            _atomic_write_json(self.problems_file, data)
        except Exception as e:
            logger.error(f"Failed to save problems to {self.problems_file}: {e}")

    # ── Stage 1: Shortlisting ──────────────────────────────────────────

    def shortlist_candidates(
        self,
        incoming_tokens: Set[str],
        incoming_stmt: str,
        candidate_problems: List[ResearchProblem],
    ) -> List[Tuple[ResearchProblem, float]]:
        """Shortlists up to shortlist_max existing problems using keyword overlap Jaccard."""
        scored: List[Tuple[ResearchProblem, float]] = []
        for p in candidate_problems:
            if incoming_stmt.strip().lower() == p.problem_statement.strip().lower():
                scored.append((p, 1.0))
                continue

            p_tokens = extract_problem_tokens(
                statement=p.problem_statement,
                keywords=p.supervisor_keywords,
                candidate_methods=p.candidate_methods,
                research_area=p.research_area,
            )
            sim = compute_token_jaccard(incoming_tokens, p_tokens)
            if sim >= self.shortlist_threshold:
                scored.append((p, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[: self.shortlist_max]

    # ── Stage 2: Claude Sonnet Semantic Matching & Cache ───────────────

    def _match_with_llm(
        self,
        statement: str,
        research_area: str,
        candidate_methods: List[str],
        keywords: List[str],
        shortlist: List[Tuple[ResearchProblem, float]],
    ) -> Optional[ResearchProblem]:
        """Calls Claude Sonnet to determine if the incoming problem matches an existing candidate."""
        # 1. Check pairwise cache for decisions
        for cand, _ in shortlist:
            key = self._pair_cache_key(statement, cand.id)
            if key in self.cache and self.cache[key].get("matches") is True:
                logger.debug(f"Grouping cache hit (match): '{statement[:30]}' -> {cand.id}")
                return cand

        # If all candidates have cached non-match decisions, we know none match
        all_cached_no_match = all(
            (self._pair_cache_key(statement, cand.id) in self.cache)
            and (self.cache[self._pair_cache_key(statement, cand.id)].get("matches") is False)
            for cand, _ in shortlist
        )
        if all_cached_no_match and shortlist:
            logger.debug(f"Grouping cache hit (all distinct): '{statement[:30]}'")
            return None

        # 2. Construct LLM prompt
        system_prompt = (
            "You are an expert PhD research advisor in Edge Computing and Computer Systems.\n"
            "Your task is to determine whether a newly extracted research problem addresses the exact same "
            "underlying technical research bottleneck as one of the candidate problems already tracked, "
            "or represents a distinct problem.\n\n"
            "Rules:\n"
            "- Return matching_problem_id with the exact ID if they describe the same core technical challenge or trade-off.\n"
            "- Return null if they address different bottlenecks, different system layers, or distinct problems.\n"
            "- If multiple could match, select the single best matching candidate."
        )

        candidates_text = "\n\n".join(
            [
                f"Candidate {idx + 1} [ID: {cand.id}]:\n"
                f"  Problem Statement: {cand.problem_statement}\n"
                f"  Candidate Methods: {', '.join(cand.candidate_methods) if cand.candidate_methods else 'None'}\n"
                f"  Area: {cand.research_area}"
                for idx, (cand, _) in enumerate(shortlist)
            ]
        )

        user_prompt = (
            f"--- New Research Problem ---\n"
            f"Statement: {statement}\n"
            f"Research Area: {research_area}\n"
            f"Candidate Methods: {', '.join(candidate_methods) if candidate_methods else 'None'}\n"
            f"Keywords: {', '.join(keywords) if keywords else 'None'}\n\n"
            f"--- Candidate Existing Problems ---\n"
            f"{candidates_text}\n\n"
            f"Does the new problem match any candidate? Return matching_problem_id or null."
        )

        self.llm_call_count += 1
        result = None
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = self.llm_client.call_structured(
                    model=self.grouping_model,
                    system=system_prompt,
                    user_prompt=user_prompt,
                    tool_name="match_research_problem",
                    tool_schema=GROUPING_TOOL_SCHEMA,
                    temperature=self.temperature,
                )
                break
            except ModelNotFoundError:
                # 404 is a configuration error: must raise immediately
                raise
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.info(f"Retrying grouping LLM call after error: {e}")

        if result is None:
            raise LLMExecutionError(f"Grouping LLM call failed after {self.max_retries + 1} attempts: {last_error}")

        matched_id = result.get("matching_problem_id")
        reasoning = result.get("reasoning", "")

        # Save pairwise decisions into cache
        for cand, _ in shortlist:
            key = self._pair_cache_key(statement, cand.id)
            is_match = (matched_id == cand.id)
            self.cache[key] = {
                "matches": is_match,
                "reasoning": reasoning if is_match else "Distinct problem",
                "prompt_version": PROMPT_VERSION,
            }
        self._save_cache()

        if matched_id:
            for cand, _ in shortlist:
                if cand.id == matched_id:
                    return cand

        return None

    # ── Core Grouping Entrypoints ──────────────────────────────────────

    def find_matching_problem(
        self,
        problem_statement: str,
        research_area: str,
        paper_info: Optional[ExtractedPaperInfo] = None,
    ) -> Tuple[Optional[ResearchProblem], bool]:
        """Matches against existing problems using two-stage semantic grouping.

        Stage 1: Shortlists up to 5 candidates via keyword Jaccard overlap.
        Stage 2: When LLM available, calls Claude Sonnet to evaluate identity.
                 Fallback (no key / error): Matches if top candidate Jaccard >= fallback_threshold.

        Returns: (matching_problem, used_fallback)
        """
        problems = self.load_problems()
        area_problems = [p for p in problems if p.research_area.lower() == research_area.lower()]
        candidate_pool = area_problems if area_problems else problems

        if not candidate_pool:
            return None, False

        # Gather incoming tokens
        cand_methods = paper_info.candidate_methods if paper_info else []
        keywords = paper_info.keywords if paper_info else []
        incoming_tokens = extract_problem_tokens(
            statement=problem_statement,
            keywords=keywords,
            candidate_methods=cand_methods,
            research_area=research_area,
        )

        # Stage 1: Shortlist
        shortlist = self.shortlist_candidates(
            incoming_tokens=incoming_tokens,
            incoming_stmt=problem_statement,
            candidate_problems=candidate_pool,
        )

        if not shortlist:
            return None, False

        # If there's an exact string match, merge directly without burning LLM call
        if shortlist[0][1] >= 0.999:
            return shortlist[0][0], False

        # Stage 2: Semantic evaluation
        if self.llm_client.is_available():
            try:
                matched = self._match_with_llm(
                    statement=problem_statement,
                    research_area=research_area,
                    candidate_methods=cand_methods,
                    keywords=keywords,
                    shortlist=shortlist,
                )
                return matched, False
            except ModelNotFoundError:
                # 404 is a configuration error: must raise immediately
                raise
            except Exception as e:
                self.fallback_count += 1
                logger.warning(
                    f"Grouping LLM call failed for problem '{problem_statement[:40]}...': {e}. "
                    f"Falling back to shortlist threshold ({self.fallback_threshold})."
                )

        # Fallback mode (no LLM key available, or transient API failure)
        used_fallback = True
        top_cand, top_sim = shortlist[0]
        if top_sim >= self.fallback_threshold:
            logger.info(
                f"Fallback matched '{problem_statement[:30]}' -> '{top_cand.problem_statement[:30]}' (sim={top_sim:.3f})"
            )
            return top_cand, used_fallback

        return None, used_fallback

    def find_existing_problem(
        self,
        problem_statement: str,
        research_area: str,
        paper_info: Optional[ExtractedPaperInfo] = None,
    ) -> Optional[ResearchProblem]:
        """Backward-compatible query method."""
        matched, _ = self.find_matching_problem(
            problem_statement=problem_statement,
            research_area=research_area,
            paper_info=paper_info,
        )
        return matched

    @staticmethod
    def _merge_claims(target: List[EvidenceClaim], incoming: List[EvidenceClaim]) -> None:
        """Append claims not already present (same paper and same text); provenance is preserved."""
        seen = {(c.paper_id, c.claim_text) for c in target}
        for claim in incoming:
            key = (claim.paper_id, claim.claim_text)
            if key not in seen:
                target.append(claim)
                seen.add(key)

    def merge_evidence(
        self,
        existing: ResearchProblem,
        paper: ExtractedPaperInfo,
        mark_low_confidence: bool = False,
    ) -> ResearchProblem:
        """Merge new evidence into an existing problem without duplicating."""
        existing.last_updated = datetime.now().isoformat()

        if paper.paper_id not in existing.supporting_papers:
            existing.supporting_papers.append(paper.paper_id)
            existing.frequency += 1

        self._merge_claims(existing.known_limitations, paper.limitations)
        self._merge_claims(existing.unresolved_questions, paper.future_work)

        # Merge candidate methods and existing approaches without duplicates
        for m in paper.candidate_methods:
            if m and m not in existing.candidate_methods:
                existing.candidate_methods.append(m)
        if paper.proposed_approach and paper.proposed_approach not in existing.candidate_methods:
            existing.candidate_methods.append(paper.proposed_approach)

        for a in paper.existing_approaches:
            if a and a not in existing.existing_approaches:
                existing.existing_approaches.append(a)

        for kw in paper.keywords:
            if kw and kw not in existing.supervisor_keywords:
                existing.supervisor_keywords.append(kw)

        for met in paper.evaluation_metrics:
            if met and met not in existing.evaluation_metrics:
                existing.evaluation_metrics.append(met)

        if mark_low_confidence or paper.confidence == Confidence.LOW:
            existing.confidence = Confidence.LOW

        # Upgrade to investigating at frequency >= 3, but NEVER auto-promote to promising
        if existing.status == ProblemStatus.NEW and existing.frequency >= 3:
            existing.status = ProblemStatus.INVESTIGATING

        return existing

    def add_or_update_problem(self, paper_info: ExtractedPaperInfo, research_area: str) -> ResearchProblem:
        """Creates or updates a problem from extracted paper info using two-stage grouping."""
        problems = self.load_problems()
        problem_statement = paper_info.research_problem

        existing_problem, used_fallback = self.find_matching_problem(
            problem_statement=problem_statement,
            research_area=research_area,
            paper_info=paper_info,
        )

        if existing_problem:
            merged = self.merge_evidence(
                existing_problem, paper_info, mark_low_confidence=used_fallback
            )
            for i, p in enumerate(problems):
                if p.id == merged.id:
                    problems[i] = merged
                    break
            self.save_problems(problems)
            return merged
        else:
            confidence = (
                Confidence.LOW
                if (used_fallback or paper_info.confidence == Confidence.LOW)
                else Confidence.NORMAL
            )
            new_problem = ResearchProblem(
                problem_statement=problem_statement,
                research_area=research_area,
                frequency=1,
                status=ProblemStatus.NEW,
                first_seen=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                supporting_papers=[paper_info.paper_id],
                known_limitations=list(paper_info.limitations),
                unresolved_questions=list(paper_info.future_work),
                candidate_methods=(
                    list(paper_info.candidate_methods)
                    if paper_info.candidate_methods
                    else ([paper_info.proposed_approach] if paper_info.proposed_approach else [])
                ),
                existing_approaches=list(paper_info.existing_approaches),
                evaluation_metrics=list(paper_info.evaluation_metrics),
                supervisor_keywords=list(paper_info.keywords),
                confidence=confidence,
                extraction_method=paper_info.extraction_method,
            )
            problems.append(new_problem)
            self.save_problems(problems)
            return new_problem

    def update_status(self, problem_id: str, new_status: str) -> bool:
        """Update problem status, validating against ProblemStatus.ALL."""
        if new_status not in ProblemStatus.ALL:
            logger.warning(f"Invalid status: {new_status}")
            return False
        problems = self.load_problems()
        for p in problems:
            if p.id == problem_id:
                p.status = new_status
                p.last_updated = datetime.now().isoformat()
                self.save_problems(problems)
                return True
        return False

    def get_problems_by_status(self, status: str) -> List[ResearchProblem]:
        """Return all problems with the given status."""
        return [p for p in self.load_problems() if p.status == status]

    def get_problems_by_area(self, area: str) -> List[ResearchProblem]:
        """Return all problems in the given research area."""
        return [p for p in self.load_problems() if p.research_area.lower() == area.lower()]
