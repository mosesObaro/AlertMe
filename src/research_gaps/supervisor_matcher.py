"""Matches research problems with potential supervisors based on AlertMe data."""

import json
import string
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from src.research_gaps.models import ResearchProblem, SupervisorMatch, LinkStatus
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / 'data'


class SupervisorMatcher:
    """Matches research problems with potential supervisors based on AlertMe data."""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or DATA_DIR

    def _normalize_text(self, text: str) -> str:
        """Helper to normalize text for comparison."""
        return text.lower().translate(str.maketrans('', '', string.punctuation)).strip()

    def _get_normalized_set(self, keywords: List[str]) -> Set[str]:
        """Convert list of keywords to a normalized set of words."""
        result = set()
        for kw in keywords:
            if not kw:
                continue
            words = self._normalize_text(kw).split()
            result.update(words)
        return result

    def load_supervisor_data(self) -> Dict[str, Any]:
        """Load from data/supervisors.json AND data/researcher_watchlist.json."""
        supervisors = {}

        sup_file = self.data_dir / 'supervisors.json'
        if sup_file.exists():
            try:
                with open(sup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        supervisors.update(data)
            except Exception as e:
                logger.error(f"Error loading {sup_file}: {e}")

        watchlist_file = self.data_dir / 'researcher_watchlist.json'
        if watchlist_file.exists():
            try:
                with open(watchlist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'researchers' in data:
                        researchers = data['researchers']
                        if isinstance(researchers, dict):
                            supervisors.update(researchers)
            except Exception as e:
                logger.error(f"Error loading {watchlist_file}: {e}")

        return supervisors

    def _compute_keyword_overlap(self, problem_keywords: List[str], supervisor_areas: List[str]) -> float:
        """Compute Jaccard similarity on normalized keyword sets."""
        set1 = self._get_normalized_set(problem_keywords)
        set2 = self._get_normalized_set(supervisor_areas)

        if not set1 or not set2:
            return 0.0

        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union) if union else 0.0

    def _compute_publication_relevance(self, problem: ResearchProblem, publications: List[Dict]) -> Tuple[float, List[Dict]]:
        """Score how relevant recent publications are, return score and matching pubs."""
        if not publications:
            return 0.0, []

        problem_terms = self._get_normalized_set(
            problem.supervisor_keywords + [problem.research_area] + [problem.problem_statement]
        )

        matching_pubs = []
        total_score = 0.0

        for pub in publications:
            if not isinstance(pub, dict):
                continue
            title = pub.get('title', '')
            topics = pub.get('topics', [])
            pub_terms = self._get_normalized_set([title] + topics)

            overlap = len(problem_terms.intersection(pub_terms))
            if overlap > 0:
                score = min(1.0, overlap / 3.0)
                matching_pubs.append(pub)
                total_score += score

        if not matching_pubs:
            return 0.0, []

        avg_score = total_score / len(matching_pubs)
        return min(1.0, avg_score), matching_pubs

    def _build_match(self, researcher_data: Dict, problem: ResearchProblem, score: float, matching_pubs: List[Dict], matching_keywords: List[str]) -> SupervisorMatch:
        """Build a SupervisorMatch object from researcher data."""
        profile_url = researcher_data.get('profile_url', '')
        google_scholar = researcher_data.get('google_scholar_url', '') or researcher_data.get('google_scholar', '')
        semantic_scholar = researcher_data.get('semantic_scholar_url', '')

        return SupervisorMatch(
            name=researcher_data.get('name', 'Unknown'),
            institution=researcher_data.get('institution', 'Unknown'),
            country=researcher_data.get('country', ''),
            relevant_research_areas=researcher_data.get('research_areas', []) or researcher_data.get('topics', []),
            relevant_publications=matching_pubs,
            matching_keywords=matching_keywords,
            profile_url=profile_url,
            google_scholar_url=google_scholar,
            semantic_scholar_url=semantic_scholar,
            link_status=LinkStatus.UNKNOWN,
            match_score=round(score, 3),
        )

    def match_supervisors(self, problem: ResearchProblem, max_matches: int = 5) -> List[SupervisorMatch]:
        """Match a single research problem with potential supervisors."""
        supervisors = self.load_supervisor_data()
        if not supervisors:
            logger.warning("No supervisor data found for matching.")
            return []

        problem_keywords = list(problem.supervisor_keywords) if problem.supervisor_keywords else []
        if problem.research_area:
            problem_keywords.append(problem.research_area)

        matches = []
        for researcher_id, data in supervisors.items():
            if not isinstance(data, dict):
                continue

            supervisor_areas = data.get('research_areas', []) or data.get('topics', [])
            keyword_score = self._compute_keyword_overlap(problem_keywords, supervisor_areas)

            norm_prob_kws = self._get_normalized_set(problem_keywords)
            norm_sup_areas = self._get_normalized_set(supervisor_areas)
            common_words = norm_prob_kws.intersection(norm_sup_areas)
            matching_keywords = list(common_words)[:5]

            publications = data.get('recent_papers', []) or data.get('publications', [])
            pub_score, matching_pubs = self._compute_publication_relevance(problem, publications)

            # Combined score: if publications exist, weight 0.4 keyword + 0.6 pub; otherwise 1.0 keyword
            if publications:
                final_score = (keyword_score * 0.4) + (pub_score * 0.6)
            else:
                final_score = keyword_score

            # Minimum threshold
            if final_score >= 0.05:
                match = self._build_match(data, problem, final_score, matching_pubs, matching_keywords)
                matches.append(match)

        matches.sort(key=lambda m: m.match_score, reverse=True)
        return matches[:max_matches]

    def match_all(self, problems: List[ResearchProblem]) -> Dict[str, List[SupervisorMatch]]:
        """Match all problems against the supervisor dataset."""
        logger.info(f"Matching supervisors for {len(problems)} problems")
        result = {}
        for p in problems:
            result[p.id] = self.match_supervisors(p)
        return result
