"""Extracts structured research information from papers using deterministic NLP heuristics."""

import re
from typing import List, Optional
from src.models import ResearchItem
from src.research_gaps.models import ExtractedPaperInfo, EvidenceClaim
from src.utils.logger import logger


class GapExtractor:
    """Extracts structured research gap information from ResearchItem objects."""

    def __init__(self):
        # Specific problem/challenge patterns - NOT including 'limitation' or 'future work'
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

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if not text:
            return []
        sentences = re.split(r'\. |\.\n', text)
        return [s.strip().rstrip('.') for s in sentences if s.strip()]

    def _match_patterns(self, sentences: List[str], patterns: List[str]) -> List[str]:
        """Return sentences matching any of the given regex patterns."""
        matched = []
        for s in sentences:
            for pat in patterns:
                if re.search(pat, s, re.IGNORECASE):
                    matched.append(s)
                    break
        return matched

    def _extract_metrics(self, text: str) -> List[str]:
        """Extract evaluation metrics mentioned in text."""
        found = []
        lower = text.lower()
        for m in self.metric_keywords:
            if m in lower:
                found.append(m)
        return found

    def _extract_year(self, date_str: str) -> int:
        """Extract year from a publication date string."""
        if not date_str:
            return 0
        match = re.search(r'(19|20)\d{2}', date_str)
        return int(match.group(0)) if match else 0

    def extract(self, item: ResearchItem) -> ExtractedPaperInfo:
        """Extract structured research gap information from a single paper."""
        abstract = item.abstract or ""
        sentences = self._split_sentences(abstract)

        # Extract structured fields via heuristic pattern matching
        problem_sents = self._match_patterns(sentences, self.problem_patterns)
        method_sents = self._match_patterns(sentences, self.method_patterns)
        contrib_sents = self._match_patterns(sentences, self.contribution_patterns)
        limit_sents = self._match_patterns(sentences, self.limitation_patterns)
        future_sents = self._match_patterns(sentences, self.future_work_patterns)
        dataset_sents = self._match_patterns(sentences, self.dataset_patterns)

        # Fallback problem detection if pattern didn't catch
        if not problem_sents:
            for s in sentences:
                if re.search(r'\b(however|problem|issue)\b', s, re.IGNORECASE):
                    problem_sents.append(s)
                    break

        research_problem = problem_sents[0] if problem_sents else ""
        proposed_approach = method_sents[0] if method_sents else ""
        methodology = " ".join(method_sents[:2]) if method_sents else ""
        dataset_testbed = dataset_sents[0] if dataset_sents else ""
        main_contribution = contrib_sents[0] if contrib_sents else (sentences[-1] if sentences else "")

        metrics = self._extract_metrics(abstract)
        # Sentences are lifted verbatim from the abstract, so each is its own supporting span.
        limitations = [EvidenceClaim(claim_text=s, paper_id=item.id, supporting_span=s) for s in limit_sents]
        future_work = [EvidenceClaim(claim_text=s, paper_id=item.id, supporting_span=s) for s in future_sents]

        # Build keywords from topics + extracted terms
        keywords = list(item.topics) if item.topics else []

        year = self._extract_year(item.publication_date)
        citation_count = item.raw_metadata.get("cited_by_count", 0) or item.raw_metadata.get("citation_count", 0)

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
            proposed_approach=proposed_approach,
            methodology=methodology,
            dataset_testbed=dataset_testbed,
            evaluation_metrics=metrics,
            main_contribution=main_contribution,
            limitations=limitations,
            future_work=future_work,
            keywords=keywords,
            abstract=abstract,
            citation_count=citation_count,
        )

    def extract_batch(self, items: List[ResearchItem]) -> List[ExtractedPaperInfo]:
        """Extract structured info from a batch of papers."""
        logger.info(f"Extracting research gap info from {len(items)} papers")
        results = []
        for item in items:
            try:
                results.append(self.extract(item))
            except Exception as e:
                logger.warning(f"Failed to extract info from '{item.title}': {e}")
        logger.info(f"Successfully extracted info from {len(results)} papers")
        return results
