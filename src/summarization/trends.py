"""Emerging research trend detector across monitored sources."""

from collections import Counter
from typing import List, Dict, Any, Optional
import datetime
from src.models import ResearchItem


class TrendDetector:
    """Analyzes topic frequency and velocity across discovered research items."""

    def __init__(self, monitored_topics: Optional[List[str]] = None):
        self.monitored_topics = monitored_topics or [
            "Edge AI", "Federated Learning", "6G + Edge", "Edge Security",
            "Computation Offloading", "Device-Edge-Cloud", "Edge Inference",
            "Resource Allocation", "TinyML", "Split Learning", "Edge Caching"
        ]

    def detect_trends(
        self,
        current_items: List[ResearchItem],
        history_items: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Calculates observed topic trends and direction indicators."""
        today = datetime.date.today()
        recent_counts: Counter = Counter()
        older_counts: Counter = Counter()

        # Count occurrences in current batch
        for item in current_items:
            combined = f"{item.title} {item.abstract}".lower()
            for topic in self.monitored_topics:
                if topic.lower() in combined:
                    recent_counts[topic] += 1

        # Count occurrences in history
        if history_items:
            for item in history_items:
                combined = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
                pub_date_str = item.get("publication_date") or item.get("discovery_date")
                is_recent = True
                if pub_date_str:
                    try:
                        dt = datetime.date.fromisoformat(pub_date_str[:10])
                        if (today - dt).days > 7:
                            is_recent = False
                    except Exception:
                        pass

                for topic in self.monitored_topics:
                    if topic.lower() in combined:
                        if is_recent:
                            recent_counts[topic] += 1
                        else:
                            older_counts[topic] += 1

        trends = []
        for topic in self.monitored_topics:
            rec = recent_counts[topic]
            old = older_counts[topic]

            if rec >= 3 and rec > old * 1.5:
                direction = "↑↑"
                status = "Surging"
            elif rec > old:
                direction = "↑"
                status = "Rising"
            elif rec == 0 and old == 0:
                direction = "→"
                status = "Stable"
            elif rec < old:
                direction = "↓"
                status = "Declining"
            else:
                direction = "→"
                status = "Steady"

            trends.append({
                "topic": topic,
                "direction": direction,
                "status": status,
                "recent_count": rec,
                "historical_count": old
            })

        # Sort by most active
        trends.sort(key=lambda x: (x["direction"] == "↑↑", x["recent_count"]), reverse=True)
        return trends
