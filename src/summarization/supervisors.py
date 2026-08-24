"""Researcher and Potential Supervisor Discovery Tracker."""

from collections import defaultdict
from typing import List, Dict, Any, Optional
from src.models import ResearchItem


class SupervisorTracker:
    """Identifies recurring researchers in high-relevance edge computing publications."""

    def __init__(self):
        pass

    def update_and_extract_supervisors(
        self,
        new_items: List[ResearchItem],
        existing_registry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Aggregates author appearances and outputs top researchers to investigate."""
        registry = existing_registry or {}

        for item in new_items:
            # Only consider high quality papers
            if not item.score or item.score.final_score < 7.0:
                continue

            for author in item.authors:
                clean_author = author.strip()
                if not clean_author or len(clean_author.split()) < 2:
                    continue

                if clean_author not in registry:
                    registry[clean_author] = {
                        "name": clean_author,
                        "publication_count": 0,
                        "average_relevance": 0.0,
                        "topics": [],
                        "recent_papers": [],
                        "institution": item.institution or "Academic Institution"
                    }

                record = registry[clean_author]
                total_pub = record["publication_count"]
                current_avg = record["average_relevance"]
                new_score = item.score.final_score

                record["publication_count"] += 1
                record["average_relevance"] = round((current_avg * total_pub + new_score) / (total_pub + 1), 1)

                if item.institution and record["institution"] == "Academic Institution":
                    record["institution"] = item.institution

                for t in (item.topics or item.score.matched_topics):
                    if t not in record["topics"]:
                        record["topics"].append(t)

                if item.title not in [p.get("title") for p in record["recent_papers"]]:
                    record["recent_papers"].append({
                        "title": item.title,
                        "url": item.url,
                        "date": item.publication_date,
                        "score": new_score
                    })
                    # Keep latest 5 papers
                    record["recent_papers"] = record["recent_papers"][-5:]

        return registry

    def get_top_supervisors_to_watch(
        self,
        registry: Dict[str, Any],
        min_publications: int = 2,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Returns list of top researchers to investigate for PhD supervision."""
        candidates = [
            r for r in registry.values()
            if r["publication_count"] >= min_publications and r["average_relevance"] >= 7.5
        ]
        candidates.sort(key=lambda x: (x["publication_count"], x["average_relevance"]), reverse=True)
        return candidates[:limit]
