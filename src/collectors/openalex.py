"""OpenAlex Works API collector for academic papers and proceedings."""

from typing import List, Dict, Any, Optional
from src.collectors.base import BaseCollector
from src.models import ResearchItem, ItemType, CredibilityTier
from src.utils.logger import logger

OPENALEX_API_URL = "https://api.openalex.org/works"


def reconstruct_abstract_from_inverted_index(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """Reconstructs full text abstract from OpenAlex's abstract_inverted_index format."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    try:
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(word for _, word in word_positions)
    except Exception:
        return ""


class OpenAlexCollector(BaseCollector):
    """Fetches high-quality published academic works from OpenAlex."""

    def __init__(
        self,
        name: str = "OpenAlex Edge Research",
        search_query: str = "edge computing OR edge intelligence OR mobile edge computing",
        max_results: int = 30,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value, enabled=enabled)
        self.search_query = search_query
        self.max_results = max_results

    def fetch(self) -> List[ResearchItem]:
        params = {
            "search": self.search_query,
            "sort": "publication_date:desc",
            "per_page": min(self.max_results, 50),
            "filter": "type:article|proceedings-article|book-chapter"
        }

        response = self.requester.get(OPENALEX_API_URL, params=params)
        if not response or response.status_code != 200:
            logger.warning(f"Failed to fetch OpenAlex data. Status: {getattr(response, 'status_code', 'None')}")
            return []

        data = response.json()
        results = data.get("results", [])
        items: List[ResearchItem] = []

        for work in results:
            title = work.get("title") or ""
            if not title:
                continue

            # Primary URL or DOI URL
            doi = work.get("doi")
            primary_location = work.get("primary_location") or {}
            landing_page_url = primary_location.get("landing_page_url") or doi or f"https://openalex.org/{work.get('id', '')}"

            # Authors
            authors = []
            for authorship in work.get("authorships", []):
                author_obj = authorship.get("author", {})
                display_name = author_obj.get("display_name")
                if display_name:
                    authors.append(display_name)

            # Venue / Journal / Conference
            source_obj = primary_location.get("source") or {}
            venue = source_obj.get("display_name") or ""

            # Abstract
            inverted_index = work.get("abstract_inverted_index")
            abstract = reconstruct_abstract_from_inverted_index(inverted_index)

            # Topics / Concepts
            topics = []
            for concept in work.get("concepts", []):
                c_name = concept.get("display_name")
                if c_name:
                    topics.append(c_name)

            pub_date = work.get("publication_date") or ""
            is_survey = "survey" in title.lower() or "review" in title.lower()
            item_type = ItemType.SURVEY.value if is_survey else ItemType.PAPER.value

            item = ResearchItem(
                title=title,
                url=landing_page_url,
                source="OpenAlex",
                source_tier=self.tier,
                item_type=item_type,
                authors=authors,
                doi=doi.replace("https://doi.org/", "") if doi else None,
                publication_date=pub_date,
                abstract=abstract,
                venue=venue,
                topics=topics,
                raw_metadata={"cited_by_count": work.get("cited_by_count", 0)}
            )
            items.append(item)

        return items
