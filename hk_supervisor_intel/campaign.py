"""
10-Week PhD Application Campaign Manager for Hong Kong universities.
Tracks deadline countdowns, weekly phased deliverables, application status,
and cross-university coverage.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from .config import (
    TARGET_HONG_KONG_UNIVERSITIES,
    CAMPAIGN_MILESTONES,
    CAMPAIGN_WEEKS_TOTAL,
    KEY_DEADLINES
)
from .models import ResearcherProfile, Scholarship

class CampaignManager:
    """Orchestrates the 10-week Hong Kong PhD application roadmap and deadline awareness."""

    def __init__(self, target_deadline: Optional[str] = None):
        # Default deadline: Dec 1, 2026 12:00 HKT (HKPFS deadline)
        self.deadline_str = target_deadline or "2026-12-01"
        self.deadline_date = datetime.strptime(self.deadline_str[:10], "%Y-%m-%d").date()

    def get_time_remaining(self, reference_date: Optional[date] = None) -> Dict[str, Any]:
        """Calculates days and weeks remaining until the key Hong Kong deadline."""
        ref = reference_date or date.today()
        delta = (self.deadline_date - ref).days
        days_remaining = max(0, delta)
        weeks_remaining = max(0, (days_remaining + 6) // 7)
        
        # Calculate current campaign week (1 to 10)
        # If 10 weeks remaining, we are in Week 1; if 1 week remaining, in Week 10
        current_week = max(1, min(10, CAMPAIGN_WEEKS_TOTAL - weeks_remaining + 1))

        return {
            "days_remaining": days_remaining,
            "weeks_remaining": weeks_remaining,
            "current_campaign_week": current_week,
            "target_deadline": self.deadline_str
        }

    def get_current_milestone(self, reference_date: Optional[date] = None) -> Dict[str, Any]:
        """Returns the milestone and action checklist for the current campaign week."""
        time_info = self.get_time_remaining(reference_date)
        week = time_info["current_campaign_week"]
        milestone = CAMPAIGN_MILESTONES.get(week, CAMPAIGN_MILESTONES[1])
        return {
            **time_info,
            "milestone_info": milestone
        }

    @staticmethod
    def get_university_coverage_summary(
        researchers: List[ResearcherProfile],
        scholarships: List[Scholarship]
    ) -> List[Dict[str, Any]]:
        """
        Computes coverage across all 8 target universities:
        - Researchers discovered
        - Strong matches (Tier 1 or Alignment >= 90%)
        - Active/Confirmed recruitment count
        - Scholarships available
        """
        summary = []
        for uni in TARGET_HONG_KONG_UNIVERSITIES:
            uni_researchers = [r for r in researchers if r.university == uni]
            strong_matches = [
                r for r in uni_researchers
                if r.priority_tier == "Tier 1" or r.alignment_score >= 90.0
            ]
            active_recruiting = [
                r for r in uni_researchers
                if r.recruitment.status in ["CONFIRMED_ACTIVE", "STRONG_EVIDENCE"]
            ]
            uni_scholarships = [
                s for s in scholarships
                if s.university == uni or "All 8" in s.university
            ]

            summary.append({
                "university": uni,
                "researchers_count": len(uni_researchers),
                "strong_matches_count": len(strong_matches),
                "active_recruiting_count": len(active_recruiting),
                "scholarships_count": len(uni_scholarships)
            })

        return summary
