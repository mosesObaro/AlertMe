"""Semantic Scholar Academic Graph API collector."""

from typing import List
from src.collectors.base import BaseCollector
from src.models import ResearchItem, ItemType, CredibilityTier
from src.utils.logger import logger

S2_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


class SemanticScholarCollector(BaseCollector):
    """Fetches high-impact research papers from Semantic Scholar."""

    def __init__(
        self,
        name: str = "Semantic Scholar Graph",
        query: str = "edge computing resource allocation offloading",
        limit: int = 25,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value, enabled=enabled)
        self.query = query
        self.limit = limit

    def fetch(self) -> List[ResearchItem]:
        params = {
            "query": self.query,
            "limit": min(self.limit, 50),
            "fields": "title,authors,abstract,venue,year,publicationDate,externalIds,url,citationCount,openAccessPdf"
        }

        response = self.requester.get(S2_API_URL, params=params)
        if not response or response.status_code != 200:
            logger.warning(f"Failed to fetch Semantic Scholar data. Status: {getattr(response, 'status_code', 'None')}")
            return []

        data = response.json()
        papers = data.get("data", [])
        items: List[ResearchItem] = []

        for paper in papers:
            title = paper.get("title")
            if not title:
                continue

            external_ids = paper.get("externalIds") or {}
            doi = external_ids.get("DOI")
            arxiv_id = external_ids.get("ArXiv")
            url = paper.get("url") or (f"https://doi.org/{doi}" if doi else "")

            # Authors
            authors = [a.get("name", "") for a in paper.get("authors", []) if a.get("name")]

            # Venue
            venue = paper.get("venue") or ""

            # Abstract
            abstract = paper.get("abstract") or ""

            pub_date = paper.get("publicationDate") or str(paper.get("year", ""))

            is_survey = "survey" in title.lower() or "review" in title.lower()
            item_type = ItemType.SURVEY.value if is_survey else ItemType.PAPER.value

            item = ResearchItem(
                title=title,
                url=url,
                source="Semantic Scholar",
                source_tier=self.tier,
                item_type=item_type,
                authors=authors,
                doi=doi,
                arxiv_id=arxiv_id,
                publication_date=pub_date,
                abstract=abstract,
                venue=venue,
                raw_metadata={"citation_count": paper.get("citationCount", 0)}
            )
            items.append(item)

        return items
