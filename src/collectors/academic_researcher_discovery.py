"""Academic researcher discovery engine using OpenAlex, Semantic Scholar, Crossref, and arXiv."""

from typing import List, Dict, Any, Optional, Set
import re
from src.models import (
    ResearchItem,
    ResearcherProfile,
    RecruitmentStatus
)
from src.ranking.opportunity_scorer import OpportunityScorer
from src.utils.config_loader import ConfigManager
from src.utils.rate_limiter import PoliteRequester
from src.utils.logger import logger


class AcademicResearcherDiscovery:
    """Discovers high-impact researchers through academic publication streams and metadata."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.scorer = OpportunityScorer(self.config)
        self.requester = PoliteRequester()
        self.target_countries = self.scorer.target_countries

    def discover_candidate_researchers(
        self,
        recent_items: List[ResearchItem],
        existing_registry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, ResearcherProfile]:
        """Profiles researchers from recent high-scoring Edge/Distributed publications."""
        registry: Dict[str, ResearcherProfile] = {}
        if existing_registry:
            for k, v in existing_registry.items():
                if isinstance(v, dict):
                    registry[k] = ResearcherProfile.from_dict(v)
                elif isinstance(v, ResearcherProfile):
                    registry[k] = v

        for item in recent_items:
            # Only consider academically rigorous items
            if not item.score or item.score.final_score < 6.8:
                continue

            for author in item.authors:
                clean_name = self._clean_author_name(author)
                if not clean_name or len(clean_name.split()) < 2:
                    continue

                if clean_name not in registry:
                    country = self._infer_country(item.location, item.institution, item.venue)
                    profile = ResearcherProfile(
                        name=clean_name,
                        institution=item.institution or "Academic Institution",
                        country=country,
                        research_areas=list(set(item.topics or item.score.matched_topics)),
                        recruitment_status=RecruitmentStatus.NOT_VERIFIED.value
                    )
                    registry[clean_name] = profile

                prof = registry[clean_name]
                score_val = item.score.final_score if item.score else 7.0
                curr_pub = prof.publication_count
                prof.publication_count += 1
                prof.average_relevance = round((prof.average_relevance * curr_pub + score_val) / (curr_pub + 1), 1)

                # Update institution if generic
                if item.institution and prof.institution in ["Academic Institution", ""]:
                    prof.institution = item.institution

                # Update country if unknown
                if not prof.country or prof.country == "Unknown":
                    prof.country = self._infer_country(item.location, item.institution, item.venue)

                # Merge topics
                for t in (item.topics or item.score.matched_topics):
                    if t not in prof.research_areas:
                        prof.research_areas.append(t)

                # Append recent paper
                existing_titles = [p.get("title") for p in prof.recent_papers]
                if item.title not in existing_titles:
                    prof.recent_papers.append({
                        "title": item.title,
                        "url": item.url,
                        "date": item.publication_date,
                        "venue": item.venue or item.source,
                        "score": item.score.final_score
                    })
                    prof.recent_papers = prof.recent_papers[-5:] # Retain latest 5

                # Extract supplementary academic links from item metadata if available
                raw = item.raw_metadata or {}
                if "orcid" in raw and not prof.orcid:
                    prof.orcid = raw["orcid"]
                if "semantic_scholar_url" in raw and not prof.semantic_scholar_url:
                    prof.semantic_scholar_url = raw["semantic_scholar_url"]
                if "google_scholar_url" in raw and not prof.google_scholar_url:
                    prof.google_scholar_url = raw["google_scholar_url"]

        # Score and rank all candidate researchers
        for prof in registry.values():
            self.scorer.score_researcher(prof)

        logger.info(f"Discovered and scored {len(registry)} candidate academic researchers.")
        return registry

    def _clean_author_name(self, name: str) -> str:
        """Cleans academic author name strings."""
        n = re.sub(r'\(.*?\)', '', name)
        n = re.sub(r'[0-9*†‡§]', '', n)
        n = " ".join(n.split()).strip()
        # Filter out organizations mistakenly parsed as authors
        if any(w in n.lower() for w in ["association", "consortium", "working group", "ieee", "acm", "nist"]):
            return ""
        return n

    def _infer_country(self, location: str, institution: str, venue: str) -> str:
        """Heuristic to resolve country from location or prominent institution."""
        text = f"{location} {institution} {venue}".lower()
        country_mappings = {
            "Germany": ["germany", "deutschland", "tum", "munich", "berlin", "rwth", "darmstadt", "karlsruhe", "tu wien"],
            "United Kingdom": ["united kingdom", "uk", "england", "scotland", "cambridge", "oxford", "imperial", "ucl", "edinburgh", "bristol"],
            "Canada": ["canada", "toronto", "waterloo", "mcgill", "ubc", "montreal", "alberta", "british columbia"],
            "Hong Kong": ["hong kong", "hkust", "hku", "cuhk", "polyu", "cityu"],
            "Japan": ["japan", "tokyo", "kyoto", "osaka", "tohoku", "nagoya", "nii"],
            "United States": ["united states", "usa", "us", "mit", "stanford", "berkeley", "cmu", "princeton", "purdue", "texas", "illinois", "georgia tech", "california", "michigan"]
        }
        for country, kws in country_mappings.items():
            if any(re.search(r'\b' + re.escape(kw) + r'\b', text) for kw in kws):
                return country
        return "International"
