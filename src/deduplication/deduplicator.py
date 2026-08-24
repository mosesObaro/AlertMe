"""Multi-stage academic item deduplication engine."""

import re
import difflib
from typing import List, Set, Tuple, Optional
from src.models import ResearchItem
from src.utils.logger import logger


def normalize_doi(doi: Optional[str]) -> Optional[str]:
    """Normalizes DOI by removing prefixes and lowercasing."""
    if not doi:
        return None
    cleaned = doi.strip().lower()
    cleaned = re.sub(r'^https?://(dx\.)?doi\.org/', '', cleaned)
    return cleaned if cleaned else None


def normalize_arxiv_id(arxiv_id: Optional[str]) -> Optional[str]:
    """Normalizes arXiv ID by removing versions (e.g. 2301.12345v2 -> 2301.12345)."""
    if not arxiv_id:
        return None
    cleaned = arxiv_id.strip().lower()
    cleaned = re.sub(r'v\d+$', '', cleaned)
    match = re.search(r'(\d{4}\.\d{4,5}|[a-z\-.]+/\d{7})', cleaned)
    return match.group(1) if match else cleaned


def normalize_url(url: str) -> str:
    """Canonicalizes URL by removing protocol, www, trailing slash, and tracking params."""
    if not url:
        return ""
    cleaned = url.strip().lower()
    cleaned = re.sub(r'^https?://', '', cleaned)
    cleaned = re.sub(r'^www\.', '', cleaned)
    cleaned = re.sub(r'\?.*$', '', cleaned) # remove query params
    return cleaned.rstrip('/')


def normalize_title(title: str) -> str:
    """Normalizes title string for fuzzy comparison."""
    if not title:
        return ""
    # Strip common prefix tags like [Code/Benchmark], [SEC], [PDF]
    cleaned = re.sub(r'^\[[^\]]+\]\s*', '', title)
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned.lower())
    return " ".join(cleaned.split())


def title_similarity(title1: str, title2: str) -> float:
    """Calculates combined token set Jaccard and sequence matcher similarity."""
    t1 = normalize_title(title1)
    t2 = normalize_title(title2)

    if not t1 or not t2:
        return 0.0
    if t1 == t2:
        return 1.0

    # Token set Jaccard
    words1 = set(t1.split())
    words2 = set(t2.split())
    if not words1 or not words2:
        return 0.0

    jaccard = len(words1.intersection(words2)) / len(words1.union(words2))
    seq_ratio = difflib.SequenceMatcher(None, t1, t2).ratio()

    # Weighted combination
    return 0.5 * jaccard + 0.5 * seq_ratio


class Deduplicator:
    """Deduplicates research items across DOIs, arXiv IDs, URLs, and fuzzy titles."""

    def __init__(self, similarity_threshold: float = 0.82):
        self.similarity_threshold = similarity_threshold

    def is_duplicate(self, item: ResearchItem, seen_pool: List[ResearchItem]) -> Tuple[bool, Optional[ResearchItem]]:
        """Checks if item matches any item in the existing pool."""
        item_doi = normalize_doi(item.doi)
        item_arxiv = normalize_arxiv_id(item.arxiv_id)
        item_url = normalize_url(item.url)

        for existing in seen_pool:
            # 1. Exact DOI Match
            existing_doi = normalize_doi(existing.doi)
            if item_doi and existing_doi and item_doi == existing_doi:
                return True, existing

            # 2. Exact arXiv ID Match
            existing_arxiv = normalize_arxiv_id(existing.arxiv_id)
            if item_arxiv and existing_arxiv and item_arxiv == existing_arxiv:
                return True, existing

            # 3. Exact Canonical URL Match
            existing_url = normalize_url(existing.url)
            if item_url and existing_url and item_url == existing_url:
                return True, existing

            # 4. Fuzzy Title Similarity
            sim = title_similarity(item.title, existing.title)
            if sim >= self.similarity_threshold:
                # If titles are very similar, check authors if available or accept match
                return True, existing

        return False, None

    def merge_items(self, primary: ResearchItem, secondary: ResearchItem) -> ResearchItem:
        """Enriches the primary item with any missing metadata from secondary item."""
        if not primary.doi and secondary.doi:
            primary.doi = secondary.doi
        if not primary.arxiv_id and secondary.arxiv_id:
            primary.arxiv_id = secondary.arxiv_id
        if not primary.abstract and secondary.abstract:
            primary.abstract = secondary.abstract
        if len(secondary.authors) > len(primary.authors):
            primary.authors = secondary.authors
        if not primary.venue and secondary.venue:
            primary.venue = secondary.venue
        if secondary.topics:
            combined_topics = list(set(primary.topics + secondary.topics))
            primary.topics = combined_topics
        return primary

    def deduplicate(
        self,
        new_items: List[ResearchItem],
        seen_history_ids: Optional[Set[str]] = None
    ) -> List[ResearchItem]:
        """Deduplicates a list of newly collected items against historical IDs and itself."""
        seen_ids = seen_history_ids or set()
        unique_items: List[ResearchItem] = []

        for item in new_items:
            # Check against historical ID hashes
            if item.id in seen_ids:
                continue

            # Check DOI / arXiv ID in historical IDs
            norm_doi = normalize_doi(item.doi)
            if norm_doi and f"doi_{norm_doi}" in seen_ids:
                continue

            norm_arxiv = normalize_arxiv_id(item.arxiv_id)
            if norm_arxiv and f"arxiv_{norm_arxiv}" in seen_ids:
                continue

            # Check against unique items collected in current batch
            is_dup, existing_match = self.is_duplicate(item, unique_items)
            if is_dup and existing_match:
                # Merge richer metadata into existing
                self.merge_items(existing_match, item)
            else:
                unique_items.append(item)

        logger.info(f"Deduplication complete: {len(new_items)} raw items -> {len(unique_items)} unique items.")
        return unique_items
