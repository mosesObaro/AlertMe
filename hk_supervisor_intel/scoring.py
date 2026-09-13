"""
Multi-factor scoring engine for the Hong Kong PhD Supervisor Intelligence module.
Computes Researcher Eligibility Scores, Composite Opportunity Rankings, and
Applicant Familiarity Scores.
"""

from typing import Dict, Any, Optional
from datetime import date
from .config import (
    RESEARCHER_SCORING_WEIGHTS,
    OPPORTUNITY_SCORING_WEIGHTS,
    FAMILIARITY_WEIGHTS
)
from .models import ResearcherProfile, Scholarship, FamiliarityRecord
from .recruitment import RecruitmentEngine

class ScoringEngine:
    """Calculates all normalized scores across supervisors, opportunities, and familiarity."""

    @classmethod
    def calculate_researcher_score(
        cls,
        researcher: ResearcherProfile,
        relevance_score: float,
        reference_date: Optional[date] = None
    ) -> float:
        """
        Calculates the researcher's overall eligibility score (0-100%).
        Weights:
        - Research Alignment: 35%
        - Current Research Activity: 20%
        - PhD Recruitment: 30%
        - Academic / Research Strength: 10%
        - Research Accessibility: 5%
        """
        # Alignment
        alignment = relevance_score

        # Activity: assessed by recent publications and active projects
        recent_count = sum(1 for p in researcher.publications if getattr(p, "is_recent", False))
        project_count = len(researcher.current_projects)
        activity_score = min(100.0, (recent_count * 30.0) + (project_count * 20.0) + 30.0)

        # Recruitment
        recruitment_score = RecruitmentEngine.get_recruitment_score(researcher.recruitment, reference_date)

        # Academic Strength: IEEE/ACM Fellows, Chair Professors, high standing
        title_lower = researcher.position.lower()
        strength = 75.0
        if "chair professor" in title_lower or "dean" in title_lower or "fellow" in title_lower:
            strength = 95.0
        elif "professor" in title_lower:
            strength = 85.0

        # Accessibility: availability of personal website, dblp, scholar
        accessibility = 60.0
        if researcher.personal_website:
            accessibility += 20.0
        if researcher.google_scholar or researcher.dblp:
            accessibility += 20.0

        w = RESEARCHER_SCORING_WEIGHTS
        total = (
            alignment * w["research_alignment"] +
            activity_score * w["current_activity"] +
            recruitment_score * w["phd_recruitment"] +
            strength * w["academic_strength"] +
            accessibility * w["research_accessibility"]
        )

        return round(total, 1)

    @classmethod
    def calculate_opportunity_score(
        cls,
        researcher: ResearcherProfile,
        scholarship: Scholarship,
        days_remaining: int,
        familiarity: FamiliarityRecord
    ) -> float:
        """
        Calculates composite opportunity score (0-100%) for:
        University + PhD Programme + Scholarship + Potential Supervisor.
        Weights:
        - 30% Research Alignment
        - 20% Supervisor Recruitment Evidence
        - 20% Scholarship Quality
        - 15% Application Feasibility
        - 10% Deadline Urgency
        - 5% Research Familiarity Gap
        """
        alignment = researcher.alignment_score

        recruitment = RecruitmentEngine.get_recruitment_score(researcher.recruitment)

        # Scholarship quality: HKPFS/Presidential = 95-100; Standard PGS = 75-80
        sch_name_lower = scholarship.scholarship_name.lower()
        if "fellowship scheme" in sch_name_lower or "presidential" in sch_name_lower or "vice-chancellor" in sch_name_lower:
            scholarship_quality = 98.0
        elif "redbird" in sch_name_lower or "cbps" in sch_name_lower or "pppfs" in sch_name_lower:
            scholarship_quality = 95.0
        else:
            scholarship_quality = 80.0

        # Feasibility: high for candidates with clear supervisor and open calls
        feasibility = 80.0
        if researcher.recruitment.status == "CONFIRMED_ACTIVE":
            feasibility = 92.0
        elif researcher.recruitment.status == "NOT_CURRENTLY_RECRUITING":
            feasibility = 20.0

        # Deadline urgency: higher urgency when days remaining is tighter but actionable (e.g. 14-45 days)
        if days_remaining <= 0:
            urgency = 0.0
        elif days_remaining <= 30:
            urgency = 95.0
        elif days_remaining <= 60:
            urgency = 80.0
        elif days_remaining <= 75:
            urgency = 65.0
        else:
            urgency = 50.0

        # Familiarity gap: higher priority given to candidates needing study to close familiarity gap
        fam_gap = max(0.0, 100.0 - familiarity.familiarity_score)

        w = OPPORTUNITY_SCORING_WEIGHTS
        total = (
            alignment * w["research_alignment"] +
            recruitment * w["supervisor_recruitment"] +
            scholarship_quality * w["scholarship_quality"] +
            feasibility * w["application_feasibility"] +
            urgency * w["deadline_urgency"] +
            (fam_gap * 0.5 + 50.0) * w["research_familiarity_gap"]
        )

        return round(total, 1)

    @classmethod
    def calculate_familiarity_score(cls, record: FamiliarityRecord, researcher: ResearcherProfile) -> float:
        """
        Calculates the applicant's familiarity score (0-100%) with a supervisor.
        Weights:
        - 20% Profile Understanding
        - 20% Publication Exposure
        - 20% Research Trajectory
        - 15% Recent Research
        - 10% Methodology
        - 10% Current Projects
        - 5% Recruitment Awareness
        """
        # Profile understanding: based on basic exposure
        profile_score = 100.0 if record.last_exposed is not None else 30.0

        # Publication exposure: fraction of researcher's publications exposed
        total_pubs = max(1, len(researcher.publications))
        pub_score = min(100.0, (len(record.papers_exposed) / total_pubs) * 100.0)

        # Trajectory
        traj_score = 100.0 if record.research_trajectory_understood or record.exposure_cycle_day >= 3 else 20.0

        # Recent research
        recent_score = 100.0 if record.exposure_cycle_day >= 4 else 20.0

        # Methodology
        method_score = 100.0 if record.exposure_cycle_day >= 6 else 15.0

        # Current projects
        proj_score = min(100.0, len(record.research_projects_exposed) * 35.0 + (30.0 if record.exposure_cycle_day >= 5 else 0.0))

        # Recruitment awareness
        recruit_score = 100.0 if record.recruitment_verified or record.exposure_cycle_day >= 1 else 30.0

        w = FAMILIARITY_WEIGHTS
        total = (
            profile_score * w["profile_understanding"] +
            pub_score * w["publication_exposure"] +
            traj_score * w["research_trajectory"] +
            recent_score * w["recent_research"] +
            method_score * w["methodology"] +
            proj_score * w["current_projects"] +
            recruit_score * w["recruitment_awareness"]
        )

        return round(total, 1)
