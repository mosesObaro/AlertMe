"""PhD and Fellowship Opportunities collector."""

from typing import List, Optional
import feedparser
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector
from src.models import ResearchItem, ItemType, CredibilityTier
from src.utils.logger import logger


class OpportunityCollector(BaseCollector):
    """Collects PhD positions, fully funded studentships, and research fellowships."""

    def __init__(
        self,
        name: str = "PhD & Research Opportunities",
        feeds: Optional[List[str]] = None,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER2_UNIVERSITY_LAB.value, enabled=enabled)
        self.feeds = feeds or [
            "https://www.jobs.ac.uk/jobs/computer-science-phds.rss"
        ]

    def fetch(self) -> List[ResearchItem]:
        items: List[ResearchItem] = []

        for feed_url in self.feeds:
            try:
                response = self.requester.get(feed_url)
                if not response or response.status_code != 200:
                    continue

                feed = feedparser.parse(response.content)
                for entry in feed.entries:
                    title = entry.get("title", "").strip()
                    if not title:
                        continue

                    link = entry.get("link", "").strip()
                    raw_desc = entry.get("summary") or entry.get("description") or ""
                    soup = BeautifulSoup(raw_desc, "html.parser")
                    clean_desc = " ".join(soup.get_text().split())

                    # Check if relevant to CS/Systems/Edge/Distributed/AI
                    combined_text = f"{title} {clean_desc}".lower()
                    edge_keywords = [
                        "edge", "cloud", "distributed", "iot", "systems", "network",
                        "federated", "5g", "6g", "computing", "pervasive", "fog"
                    ]
                    
                    if not any(kw in combined_text for kw in edge_keywords):
                        continue

                    item = ResearchItem(
                        title=title,
                        url=link,
                        source="Academic Opportunities",
                        source_tier=self.tier,
                        item_type=ItemType.PHD_OPPORTUNITY.value,
                        abstract=clean_desc,
                        venue="PhD Studentship / Fellowship",
                        institution=entry.get("author", "")
                    )
                    items.append(item)

            except Exception as e:
                logger.warning(f"Error fetching opportunity feed {feed_url}: {e}")

        return items
