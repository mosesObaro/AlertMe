"""
Multi-Factor Scoring and Relevance Matching Engine for Country Supervisor Intelligence.
Produces transparent, explainable suitability scores for universities and professors.
"""

from typing import List, Dict, Tuple, Any, Optional
from .models import UniversityProfile, ResearcherProfile, FundingOpportunity
from .config import (
    UNIVERSITY_SCORING_WEIGHTS, PROFESSOR_SCORING_WEIGHTS,
    DEFAULT_APPLICANT_PROFILE, RESEARCH_KEYWORDS
)
from .discovery import DiscoveryEngine

class ScoringEngine:
    """Calculates explainable suitability and alignment scores."""

    @staticmethod
    def score_university(uni: UniversityProfile, profile_interests: Optional[List[str]] = None) -> float:
        """Computes 0-100 suitability score for a university."""
        interests = profile_interests or DEFAULT_APPLICANT_PROFILE["research_interests"]

        # 1. Research alignment (35%)
        dept_text = " ".join(uni.relevant_departments + uni.relevant_research_centres).lower()
        topic_score, _ = DiscoveryEngine.match_research_keywords(dept_text)

        # 2. Funding availability (25%)
        fund_map = {"High": 100.0, "Medium": 75.0, "Moderate": 50.0}
        fund_score = fund_map.get(uni.funding_availability_rating, 75.0)

        # 3. Faculty density (20%)
        density_score = min(100.0, len(uni.relevant_departments) * 25.0 + len(uni.relevant_research_centres) * 15.0)

        # 4. Infrastructure strength (10%)
        infra_score = 90.0 if len(uni.relevant_research_centres) >= 2 else 70.0

        # 5. International access (10%)
        intl_score = 95.0

        final_score = (
            topic_score * UNIVERSITY_SCORING_WEIGHTS["research_alignment"] +
            fund_score * UNIVERSITY_SCORING_WEIGHTS["funding_availability"] +
            density_score * UNIVERSITY_SCORING_WEIGHTS["faculty_density"] +
            infra_score * UNIVERSITY_SCORING_WEIGHTS["infrastructure_strength"] +
            intl_score * UNIVERSITY_SCORING_WEIGHTS["international_access"]
        )
        return round(min(100.0, max(0.0, final_score)), 1)

    @staticmethod
    def score_professor(prof: ResearcherProfile, profile_interests: Optional[List[str]] = None) -> Tuple[float, List[str]]:
        """
        Computes 0-100 alignment score for a professor and generates explainable reasons.
        Returns (final_score, list_of_reasons).
        """
        interests = profile_interests or DEFAULT_APPLICANT_PROFILE["research_interests"]

        # 1. Research alignment (35%)
        prof_text = " ".join(prof.research_interests) + " " + prof.research_summary + " " + prof.edge_relevance
        for pub in prof.publications:
            prof_text += f" {pub.title} {pub.research_problem} {pub.key_contribution}"

        raw_alignment, hits = DiscoveryEngine.match_research_keywords(prof_text)

        # 2. Current activity (20%)
        recent_pubs = [p for p in prof.publications if getattr(p, "is_recent", False) or getattr(p, "year", 2020) >= 2023]
        activity_score = 100.0 if len(recent_pubs) >= 1 else 75.0
        if prof.current_projects:
            activity_score = min(100.0, activity_score + 10.0)

        # 3. PhD recruitment (25%)
        rec_status = prof.recruitment.status.upper() if prof.recruitment else "UNKNOWN"
        rec_map = {
            "CONFIRMED_ACTIVE": 100.0,
            "STRONG_EVIDENCE": 85.0,
            "POSSIBLE": 60.0,
            "UNKNOWN": 50.0,
            "NOT_CURRENTLY_RECRUITING": 15.0,
            "RECRUITMENT_STALE": 30.0
        }
        rec_score = rec_map.get(rec_status, 50.0)

        # 4. Academic stature (10%)
        tier_map = {"Tier 1": 100.0, "Tier 2": 80.0, "Tier 3": 60.0}
        stature_score = tier_map.get(prof.priority_tier, 80.0)

        # 5. Research accessibility (10%)
        access_score = 50.0
        if prof.official_profile_url:
            access_score += 20.0
        if prof.personal_website:
            access_score += 15.0
        if prof.google_scholar or prof.dblp:
            access_score += 15.0
        access_score = min(100.0, access_score)

        final_score = (
            raw_alignment * PROFESSOR_SCORING_WEIGHTS["research_alignment"] +
            activity_score * PROFESSOR_SCORING_WEIGHTS["current_activity"] +
            rec_score * PROFESSOR_SCORING_WEIGHTS["phd_recruitment"] +
            stature_score * PROFESSOR_SCORING_WEIGHTS["academic_stature"] +
            access_score * PROFESSOR_SCORING_WEIGHTS["research_accessibility"]
        )
        final_score = round(min(100.0, max(0.0, final_score)), 1)

        # Generate explainable reasons
        reasons = []
        if hits.get("core", 0) > 0:
            reasons.append("Direct research publications in Edge Computing and Edge Intelligence architectures.")
        if hits.get("distributed_systems", 0) > 0:
            reasons.append("Strong focus on Distributed Systems, consensus, and decentralized computation.")
        if rec_status in ["CONFIRMED_ACTIVE", "STRONG_EVIDENCE"]:
            reasons.append(f"Documented active doctoral recruitment evidence: '{prof.recruitment.evidence_text[:80]}...'")
        if recent_pubs:
            reasons.append(f"Active recent publication track record including '{recent_pubs[0].title}' ({recent_pubs[0].year}).")
        if prof.current_projects:
            reasons.append(f"Leads active research projects: {', '.join(prof.current_projects[:2])}.")

        return final_score, reasons
