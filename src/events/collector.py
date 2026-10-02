"""Event collectors for academic and industrial events.
Includes generic ConfigurableEventCollector, EdgeEventCollector, and MLEmbeddedIoTEventCollector.
"""

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


class ConfigurableEventCollector(BaseCollector):
    """
    Generic, configuration-driven event collector.
    Discovers academic conferences, industry summits, workshops, webinars, and training bootcamps.
    Reads curated events from specified configuration and polls external feeds.
    """

    def __init__(
        self,
        name: str = "Academic & Industry Events",
        config_manager: Optional[ConfigManager] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        domain: str = "general",
        tier: str = CredibilityTier.TIER3_CONFERENCE.value,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=tier, enabled=enabled)
        self.config = config_manager or ConfigManager()
        self.domain = domain
        self._explicit_config = config_dict
        self.normalizer = EventNormalizer()
        self.verifier = EventVerifier()
        self.scorer = EventScorer(
            config_manager=self.config,
            domain=self.domain,
            search_specs=self.events_config.get("search_specifications") if isinstance(self.events_config, dict) else None
        )
        self.events_cache: List[EdgeEvent] = []

    @property
    def events_config(self) -> Dict[str, Any]:
        """Resolves configuration dictionary for this collector."""
        if self._explicit_config is not None:
            return self._explicit_config
        if hasattr(self.config, "get_events_config"):
            return self.config.get_events_config(self.domain)
        return self.config.events if hasattr(self.config, "events") else {}

    def fetch_events(self) -> List[EdgeEvent]:
        """Fetches and normalizes raw events from curated lists and active feeds."""
        events: List[EdgeEvent] = []
        events_cfg = self.events_config

        # 1. Collect Curated Events
        curated_list = events_cfg.get("curated_events", []) if isinstance(events_cfg, dict) else []
        for raw in curated_list:
            try:
                event = self.normalizer.normalize(raw)
                event.domain = self.domain
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
                    event.domain = self.domain
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


class EdgeEventCollector(ConfigurableEventCollector):
    """
    Collects academic conferences, industry summits, workshops, webinars, and training bootcamps
    for the Edge Computing research domain.
    """

    def __init__(
        self,
        name: str = "Edge Computing Events",
        config_manager: Optional[ConfigManager] = None,
        enabled: bool = True
    ):
        cfg_mgr = config_manager or ConfigManager()
        super().__init__(
            name=name,
            config_manager=cfg_mgr,
            domain="edge_computing",
            config_dict=getattr(cfg_mgr, "events", {}),
            enabled=enabled
        )


class MLEmbeddedIoTEventCollector(ConfigurableEventCollector):
    """
    Collects academic conferences, industry summits, workshops, webinars, and training bootcamps
    for Machine Learning, Embedded Systems, and Internet of Things (IoT) domains.
    """

    def __init__(
        self,
        name: str = "ML/Embedded/IoT Events",
        config_manager: Optional[ConfigManager] = None,
        enabled: bool = True
    ):
        cfg_mgr = config_manager or ConfigManager()
        super().__init__(
            name=name,
            config_manager=cfg_mgr,
            domain="ml_embedded_iot",
            config_dict=getattr(cfg_mgr, "ml_iot_events", {}),
            enabled=enabled
        )
