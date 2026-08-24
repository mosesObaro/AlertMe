"""Conferences and Call for Papers (CFP) collector."""

import datetime
from typing import List, Dict, Any, Optional
from src.collectors.base import BaseCollector
from src.models import ResearchItem, ItemType, CredibilityTier
from src.utils.logger import logger
import feedparser
from bs4 import BeautifulSoup


class ConferenceCollector(BaseCollector):
    """Monitors conference announcements, CFPs, and tracks approaching submission deadlines."""

    def __init__(
        self,
        name: str = "Conferences & CFPs",
        conferences_config: Optional[List[Dict[str, Any]]] = None,
        cfp_feeds: Optional[List[str]] = None,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER3_CONFERENCE.value, enabled=enabled)
        self.conferences_config = conferences_config or []
        self.cfp_feeds = cfp_feeds or [
            "http://www.wikicfp.com/cfp/rss?cat=edge%20computing",
            "https://www.usenix.org/conferences/upcoming/feed"
        ]

    def fetch(self) -> List[ResearchItem]:
        items: List[ResearchItem] = []

        # 1. Process curated conference schedule if specified
        today = datetime.date.today()
        current_year = today.year

        for conf in self.conferences_config:
            name = conf.get("name", "")
            acronym = conf.get("acronym", name)
            website = conf.get("website", "")
            topics = conf.get("topics", [])
            organizer = conf.get("organizer", "Academic")
            deadline_month = conf.get("typical_deadline_month")

            if deadline_month:
                # Estimate deadline in current year or next year
                target_year = current_year if deadline_month >= today.month else current_year + 1
                try:
                    estimated_deadline = datetime.date(target_year, deadline_month, 15)
                    days_until = (estimated_deadline - today).days

                    # Only alert if within 90 days of deadline
                    if 0 <= days_until <= 90:
                        is_urgent = days_until <= 14
                        title = f"[{acronym}] {name} {target_year} — Call for Papers"
                        abstract = f"Submission deadline approaching in approximately {days_until} days ({estimated_deadline.isoformat()}). Topics: {', '.join(topics)}."
                        
                        item = ResearchItem(
                            title=title,
                            url=website,
                            source=f"Curated Conference List ({organizer})",
                            source_tier=self.tier,
                            item_type=ItemType.CONFERENCE_CFP.value,
                            deadline=estimated_deadline.isoformat(),
                            is_urgent=is_urgent,
                            abstract=abstract,
                            venue=f"{acronym} {target_year}",
                            topics=topics
                        )
                        items.append(item)
                except Exception as e:
                    logger.debug(f"Error computing conference deadline for {name}: {e}")

        # 2. Process external CFP feeds
        for feed_url in self.cfp_feeds:
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
                    summary = entry.get("summary") or entry.get("description") or ""
                    soup = BeautifulSoup(summary, "html.parser")
                    clean_summary = " ".join(soup.get_text().split())

                    item = ResearchItem(
                        title=title,
                        url=link,
                        source="Conference Feed",
                        source_tier=self.tier,
                        item_type=ItemType.CONFERENCE_CFP.value,
                        abstract=clean_summary,
                        venue="Conference CFP"
                    )
                    items.append(item)
            except Exception as e:
                logger.warning(f"Failed to fetch CFP feed {feed_url}: {e}")

        return items
