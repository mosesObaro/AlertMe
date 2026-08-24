"""Universal RSS/Atom feed collector for standards, universities, and industry research."""

import datetime
from typing import List, Optional
import feedparser
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector
from src.models import ResearchItem, ItemType, CredibilityTier
from src.utils.logger import logger


def clean_html_summary(html_text: Optional[str]) -> str:
    """Strips HTML tags and normalizes whitespace."""
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        return " ".join(soup.get_text().split())
    except Exception:
        return html_text.strip()


class RssFeedCollector(BaseCollector):
    """Collects updates from an RSS or Atom feed."""

    def __init__(
        self,
        name: str,
        url: str,
        tier: str = CredibilityTier.TIER1_ACADEMIC_STANDARDS.value,
        default_item_type: str = ItemType.TECH_REPORT.value,
        organization: str = "",
        institution: str = "",
        enabled: bool = True
    ):
        super().__init__(name=name, tier=tier, enabled=enabled)
        self.url = url
        self.default_item_type = default_item_type
        self.organization = organization
        self.institution = institution

    def fetch(self) -> List[ResearchItem]:
        response = self.requester.get(self.url)
        if not response or response.status_code != 200:
            logger.warning(f"Failed to fetch RSS feed [{self.name}] from {self.url}")
            return []

        feed = feedparser.parse(response.content)
        items: List[ResearchItem] = []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if not title:
                continue

            link = entry.get("link", "").strip()
            raw_summary = entry.get("summary") or entry.get("description") or ""
            abstract = clean_html_summary(raw_summary)

            # Date parsing
            pub_date = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                dt = datetime.datetime(*entry.published_parsed[:6])
                pub_date = dt.strftime("%Y-%m-%d")
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                dt = datetime.datetime(*entry.updated_parsed[:6])
                pub_date = dt.strftime("%Y-%m-%d")

            # Authors
            authors = []
            if hasattr(entry, "author") and entry.author:
                authors.append(entry.author.strip())
            elif hasattr(entry, "authors"):
                for a in entry.authors:
                    if "name" in a and a["name"]:
                        authors.append(a["name"].strip())

            # Item Type detection
            lower_title = title.lower()
            if "standard" in lower_title or "spec" in lower_title or "etsi" in lower_title:
                item_type = ItemType.STANDARDS_UPDATE.value
            elif "phd" in lower_title or "fellowship" in lower_title or "opening" in lower_title:
                item_type = ItemType.PHD_OPPORTUNITY.value
            elif "cfp" in lower_title or "call for papers" in lower_title:
                item_type = ItemType.CONFERENCE_CFP.value
            else:
                item_type = self.default_item_type

            venue = self.organization or self.institution or self.name

            item = ResearchItem(
                title=title,
                url=link,
                source=self.name,
                source_tier=self.tier,
                item_type=item_type,
                authors=authors,
                publication_date=pub_date,
                abstract=abstract,
                venue=venue,
                institution=self.institution
            )
            items.append(item)

        return items
