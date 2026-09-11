"""PhD and Fellowship Opportunities collector with multi-country and dependant support awareness."""

from typing import List, Optional, Dict, Any
import re
import feedparser
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector
from src.models import (
    ResearchItem,
    PhDOpportunity,
    ItemType,
    CredibilityTier,
    RecruitmentStatus,
    FundingStatus,
    DependantSupportClassification
)
from src.ranking.opportunity_scorer import OpportunityScorer
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger


class OpportunityCollector(BaseCollector):
    """Collects and standardizes PhD positions, studentships, and lab openings across target countries."""

    def __init__(
        self,
        name: str = "PhD & Research Opportunities",
        config_manager: Optional[ConfigManager] = None,
        feeds: Optional[List[str]] = None,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER2_UNIVERSITY_LAB.value, enabled=enabled)
        self.config = config_manager or ConfigManager()
        self.scorer = OpportunityScorer(self.config)
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

                    # Check if relevant to Edge, Distributed, Systems, Networks, or AI/ML
                    combined_text = f"{title} {clean_desc}".lower()
                    core_keywords = [
                        "edge", "cloud", "distributed", "iot", "systems", "network",
                        "federated", "5g", "6g", "computing", "pervasive", "fog",
                        "inference", "offloading", "tinyml", "resource allocation"
                    ]

                    if not any(re.search(r'\b' + re.escape(kw) + r'\b', combined_text) for kw in core_keywords):
                        continue

                    # Extract metadata
                    institution = entry.get("author") or self._extract_institution(clean_desc, title)
                    country = self._infer_country(institution, clean_desc, feed_url)
                    funding_status, funding_info = self.scorer.classify_funding_status(combined_text)
                    rec_status, rec_evidence = self.scorer.classify_recruitment_status(combined_text)
                    if rec_status == RecruitmentStatus.NOT_VERIFIED.value:
                        # Job advert itself is a strong indicator of active recruitment
                        rec_status = RecruitmentStatus.ACTIVELY_RECRUITING.value
                        rec_evidence = f"Advertised vacancy: {title}"

                    dep_status, dep_info = self.scorer.classify_dependant_support(combined_text, country)
                    matched_areas = [kw.title() for kw in core_keywords if kw in combined_text]

                    opp = PhDOpportunity(
                        title=title,
                        university=institution or "University Research Group",
                        country=country,
                        research_areas=matched_areas[:4],
                        opportunity_type="phd_studentship",
                        funding_status=funding_status,
                        funding_amount=funding_info,
                        eligibility=clean_desc[:300],
                        dependant_support_info=dep_info,
                        dependant_support_classification=dep_status,
                        source_url=link,
                        source=entry.get("publisher") or "Academic Opportunities",
                        recruitment_status=rec_status,
                        recruitment_evidence=rec_evidence
                    )

                    # Score opportunity
                    self.scorer.score_opportunity(opp)

                    # Convert to ResearchItem with rich opportunity_data
                    item = opp.to_research_item()
                    items.append(item)

            except Exception as e:
                logger.warning(f"Error fetching opportunity feed {feed_url}: {e}")

        logger.info(f"Discovered and scored {len(items)} PhD opportunities from institutional feeds.")
        return items

    def _extract_institution(self, desc: str, title: str) -> str:
        m = re.search(r'(University of [A-Za-z\s]+|[A-Za-z\s]+ University|[A-Za-z\s]+ Institute of Technology)', f"{title} {desc}")
        if m:
            return m.group(0).strip()
        return "Academic Institution"

    def _infer_country(self, institution: str, desc: str, url: str) -> str:
        text = f"{institution} {desc} {url}".lower()
        if ".ac.uk" in text or "uk" in text or "united kingdom" in text:
            return "United Kingdom"
        elif "germany" in text or ".de" in text or "tum" in text or "munich" in text:
            return "Germany"
        elif "canada" in text or ".ca" in text or "toronto" in text or "waterloo" in text:
            return "Canada"
        elif "hong kong" in text or ".hk" in text or "hkust" in text or "hku" in text:
            return "Hong Kong"
        elif "japan" in text or ".jp" in text or "tokyo" in text or "kyoto" in text:
            return "Japan"
        elif "usa" in text or "united states" in text or ".edu" in text:
            return "United States"
        return "International"
