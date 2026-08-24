"""Crossref API collector for published journal articles and proceedings."""

import re
from typing import List, Optional
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector
from src.models import ResearchItem, ItemType, CredibilityTier
from src.utils.logger import logger

CROSSREF_API_URL = "https://api.crossref.org/works"


def clean_crossref_abstract(raw_abstract: Optional[str]) -> str:
    """Strips XML/JATS markup from Crossref abstracts."""
    if not raw_abstract:
        return ""
    try:
        soup = BeautifulSoup(raw_abstract, "html.parser")
        return " ".join(soup.get_text().split())
    except Exception:
        return re.sub(r'<[^>]+>', ' ', raw_abstract).strip()


class CrossrefCollector(BaseCollector):
    """Fetches recently indexed works from Crossref (IEEE, ACM, Springer, Elsevier)."""

    def __init__(
        self,
        name: str = "Crossref Works",
        query: str = "edge computing edge intelligence",
        rows: int = 25,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value, enabled=enabled)
        self.query = query
        self.rows = rows

    def fetch(self) -> List[ResearchItem]:
        params = {
            "query": self.query,
            "sort": "published",
            "order": "desc",
            "rows": min(self.rows, 50),
            "mailto": "obaro.moses.phd@example.com"
        }

        response = self.requester.get(CROSSREF_API_URL, params=params)
        if not response or response.status_code != 200:
            logger.warning(f"Failed to fetch Crossref data. Status: {getattr(response, 'status_code', 'None')}")
            return []

        data = response.json()
        message = data.get("message", {})
        works = message.get("items", [])
        items: List[ResearchItem] = []

        for work in works:
            title_list = work.get("title", [])
            if not title_list:
                continue
            title = " ".join(title_list[0].split())
            doi = work.get("DOI")
            url = work.get("URL") or (f"https://doi.org/{doi}" if doi else "")

            # Authors
            authors = []
            for author_obj in work.get("author", []):
                given = author_obj.get("given", "")
                family = author_obj.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

            # Venue / Journal / Publisher
            container_titles = work.get("container-title", [])
            venue = container_titles[0] if container_titles else work.get("publisher", "")

            # Publication Date
            pub_date = ""
            published_parts = work.get("published", {}).get("date-parts", [[]])[0]
            if published_parts:
                pub_date = "-".join(f"{part:02d}" for part in published_parts)

            # Abstract
            abstract = clean_crossref_abstract(work.get("abstract"))

            # Topics / Subject
            topics = work.get("subject", [])

            is_survey = "survey" in title.lower() or "review" in title.lower()
            item_type = ItemType.SURVEY.value if is_survey else ItemType.PAPER.value

            item = ResearchItem(
                title=title,
                url=url,
                source="Crossref",
                source_tier=self.tier,
                item_type=item_type,
                authors=authors,
                doi=doi,
                publication_date=pub_date,
                abstract=abstract,
                venue=venue,
                topics=topics
            )
            items.append(item)

        return items
