"""arXiv API collector for preprints and papers in cs.DC, cs.NI, cs.AI."""

import xml.etree.ElementTree as ET
import re
from typing import List
from src.collectors.base import BaseCollector
from src.models import ResearchItem, ItemType, CredibilityTier
from src.utils.logger import logger

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivCollector(BaseCollector):
    """Fetches recently published preprints and papers from arXiv."""

    def __init__(
        self,
        name: str = "arXiv Edge & Distributed Systems",
        query: str = 'cat:cs.DC AND (all:"edge computing" OR all:"edge intelligence" OR all:"mobile edge computing" OR all:"edge AI")',
        max_results: int = 30,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value, enabled=enabled)
        self.query = query
        self.max_results = max_results

    def fetch(self) -> List[ResearchItem]:
        params = {
            "search_query": self.query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(self.max_results)
        }

        response = self.requester.get(ARXIV_API_URL, params=params)
        if not response or response.status_code != 200:
            logger.warning(f"Failed to fetch arXiv data. Status: {getattr(response, 'status_code', 'None')}")
            return []

        return self._parse_feed(response.text)

    def _parse_feed(self, xml_text: str) -> List[ResearchItem]:
        items: List[ResearchItem] = []
        try:
            root = ET.fromstring(xml_text)
            for entry in root.findall("atom:entry", ATOM_NS):
                title_elem = entry.find("atom:title", ATOM_NS)
                summary_elem = entry.find("atom:summary", ATOM_NS)
                id_elem = entry.find("atom:id", ATOM_NS)
                published_elem = entry.find("atom:published", ATOM_NS)
                doi_elem = entry.find("arxiv:doi", ATOM_NS)

                if title_elem is None or id_elem is None:
                    continue

                raw_title = title_elem.text or ""
                title = " ".join(raw_title.strip().split())
                abstract = " ".join((summary_elem.text or "").strip().split()) if summary_elem is not None else ""
                url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
                pub_date = (published_elem.text or "")[:10] if published_elem is not None else ""
                doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

                # Extract raw arXiv ID from URL (e.g. http://arxiv.org/abs/2301.12345v1 -> 2301.12345)
                arxiv_id_match = re.search(r'abs/([a-zA-Z0-9.\-]+)', url)
                arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else None

                # Authors
                authors = []
                for author_elem in entry.findall("atom:author", ATOM_NS):
                    name_elem = author_elem.find("atom:name", ATOM_NS)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                # Categories / Topics
                topics = []
                for cat_elem in entry.findall("atom:category", ATOM_NS):
                    term = cat_elem.attrib.get("term")
                    if term:
                        topics.append(term)

                # Check if survey
                is_survey = "survey" in title.lower() or "review" in title.lower()
                item_type = ItemType.SURVEY.value if is_survey else ItemType.PREPRINT.value

                item = ResearchItem(
                    title=title,
                    url=url,
                    source="arXiv",
                    source_tier=self.tier,
                    item_type=item_type,
                    authors=authors,
                    doi=doi,
                    arxiv_id=arxiv_id,
                    publication_date=pub_date,
                    abstract=abstract,
                    venue="arXiv CS",
                    topics=topics
                )
                items.append(item)

        except Exception as e:
            logger.error(f"Error parsing arXiv XML feed: {e}", exc_info=True)

        return items
