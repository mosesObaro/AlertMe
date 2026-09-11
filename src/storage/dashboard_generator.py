"""Generates static JSON database for GitHub Pages dashboard."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime
from src.models import ResearchItem, PhDOpportunity, Scholarship, ResearcherProfile
from src.storage.state_manager import StateManager, _atomic_write_json
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
DASHBOARD_DATA_FILE = DOCS_DIR / "data.json"


class DashboardGenerator:
    """Exports structured data for the GitHub Pages static dashboard."""

    def __init__(self, state_manager: Optional[StateManager] = None, config_manager: Optional[ConfigManager] = None):
        self.state_manager = state_manager or StateManager()
        self.config_manager = config_manager or ConfigManager()

    def _normalize_dict(self, obj: Any) -> Dict[str, Any]:
        """Normalizes a dataclass or dict to a standard dictionary."""
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return obj
        return {}

    def generate_dashboard_data(
        self,
        current_items: List[ResearchItem],
        trends: List[Dict[str, Any]],
        supervisors: List[Dict[str, Any]],
        opportunities: Optional[List[Any]] = None,
        scholarships: Optional[List[Any]] = None,
        researchers: Optional[List[Any]] = None,
        countries_info: Optional[Dict[str, Any]] = None
    ):
        """Builds and writes docs/data.json with full intelligence payload."""
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

        # Build Opportunities list
        opp_list: List[Dict[str, Any]] = []
        if opportunities:
            opp_list = [self._normalize_dict(o) for o in opportunities]
        else:
            stored_opps = self.state_manager.load_opportunities()
            if stored_opps:
                opp_list = stored_opps
            else:
                for it in items_list:
                    opp_data = it.get("opportunity_data")
                    if opp_data and opp_data.get("kind") == "phd_opportunity":
                        opp_list.append(opp_data)
                    elif it.get("item_type") in ["phd_opportunity", "fellowship"]:
                        opp_list.append({
                            "title": it.get("title"),
                            "university": it.get("institution", ""),
                            "department": "",
                            "country": it.get("location", ""),
                            "link": it.get("url"),
                            "fit_score": it.get("score", {}).get("final_score", 7.0) if it.get("score") else 7.0,
                            "recruitment_status": "unverified",
                            "funding_status": "partially_funded",
                            "dependant_support": "unspecified",
                            "direct_quote": None,
                            "deadline": it.get("deadline")
                        })

        # Build Scholarships list
        schol_list: List[Dict[str, Any]] = []
        if scholarships:
            schol_list = [self._normalize_dict(s) for s in scholarships]
        else:
            stored_schols = self.state_manager.load_scholarships()
            if stored_schols:
                schol_list = stored_schols
            else:
                for it in items_list:
                    opp_data = it.get("opportunity_data")
                    if opp_data and opp_data.get("kind") == "scholarship":
                        schol_list.append(opp_data)

        # Build Researchers list
        res_list: List[Dict[str, Any]] = []
        if researchers:
            res_list = [self._normalize_dict(r) for r in researchers]
        else:
            watchlist_data = self.state_manager.load_researcher_watchlist()
            if watchlist_data and "researchers" in watchlist_data:
                res_list = watchlist_data.get("researchers", [])
            elif supervisors:
                res_list = supervisors

        # Load Target Countries guidance
        target_countries = countries_info or self.config_manager.phd_opportunities_config.get("target_countries", {})

        # Compute summary metrics
        total_items = len(items_list)
        high_relevance_count = sum(
            1 for x in items_list if (x.get("score", {}).get("final_score", 0.0) if x.get("score") else 0.0) >= 7.5
        )
        papers_count = sum(1 for x in items_list if x.get("item_type") in ["paper", "preprint", "survey"])
        conferences_count = sum(1 for x in items_list if x.get("item_type") == "conference_cfp")
        opportunities_count = len(opp_list)
        scholarships_count = len(schol_list)
        active_recruitment_count = sum(
            1 for o in opp_list if o.get("recruitment_status") == "actively_recruiting"
        ) + sum(
            1 for r in res_list if r.get("recruitment_status") == "actively_recruiting"
        )

        dashboard_payload = {
            "meta": {
                "last_updated": today_str,
                "total_items": total_items,
                "high_relevance_count": high_relevance_count,
                "papers_count": papers_count,
                "conferences_count": conferences_count,
                "opportunities_count": opportunities_count,
                "scholarships_count": scholarships_count,
                "active_recruitment_count": active_recruitment_count
            },
            "trends": trends,
            "supervisors": supervisors,
            "researchers": res_list,
            "opportunities": opp_list,
            "scholarships": schol_list,
            "target_countries": target_countries,
            "items": items_list[:200]  # Top 200 items for web UI performance
        }

        try:
            _atomic_write_json(DASHBOARD_DATA_FILE, dashboard_payload)
            logger.info(f"Updated dashboard data in {DASHBOARD_DATA_FILE}")
        except Exception as e:
            logger.error(f"Failed to write dashboard data: {e}")
