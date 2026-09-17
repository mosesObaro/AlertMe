"""
Discovery and Entity Deduplication Engine for Country-Based Supervisor Intelligence.
Handles university and professor discovery, alias normalization, cross-source deduplication,
and research keyword matching.
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from .models import UniversityProfile, ResearcherProfile, FundingOpportunity
from .config import RESEARCH_KEYWORDS, normalize_country_key

class DiscoveryEngine:
    """Performs multi-signal entity deduplication and research area discovery."""

    @staticmethod
    def normalize_string(text: str) -> str:
        if not text:
            return ""
        clean = text.strip().lower()
        clean = re.sub(r"[,\.\(\)\-\_]", " ", clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean

    @classmethod
    def deduplicate_professors(cls, professors: List[ResearcherProfile]) -> List[ResearcherProfile]:
        """
        Deduplicates professors based on composite key:
        (normalized_name, normalized_university) or ORCID or profile_url.
        """
        seen_keys = set()
        seen_orcids = set()
        seen_urls = set()
        deduped: List[ResearcherProfile] = []

        for p in professors:
            norm_name = cls.normalize_string(p.name)
            norm_uni = cls.normalize_string(p.university)
            key = (norm_name, norm_uni)

            # Check ORCID
            if p.orcid and p.orcid in seen_orcids:
                continue

            # Check exact profile URL
            if p.official_profile_url and p.official_profile_url in seen_urls:
                continue

            # Check composite name + uni
            if key in seen_keys:
                continue

            seen_keys.add(key)
            if p.orcid:
                seen_orcids.add(p.orcid)
            if p.official_profile_url:
                seen_urls.add(p.official_profile_url)
            deduped.append(p)

        return deduped

    @classmethod
    def deduplicate_universities(cls, universities: List[UniversityProfile]) -> List[UniversityProfile]:
        """Deduplicates universities by canonical name and country."""
        seen = set()
        deduped = []
        for u in universities:
            norm_name = cls.normalize_string(u.canonical_name)
            norm_country = cls.normalize_string(u.country)
            key = (norm_name, norm_country)
            if key not in seen:
                seen.add(key)
                deduped.append(u)
        return deduped

    @classmethod
    def deduplicate_funding(cls, opportunities: List[FundingOpportunity]) -> List[FundingOpportunity]:
        """Deduplicates funding opportunities by title and university."""
        seen = set()
        deduped = []
        for fo in opportunities:
            norm_title = cls.normalize_string(fo.title)
            norm_uni = cls.normalize_string(fo.university)
            key = (norm_title, norm_uni)
            if key not in seen:
                seen.add(key)
                deduped.append(fo)
        return deduped

    @staticmethod
    def match_research_keywords(text: str) -> Tuple[float, Dict[str, int]]:
        """
        Evaluates keyword overlap across Edge Computing, Distributed Systems, Networking,
        AI/IoT, and Optimization domains. Returns (score_0_to_100, hit_counts_dict).
        """
        lower_text = text.lower()
        hits = {cat: 0 for cat in RESEARCH_KEYWORDS}

        for cat, keywords in RESEARCH_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", lower_text):
                    hits[cat] += 1

        weighted_score = (
            hits["core"] * 25.0 +
            hits["distributed_systems"] * 20.0 +
            hits["optimization_systems"] * 20.0 +
            hits["ai_iot"] * 18.0 +
            hits["networking"] * 17.0
        )
        final_score = min(100.0, weighted_score)
        return final_score, hits
