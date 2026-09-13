"""
Data models for the Hong Kong PhD Supervisor Intelligence module.
Provides strongly-typed dataclasses for universities, researchers, publications,
recruitment evidence, scholarships, opportunities, and daily intelligence alerts.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class UniversityProfile:
    university_id: str
    canonical_name: str
    aliases: List[str]
    official_url: str
    graduate_school_url: str
    research_url: str
    phd_application_url: str
    scholarship_url: str
    relevant_departments: List[str]
    relevant_research_centres: List[str]
    last_verified: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniversityProfile":
        return cls(**data)

@dataclass
class Publication:
    publication_id: str
    title: str
    authors: List[str]
    year: int
    venue: str
    doi_or_url: str
    research_problem: str
    approach: str
    key_contribution: str
    edge_relevance: str
    is_seminal: bool = False
    is_recent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Publication":
        return cls(**data)

@dataclass
class RecruitmentEvidence:
    status: str  # CONFIRMED_ACTIVE, STRONG_EVIDENCE, POSSIBLE, UNKNOWN, NOT_CURRENTLY_RECRUITING, RECRUITMENT_STALE
    confidence: float  # 0.0 to 1.0
    evidence_text: str
    source_url: str
    source_type: str  # official_lab_website, faculty_homepage, call_for_phd, department_directory
    source_date: str  # YYYY-MM-DD
    last_verified: str  # YYYY-MM-DD

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecruitmentEvidence":
        return cls(**data)

@dataclass
class ResearcherProfile:
    researcher_id: str
    name: str
    university: str
    department: str
    position: str
    research_group: str
    official_profile_url: str
    personal_website: str
    google_scholar: str
    orcid: str
    dblp: str
    research_interests: List[str]
    research_summary: str
    edge_relevance: str
    research_trajectory: str
    current_projects: List[str]
    research_methods: List[str]
    datasets: List[str]
    simulation_tools: List[str]
    systems_testbeds: List[str]
    recruitment: RecruitmentEvidence
    potential_phd_topics: List[str]
    potential_alignment: str
    priority_tier: str  # Tier 1, Tier 2, Tier 3
    relevant_curriculum_weeks: List[int] = field(default_factory=list)
    relevant_curriculum_courses: List[str] = field(default_factory=list)
    publications: List[Publication] = field(default_factory=list)
    alignment_score: float = 0.0
    familiarity_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearcherProfile":
        data = dict(data)
        if isinstance(data.get("recruitment"), dict):
            data["recruitment"] = RecruitmentEvidence.from_dict(data["recruitment"])
        if "publications" in data:
            data["publications"] = [
                Publication.from_dict(p) if isinstance(p, dict) else p
                for p in data["publications"]
            ]
        return cls(**data)

@dataclass
class Scholarship:
    scholarship_id: str
    university: str
    scholarship_name: str
    phd_program: str
    eligibility: str
    application_deadline: str
    funding_amount: str
    tuition_coverage: str
    living_allowance: str
    duration: str
    dependent_support: str
    supervisor_requirement: str
    application_requirements: str
    official_url: str
    source: str
    last_verified: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scholarship":
        return cls(**data)

@dataclass
class Opportunity:
    opportunity_id: str
    university: str
    phd_program: str
    scholarship: Scholarship
    supervisor: ResearcherProfile
    research_alignment_score: float
    recruitment_score: float
    scholarship_quality_score: float
    application_feasibility_score: float
    deadline_urgency_score: float
    familiarity_gap_score: float
    composite_opportunity_score: float
    priority: str  # High, Medium, Low
    days_remaining: int
    status: str = "Identified"  # Identified, Shortlisted, Outreach Sent, Applying, Submitted

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class FamiliarityRecord:
    researcher_id: str
    papers_exposed: List[str] = field(default_factory=list)
    papers_read: List[str] = field(default_factory=list)
    topics_exposed: List[str] = field(default_factory=list)
    research_projects_exposed: List[str] = field(default_factory=list)
    research_trajectory_understood: bool = False
    recruitment_verified: bool = False
    familiarity_score: float = 0.0
    last_exposed: Optional[str] = None
    exposure_cycle_day: int = 1  # 1 through 7

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FamiliarityRecord":
        return cls(**data)

@dataclass
class DailyAlert:
    alert_id: str
    date: str
    weeks_remaining: int
    days_remaining: int
    university: str
    professor: str
    department: str
    research_group: str
    priority_tier: str
    research_alignment_pct: int
    recruitment_status: str
    recruitment_evidence: str
    cycle_day: int
    today_research_focus: str
    paper_title: str
    paper_author: str
    paper_year: int
    paper_link: str
    research_problem: str
    approach: str
    key_contribution: str
    why_it_matters_for_edge: str
    research_trajectory: str
    what_to_read_next: str
    potential_phd_alignment: str
    application_action_today: str
    scholarship_connection: str
    deadline_info: str
    next_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        """Formats the alert matching the prompt's required daily alert specification."""
        return f"""HONG KONG PHD SUPERVISOR INTELLIGENCE

Date: {self.date}
Weeks Remaining: {self.weeks_remaining}
Days Remaining: {self.days_remaining}

UNIVERSITY: {self.university}
Professor: {self.professor}
Department: {self.department}
Research Group: {self.research_group}

SUPERVISOR PRIORITY: {self.priority_tier}
RESEARCH ALIGNMENT: {self.research_alignment_pct}%
RECRUITMENT STATUS: {self.recruitment_status}
RECRUITMENT EVIDENCE: {self.recruitment_evidence}

TODAY'S RESEARCH FOCUS (Day {self.cycle_day} of 7-Day Familiarity Cycle):
Focus: {self.today_research_focus}

Paper: {self.paper_title}
Author: {self.paper_author}
Year: {self.paper_year}
Link: {self.paper_link}

RESEARCH PROBLEM:
{self.research_problem}

APPROACH:
{self.approach}

KEY CONTRIBUTION:
{self.key_contribution}

WHY THIS MATTERS FOR EDGE COMPUTING:
{self.why_it_matters_for_edge}

RESEARCH TRAJECTORY:
{self.research_trajectory}

WHAT TO READ NEXT:
{self.what_to_read_next}

POTENTIAL PHD ALIGNMENT:
{self.potential_phd_alignment}

APPLICATION ACTION TODAY:
{self.application_action_today}

SCHOLARSHIP CONNECTION:
{self.scholarship_connection}

DEADLINE:
{self.deadline_info}

NEXT ACTION:
{self.next_action}
"""
