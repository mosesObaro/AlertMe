"""Event collector for Edge Computing academic and industrial events."""

import datetime
from typing import List, Dict, Any, Optional
import feedparser
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector
from src.models import ResearchItem, CredibilityTier
from src.events.models import EdgeEvent
from src.events.normalizer import EventNormalizer
from src.events.verifier import EventVerifier
from src.events.scorer import EventScorer
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger


class EdgeEventCollector(BaseCollector):
    """
    Collects academic conferences, industry summits, workshops, webinars, and training bootcamps.
    Reads curated events from events.yaml and polls external feeds.
    """

    def __init__(
        self,
        name: str = "Edge Computing Events",
        config_manager: Optional[ConfigManager] = None,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER3_CONFERENCE.value, enabled=enabled)
        self.config = config_manager or ConfigManager()
        self.normalizer = EventNormalizer()
        self.verifier = EventVerifier()
        self.scorer = EventScorer(config_manager=self.config)
        self.events_cache: List[EdgeEvent] = []

    def fetch_events(self) -> List[EdgeEvent]:
        """Fetches and normalizes raw events from curated lists and active feeds."""
        events: List[EdgeEvent] = []
        events_cfg = self.config.events if hasattr(self.config, "events") else {}

        # 1. Collect Curated Events
        curated_list = events_cfg.get("curated_events", []) if isinstance(events_cfg, dict) else []
        for raw in curated_list:
            try:
                event = self.normalizer.normalize(raw)
                events.append(event)
            except Exception as e:
                logger.warning(f"Error normalizing curated event '{raw.get('event_name')}': {e}")

        # 2. Collect from Event Feeds
        feeds = events_cfg.get("event_feeds", []) if isinstance(events_cfg, dict) else []
        for feed_info in feeds:
            if not feed_info.get("enabled", True):
                continue
            feed_url = feed_info.get("url")
            feed_name = feed_info.get("name", "Event Feed")
            try:
                response = self.requester.get(feed_url)
                if not response or response.status_code != 200:
                    continue

                parsed = feedparser.parse(response.content)
                for entry in parsed.entries:
                    title = entry.get("title", "").strip()
                    if not title:
                        continue
                    link = entry.get("link", "").strip()
                    summary = entry.get("summary") or entry.get("description") or ""
                    soup = BeautifulSoup(summary, "html.parser")
                    clean_desc = " ".join(soup.get_text().split())

                    raw_item = {
                        "event_name": title,
                        "description": clean_desc,
                        "url": link,
                        "source": feed_name,
                        "source_url": link,
                        "event_type": feed_info.get("default_event_type", "academic_conference")
                    }
                    event = self.normalizer.normalize(raw_item)
                    events.append(event)
            except Exception as e:
                logger.debug(f"Feed '{feed_name}' poll skipped or failed: {e}")

        # Verify and score all collected events
        verified_events = self.verifier.verify_all(events)
        for ev in verified_events:
            self.scorer.score_event(ev)
        self.events_cache = verified_events
        return verified_events

    def fetch(self) -> List[ResearchItem]:
        """Implements BaseCollector interface, bridging events to ResearchItem."""
        events = self.fetch_events()
        return [event.to_research_item() for event in events]
