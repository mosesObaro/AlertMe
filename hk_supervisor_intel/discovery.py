"""
Discovery and institutional filtering engine for the Hong Kong PhD Supervisor Intelligence module.
Strictly enforces the 8-university boundary, normalizes institutional aliases,
evaluates edge computing relevance, and deduplicates researcher profiles.
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from .config import TARGET_HONG_KONG_UNIVERSITIES, UNIVERSITY_ALIASES, RESEARCH_KEYWORDS
from .models import ResearcherProfile

class DiscoveryEngine:
    """Enforces institutional boundaries and edge computing research qualification."""

    # Explicit exclusion keywords for other non-target tertiary institutions in Hong Kong
    EXCLUDED_INSTITUTIONS = [
        "hang seng", "shue yan", "metropolitan", "open university", "chu hai",
        "performing arts", "caritas", "tung wah", "ouhk", "hkmu", "hsuhk", "hksyu"
    ]

    @classmethod
    def normalize_university_name(cls, raw_name: str) -> Optional[str]:
        """
        Normalizes a university name or alias to the canonical target name.
        Returns None if the university is outside the 8 target institutions.
        """
        if not raw_name:
            return None
            
        clean = raw_name.strip().lower()
        clean = re.sub(r"[,\.\(\)]", "", clean)
        clean = re.sub(r"\s+", " ", clean)

        # 1. Reject explicit outside Hong Kong institutions
        for excluded in cls.EXCLUDED_INSTITUTIONS:
            if excluded in clean:
                return None

        # 2. Check exact alias match
        if clean in UNIVERSITY_ALIASES:
            return UNIVERSITY_ALIASES[clean]

        # 3. Check exact canonical match
        for canon in TARGET_HONG_KONG_UNIVERSITIES:
            if canon.lower() == clean:
                return canon

        # 4. Check word-boundary alias matching (longer aliases first)
        sorted_aliases = sorted(UNIVERSITY_ALIASES.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, clean):
                return UNIVERSITY_ALIASES[alias]

        return None

    @classmethod
    def is_target_university(cls, university_name: str) -> bool:
        """Strictly verifies if a university is one of the 8 canonical target institutions."""
        return cls.normalize_university_name(university_name) in TARGET_HONG_KONG_UNIVERSITIES

    @classmethod
    def filter_by_target_university(cls, researchers: List[ResearcherProfile]) -> List[ResearcherProfile]:
        """
        Filters researcher profiles, strictly rejecting any outside the 8 target universities.
        Normalizes university name on approved candidates.
        """
        qualified = []
        for r in researchers:
            canon = cls.normalize_university_name(r.university)
            if canon:
                r.university = canon
                qualified.append(r)
        return qualified

    @staticmethod
    def evaluate_edge_relevance(interests: List[str], summary: str) -> Tuple[float, Dict[str, int]]:
        """
        Evaluates research overlap with Edge Computing, Distributed Systems, 5G, AIoT, and Optimization.
        Returns (relevance_score_0_to_100, keyword_hit_counts).
        """
        text = " ".join(interests).lower() + " " + summary.lower()
        hits = {cat: 0 for cat in RESEARCH_KEYWORDS}
        total_hits = 0

        for cat, keywords in RESEARCH_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", text):
                    hits[cat] += 1
                    total_hits += 1

        # Core edge and distributed systems carry higher weight
        weighted_score = (
            hits["core"] * 25.0 +
            hits["distributed_systems"] * 20.0 +
            hits["optimization_systems"] * 20.0 +
            hits["ai_iot"] * 18.0 +
            hits["networking"] * 17.0
        )

        final_score = min(100.0, weighted_score)
        return final_score, hits

    @classmethod
    def deduplicate_researchers(cls, researchers: List[ResearcherProfile]) -> List[ResearcherProfile]:
        """Deduplicates researchers by canonical name and normalized university."""
        seen = set()
        deduped = []
        
        for r in researchers:
            norm_uni = cls.normalize_university_name(r.university) or r.university
            key = (r.name.strip().lower(), norm_uni.lower())
            if key not in seen:
                seen.add(key)
                deduped.append(r)
                
        return deduped
