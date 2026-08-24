"""Generates static JSON database for GitHub Pages dashboard."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
from src.models import ResearchItem
from src.storage.state_manager import StateManager, _atomic_write_json
from src.utils.logger import logger

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
DASHBOARD_DATA_FILE = DOCS_DIR / "data.json"


class DashboardGenerator:
    """Exports structured data for the GitHub Pages static dashboard."""

    def __init__(self, state_manager: Optional[StateManager] = None):
        self.state_manager = state_manager or StateManager()

    def generate_dashboard_data(
        self,
        current_items: List[ResearchItem],
        trends: List[Dict[str, Any]],
        supervisors: List[Dict[str, Any]]
    ):
        """Builds and writes docs/data.json."""
        history = self.state_manager.load_alert_history()
        today_str = datetime.date.today().isoformat()

        # Combine history and current items for the dashboard viewer
        all_items_map = {}
        for h in history:
            all_items_map[h.get("id")] = h
        for item in current_items:
            all_items_map[item.id] = item.to_dict()

        items_list = list(all_items_map.values())
        # Sort by score descending then date
        items_list.sort(
            key=lambda x: (
                x.get("score", {}).get("final_score", 0.0) if x.get("score") else 0.0,
                x.get("publication_date", "")
            ),
            reverse=True
        )

        # Compute summary metrics
        total_items = len(items_list)
        high_relevance_count = sum(
            1 for x in items_list if (x.get("score", {}).get("final_score", 0.0) if x.get("score") else 0.0) >= 7.5
        )
        papers_count = sum(1 for x in items_list if x.get("item_type") in ["paper", "preprint", "survey"])
        conferences_count = sum(1 for x in items_list if x.get("item_type") == "conference_cfp")
        opportunities_count = sum(1 for x in items_list if x.get("item_type") == "phd_opportunity")

        dashboard_payload = {
            "meta": {
                "last_updated": today_str,
                "total_items": total_items,
                "high_relevance_count": high_relevance_count,
                "papers_count": papers_count,
                "conferences_count": conferences_count,
                "opportunities_count": opportunities_count
            },
            "trends": trends,
            "supervisors": supervisors,
            "items": items_list[:200] # Top 200 items for web UI performance
        }

        try:
            _atomic_write_json(DASHBOARD_DATA_FILE, dashboard_payload)
            logger.info(f"Updated dashboard data in {DASHBOARD_DATA_FILE}")
        except Exception as e:
            logger.error(f"Failed to write dashboard data: {e}")
