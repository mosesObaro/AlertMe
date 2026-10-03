"""Extracts structured research gap information from papers using Claude Sonnet with deterministic fallback."""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from src.models import ResearchItem
from src.research_gaps.models import (
    ExtractedPaperInfo,
    EvidenceClaim,
    ExtractionMethod,
    Confidence,
    canonical_paper_id,
)
from src.research_gaps.llm_client import AnthropicClient, ModelNotFoundError, LLMExecutionError
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "research_gaps.yaml"

PROMPT_VERSION = "2026-10-extractor-v1"

EXTRACTION_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "scoped_problem": {
            "type": "string",
            "description": (
                "A precise statement describing the specific technical research gap or bottleneck "
                "left unresolved. Must NOT be general background or introductory motivation."
            ),
        },
        "research_question": {
            "type": "string",
            "description": "An interrogative research question (e.g., 'How can...', 'What architecture...').",
        },
        "why_unresolved": {
            "type": "string",
            "description": "Explanation of why prior approaches fail or what fundamental trade-off prevents resolution.",
        },
        "limitations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_text": {"type": "string", "description": "Concise statement of the limitation"},
                    "supporting_span": {
                        "type": "string",
                        "description": "Verbatim substring copied exactly from the abstract demonstrating this limitation",
                    },
                },
                "required": ["claim_text", "supporting_span"],
            },
            "description": "Explicit limitations acknowledged in the text. Return empty array rather than inferring unstated limitations.",
        },
        "open_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_text": {"type": "string", "description": "Concise statement of the open question or future work"},
                    "supporting_span": {
                        "type": "string",
                        "description": "Verbatim substring copied exactly from the abstract demonstrating this direction",
                    },
                },
                "required": ["claim_text", "supporting_span"],
            },
            "description": "Explicit future work or unresolved directions mentioned in the text. Return empty array if none.",
        },
        "existing_approaches": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Baseline techniques, existing algorithms, or prior frameworks referenced in the text.",
        },
        "candidate_methods": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific novel methodology, algorithm, or architecture proposed in the paper or suggested as future work.",
        },
        "evaluation_metrics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Evaluation metrics mentioned in the text (e.g. latency, energy, throughput, accuracy).",
        },
    },
    "required": [
        "scoped_problem",
        "research_question",
        "why_unresolved",
        "limitations",
        "open_questions",
        "existing_approaches",
        "candidate_methods",
        "evaluation_metrics",
    ],
}


class GapExtractor:
    """Extracts structured research gap information using Claude Sonnet with deterministic NLP fallback."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        cache_dir: Optional[Path] = None,
        llm_client: Optional[AnthropicClient] = None,
    ):
        self.config = config or self._load_config()
        self.cache_dir = cache_dir or (DATA_DIR / "extractor_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cache.json"

        llm_cfg = self.config.get("llm", {})
        self.model = llm_cfg.get("extractor_model", "claude-sonnet-5-5")
        self.temperature = float(llm_cfg.get("temperature", 0.0))
        self.max_retries = int(llm_cfg.get("max_retries", 1))

        self.llm_client = llm_client or AnthropicClient()
        self.cache = self._load_cache()

        # Telemetry counts for pipeline reporting and CI verification
        self.llm_call_count = 0
        self.fallback_count = 0
        self.total_extracted = 0

        # Heuristic patterns used for deterministic fallback
        self.problem_patterns = [
            r'(challenge|bottleneck|trade-off|unresolved|open question|fundamental problem|major issue)',
            r'(lack of|insufficient|remains unclear|difficult to achieve|how to efficiently)',
        ]
        self.method_patterns = [
            r'(we propose|we design|we introduce|we develop|we present|we formulate|algorithm|framework|architecture|model)',
            r'(reinforcement learning|deep learning|optimization|heuristic|game theory|lyapunov|federated|neural network)',
        ]
        self.contribution_patterns = [
            r'(experimental results|simulation results|show that|demonstrates|outperforms|achieves|reduces|improves|evaluation)',
            r'(compared to|superior to|findings indicate|we demonstrate)',
        ]
        self.limitation_patterns = [
            r'(limitation|does not consider|not addressed|assumption|simplified|drawback|neglected|fails to|restricted to|only considers)',
        ]
        self.future_work_patterns = [
            r'(future work|future research|plan to|will be extended|could be extended|remains open|further investigation|promising direction)',
        ]
        self.dataset_patterns = [
            r'(dataset|benchmark|testbed|simulation|real-world|traces|workload)',
        ]
        self.metric_keywords = [
            'latency', 'throughput', 'accuracy', 'energy', 'delay', 'convergence',
            'cost', 'utilization', 'f1', 'precision', 'recall', 'bandwidth',
            'completion time', 'makespan', 'response time', 'power consumption',
        ]

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
                logger.warning(f"Could not load extractor cache: {e}")
        return {}

    def _save_cache(self) -> None:
        try:
            from src.storage.state_manager import _atomic_write_json
            _atomic_write_json(self.cache_file, self.cache)
        except Exception as e:
            logger.warning(f"Could not save extractor cache: {e}")

    def _cache_key(self, paper_id: str, text: str) -> str:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"{paper_id}_{text_hash}_{PROMPT_VERSION}"

    # ── Text Token & Heuristic Helpers ─────────────────────────────────

    def _split_sentences(self, text: str) -> List[str]:
        if not text:
            return []
        sentences = re.split(r'\. |\.\n', text)
        return [s.strip().rstrip('.') for s in sentences if s.strip()]

    def _match_patterns(self, sentences: List[str], patterns: List[str]) -> List[str]:
        matched = []
        for s in sentences:
            for pat in patterns:
                if re.search(pat, s, re.IGNORECASE):
                    matched.append(s)
                    break
        return matched

    def _extract_metrics(self, text: str) -> List[str]:
        found = []
        lower = text.lower()
        for m in self.metric_keywords:
            if m in lower:
                found.append(m)
        return found

    def _extract_year(self, date_str: str) -> int:
        if not date_str:
            return 0
        match = re.search(r'(19|20)\d{2}', str(date_str))
        return int(match.group(0)) if match else 0

    # ── Claim Validation and Confidence Checks ─────────────────────────

    def _validate_claims(
        self,
        raw_claims: List[Dict[str, Any]],
        text: str,
        paper_id: str,
    ) -> List[EvidenceClaim]:
        """Validates that every claim carries a verbatim supporting_span that is a substring of the text.

        Drops any claim whose supporting span is not verified in the source text.
        """
        valid_claims = []
        text_lower = text.lower()
        for c in raw_claims:
            if not isinstance(c, dict):
                continue
            claim_text = c.get("claim_text", "").strip()
            span = c.get("supporting_span", "").strip()
            if not claim_text or not span:
                continue

            # Strict substring check (case-insensitive to accommodate capitalizations)
            if span.lower() in text_lower:
                valid_claims.append(
                    EvidenceClaim(claim_text=claim_text, paper_id=paper_id, supporting_span=span)
                )
            else:
                logger.warning(
                    f"Dropped claim '{claim_text[:40]}...': span '{span[:40]}...' is not a substring of abstract."
                )
        return valid_claims

    def _evaluate_confidence(
        self,
        scoped_problem: str,
        candidate_methods: List[str],
        limitations: List[EvidenceClaim],
        open_questions: List[EvidenceClaim],
    ) -> Tuple[str, List[str]]:
        """Evaluates whether the extracted problem exhibits hallmarks of low-confidence extraction."""
        reasons = []

        # 1. candidate_methods equals the statement verbatim or nearly verbatim
        norm_stmt = re.sub(r'\W+', '', scoped_problem.lower())
        for m in candidate_methods:
            norm_m = re.sub(r'\W+', '', m.lower())
            if norm_m and (norm_m == norm_stmt or norm_m in norm_stmt or norm_stmt in norm_m):
                reasons.append("candidate_methods_equals_statement")
                break

        # 2. Scoped problem shares no key terms with its limitations and open questions
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'that', 'this', 'these', 'those', 'such', 'not', 'can', 'could', 'will', 'would',
            'paper', 'propose', 'presents', 'approach', 'system', 'method', 'framework', 'work'
        }
        stmt_terms = {w for w in re.findall(r'[a-zA-Z]{4,}', scoped_problem.lower()) if w not in stop_words}
        all_claim_text = " ".join([c.claim_text for c in limitations + open_questions])
        claim_terms = {w for w in re.findall(r'[a-zA-Z]{4,}', all_claim_text.lower()) if w not in stop_words}

        if (limitations or open_questions) and stmt_terms and claim_terms:
            overlap = stmt_terms.intersection(claim_terms)
            if not overlap:
                reasons.append("statement_shares_no_key_terms_with_claims")

        confidence = Confidence.LOW if reasons else Confidence.NORMAL
        return confidence, reasons

    # ── Core Extraction Methods ────────────────────────────────────────

    def _extract_with_llm(
        self,
        item: ResearchItem,
        text: str,
        source_scope: str = "abstract",
    ) -> ExtractedPaperInfo:
        """Executes structured extraction via Claude Sonnet."""
        system_prompt = (
            "You are an expert academic research assistant preparing for a PhD in Edge Computing & Distributed Systems.\n"
            "Analyze the provided academic publication text (which is restricted to the paper's abstract) and extract structured research gap intelligence.\n\n"
            "STRICT RULES:\n"
            "1. Scoped Problem: Extract a precise statement of the specific research gap, bottleneck, or tradeoff left unresolved. "
            "Do NOT output general background or broad motivation (BAD: 'Deploying deep learning models on resource-constrained edge devices faces acute memory and latency bottlenecks'. "
            "GOOD: 'Existing dynamic layer partitioning frameworks overlook wireless channel fluctuations and hardware runtime jitter, causing severe tail latency spikes in multi-tenant edge nodes').\n"
            "2. Research Question: Formulate a focused, interrogative research question ('How can...', 'What architecture...').\n"
            "3. Why Unresolved: State why prior approaches fail or the fundamental constraint that makes this hard.\n"
            "4. Verbatim Supporting Spans: For every limitation and open question, you MUST provide a supporting_span that is copied VERBATIM as a substring from the input text. Never fabricate spans.\n"
            "5. Return Empty When Not Mentioned: If the paper does not acknowledge limitations, return an empty array. Do not invent limitations.\n"
            "6. Candidate Methods: List the novel algorithms, architectures, or techniques proposed in the paper or proposed for future work. "
            "Do NOT duplicate the problem statement."
        )

        user_prompt = (
            f"Paper Title: {item.title}\n"
            f"Venue: {item.venue or item.source}\n"
            f"Source Scope: {source_scope}\n\n"
            f"--- Paper Text ({source_scope}) ---\n"
            f"{text}\n"
            f"--- End Paper Text ---"
        )

        # Call structured tool with one retry on transient execution failure
        result = None
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = self.llm_client.call_structured(
                    model=self.model,
                    system=system_prompt,
                    user_prompt=user_prompt,
                    tool_name="extract_research_gap_info",
                    tool_schema=EXTRACTION_TOOL_SCHEMA,
                    temperature=self.temperature,
                )
                break
            except ModelNotFoundError:
                # 404 is a configuration error: must raise immediately per specification
                raise
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.info(f"Retrying LLM extraction for '{item.title}' after error: {e}")

        if result is None:
            raise LLMExecutionError(f"LLM extraction failed after {self.max_retries + 1} attempts: {last_error}")

        # Validate supporting spans against text
        limitations = self._validate_claims(result.get("limitations", []), text, item.id)
        open_questions = self._validate_claims(result.get("open_questions", []), text, item.id)

        scoped_problem = result.get("scoped_problem", "").strip()
        candidate_methods = [m.strip() for m in result.get("candidate_methods", []) if m.strip()]
        existing_approaches = [a.strip() for a in result.get("existing_approaches", []) if a.strip()]
        metrics = [m.strip() for m in result.get("evaluation_metrics", []) if m.strip()] or self._extract_metrics(text)

        confidence, low_reasons = self._evaluate_confidence(
            scoped_problem, candidate_methods, limitations, open_questions
        )

        return ExtractedPaperInfo(
            paper_id=item.id,
            title=item.title,
            authors=item.authors,
            year=self._extract_year(item.publication_date),
            venue=item.venue,
            doi=item.doi or "",
            url=item.url,
            source=item.source,
            research_problem=scoped_problem,
            research_question=result.get("research_question", "").strip(),
            why_unresolved=result.get("why_unresolved", "").strip(),
            proposed_approach=candidate_methods[0] if candidate_methods else "",
            methodology=" ".join(candidate_methods[:2]) if candidate_methods else "",
            dataset_testbed="",
            evaluation_metrics=metrics,
            main_contribution=result.get("why_unresolved", "").strip(),
            limitations=limitations,
            future_work=open_questions,
            existing_approaches=existing_approaches,
            candidate_methods=candidate_methods,
            keywords=list(item.topics) if item.topics else [],
            abstract=text,
            citation_count=item.raw_metadata.get("cited_by_count", 0) or item.raw_metadata.get("citation_count", 0),
            extraction_method=ExtractionMethod.LLM,
            source_scope=source_scope,
            prompt_version=PROMPT_VERSION,
            confidence=confidence,
            low_confidence_reasons=low_reasons,
        )

    def _extract_deterministic(
        self,
        item: ResearchItem,
        text: str,
        is_fallback: bool = False,
        source_scope: str = "abstract",
    ) -> ExtractedPaperInfo:
        """Deterministic NLP rule-based extractor with claim span validation."""
        sentences = self._split_sentences(text)

        problem_sents = self._match_patterns(sentences, self.problem_patterns)
        method_sents = self._match_patterns(sentences, self.method_patterns)
        contrib_sents = self._match_patterns(sentences, self.contribution_patterns)
        limit_sents = self._match_patterns(sentences, self.limitation_patterns)
        future_sents = self._match_patterns(sentences, self.future_work_patterns)

        # Disambiguate problem vs background: if sentence 1 was matched but sentence 2 also has a contrastive marker, prefer sentence 2
        research_problem = ""
        if len(problem_sents) > 1 and len(sentences) > 1 and problem_sents[0] == sentences[0]:
            for s in sentences[1:3]:
                if re.search(r'\b(however|challenge|bottleneck|unresolved)\b', s, re.IGNORECASE):
                    research_problem = s
                    break
        if not research_problem and problem_sents:
            research_problem = problem_sents[0]
        elif not research_problem:
            for s in sentences:
                if re.search(r'\b(however|problem|issue)\b', s, re.IGNORECASE):
                    research_problem = s
                    break

        # Candidate methods: avoid picking the same sentence as research_problem
        candidate_methods = []
        for ms in method_sents:
            if ms.strip().lower() != research_problem.strip().lower():
                candidate_methods.append(ms)
        if not candidate_methods and method_sents:
            candidate_methods = [method_sents[0]]

        proposed_approach = candidate_methods[0] if candidate_methods else ""
        methodology = " ".join(candidate_methods[:2]) if candidate_methods else ""
        main_contribution = contrib_sents[0] if contrib_sents else (sentences[-1] if sentences else "")

        # Limitations and open questions are bound to their verbatim sentences in the text
        limitations = [
            EvidenceClaim(claim_text=s, paper_id=item.id, supporting_span=s)
            for s in limit_sents
            if s.lower() in text.lower()
        ]
        future_work = [
            EvidenceClaim(claim_text=s, paper_id=item.id, supporting_span=s)
            for s in future_sents
            if s.lower() in text.lower()
        ]

        metrics = self._extract_metrics(text)
        keywords = list(item.topics) if item.topics else []
        year = self._extract_year(item.publication_date)
        citation_count = item.raw_metadata.get("cited_by_count", 0) or item.raw_metadata.get("citation_count", 0)

        confidence, low_reasons = self._evaluate_confidence(
            research_problem, candidate_methods, limitations, future_work
        )

        extraction_method = (
            ExtractionMethod.DETERMINISTIC_FALLBACK if is_fallback else ExtractionMethod.DETERMINISTIC
        )

        return ExtractedPaperInfo(
            paper_id=item.id,
            title=item.title,
            authors=item.authors,
            year=year,
            venue=item.venue,
            doi=item.doi or "",
            url=item.url,
            source=item.source,
            research_problem=research_problem,
            research_question=f"How can {research_problem.lower().rstrip('.')} be resolved?" if research_problem else "",
            why_unresolved="Unresolved under heterogeneous edge operating conditions.",
            proposed_approach=proposed_approach,
            methodology=methodology,
            dataset_testbed="",
            evaluation_metrics=metrics,
            main_contribution=main_contribution,
            limitations=limitations,
            future_work=future_work,
            existing_approaches=["Baseline algorithms"],
            candidate_methods=candidate_methods,
            keywords=keywords,
            abstract=text,
            citation_count=citation_count,
            extraction_method=extraction_method,
            source_scope=source_scope,
            prompt_version="",
            confidence=confidence,
            low_confidence_reasons=low_reasons,
        )

    def extract(
        self,
        item: ResearchItem,
        text: Optional[str] = None,
        source_scope: str = "abstract",
    ) -> ExtractedPaperInfo:
        """Extracts structured research gap information from a paper.

        Takes (text, source_scope) to allow full-text sections to slot in seamlessly.
        Defaults to item.abstract with source_scope='abstract'.
        """
        paper_text = text if text is not None else (item.abstract or "")
        paper_id = item.id or canonical_paper_id(doi=item.doi, title=item.title, url=item.url)

        if not paper_text.strip():
            return ExtractedPaperInfo(
                paper_id=paper_id,
                title=item.title,
                authors=item.authors,
                year=self._extract_year(item.publication_date),
                venue=item.venue,
                doi=item.doi or "",
                url=item.url,
                source=item.source,
                extraction_method=ExtractionMethod.DETERMINISTIC,
                source_scope=source_scope,
            )

        # Check persistent cache by (paper_id, abstract_hash, prompt_version)
        cache_k = self._cache_key(paper_id, paper_text)
        if cache_k in self.cache:
            try:
                cached_dict = self.cache[cache_k]
                return ExtractedPaperInfo.from_dict(cached_dict)
            except Exception as e:
                logger.warning(f"Cache read error for {cache_k}: {e}")

        # Attempt structured Claude LLM extraction if available
        if self.llm_client.is_available():
            self.llm_call_count += 1
            try:
                extracted = self._extract_with_llm(item, paper_text, source_scope=source_scope)
                self.cache[cache_k] = extracted.to_dict()
                self._save_cache()
                self.total_extracted += 1
                return extracted
            except ModelNotFoundError:
                # 404 is a configuration error: raise immediately per spec
                raise
            except Exception as e:
                self.fallback_count += 1
                logger.warning(
                    f"LLM extraction failed for paper '{item.title}': {e}. "
                    f"Falling back to deterministic extraction (extraction_method='deterministic_fallback')."
                )
                extracted = self._extract_deterministic(
                    item, paper_text, is_fallback=True, source_scope=source_scope
                )
                self.cache[cache_k] = extracted.to_dict()
                self._save_cache()
                self.total_extracted += 1
                return extracted
        else:
            # No API key provided: use deterministic extractor
            extracted = self._extract_deterministic(
                item, paper_text, is_fallback=False, source_scope=source_scope
            )
            self.total_extracted += 1
            return extracted

    def extract_batch(
        self,
        items: List[ResearchItem],
        source_scope: str = "abstract",
    ) -> List[ExtractedPaperInfo]:
        """Extracts structured info from a batch of papers with summary reporting."""
        logger.info(f"Extracting research gap info from {len(items)} papers (scope: {source_scope})")
        results = []
        for item in items:
            try:
                results.append(self.extract(item, source_scope=source_scope))
            except ModelNotFoundError:
                # 404 is a configuration error: abort batch immediately
                raise
            except Exception as e:
                logger.error(f"Failed to extract info from '{item.title}': {e}")

        logger.info(
            f"Extraction batch complete: {len(results)} papers processed. "
            f"(LLM calls: {self.llm_call_count}, Fallbacks: {self.fallback_count})"
        )
        return results
