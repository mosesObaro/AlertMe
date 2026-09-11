"""Researcher, Potential Supervisor Discovery, and Recruitment Watchlist Tracker."""

from typing import List, Dict, Any, Optional, Tuple
from src.models import (
    ResearchItem,
    ResearcherProfile,
    RecruitmentStatus
)
from src.collectors.academic_researcher_discovery import AcademicResearcherDiscovery
from src.ranking.opportunity_scorer import OpportunityScorer
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger


class SupervisorTracker:
    """Tracks academic researchers, evaluates supervision fit, and maintains active recruitment watchlist."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.discovery_engine = AcademicResearcherDiscovery(self.config)
        self.scorer = OpportunityScorer(self.config)

    def update_and_extract_supervisors(
        self,
        new_items: List[ResearchItem],
        existing_registry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Discovers and updates candidate supervisors from recent academic publication stream."""
        registry = self.discovery_engine.discover_candidate_researchers(new_items, existing_registry)
        # Convert to dict for JSON serialization
        return {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in registry.items()}

    def get_top_supervisors_to_watch(
        self,
        registry: Dict[str, Any],
        min_publications: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Returns list of highest-scoring researchers for PhD supervision."""
        candidates = []
        for r in registry.values():
            pub_count = r.get("publication_count", 0)
            score = r.get("composite_score", 0.0) or r.get("average_relevance", 0.0)
            if pub_count >= min_publications and score >= 6.5:
                candidates.append(r)

        # Sort: actively recruiting first, then composite score descending
        def sort_key(x):
            is_active = 1 if x.get("recruitment_status") == RecruitmentStatus.ACTIVELY_RECRUITING.value else 0
            is_likely = 1 if x.get("recruitment_status") == RecruitmentStatus.LIKELY_RECRUITING.value else 0
            score = x.get("composite_score", 0.0) or x.get("average_relevance", 0.0)
            return (is_active, is_likely, score, x.get("publication_count", 0))

        candidates.sort(key=sort_key, reverse=True)
        return candidates[:limit]

    def get_actively_recruiting_researchers(
        self,
        registry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filters researchers with verified active or likely PhD recruitment status."""
        recruiting = [
            r for r in registry.values()
            if r.get("recruitment_status") in [
                RecruitmentStatus.ACTIVELY_RECRUITING.value,
                RecruitmentStatus.LIKELY_RECRUITING.value
            ]
        ]
        recruiting.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)
        return recruiting

    def sync_watchlist(
        self,
        watchlist: Dict[str, Any],
        new_items: List[ResearchItem]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Monitors watchlisted researchers for new publications or recruitment changes."""
        changes = []
        for item in new_items:
            for author in item.authors:
                clean_name = self.discovery_engine._clean_author_name(author)
                if clean_name in watchlist:
                    prof = watchlist[clean_name]
                    recent_titles = [p.get("title") for p in prof.get("recent_papers", [])]
                    if item.title not in recent_titles:
                        prof["recent_papers"].append({
                            "title": item.title,
                            "url": item.url,
                            "date": item.publication_date,
                            "venue": item.venue or item.source,
                            "score": item.score.final_score if item.score else 7.0
                        })
                        prof["recent_papers"] = prof["recent_papers"][-5:]
                        prof["publication_count"] = prof.get("publication_count", 0) + 1
                        changes.append({
                            "type": "new_paper",
                            "researcher": clean_name,
                            "paper_title": item.title
                        })

        return watchlist, changes
