"""
Data models for the Global Country-Based PhD Funding and Supervisor Intelligence Engine.
Provides strongly typed dataclasses for countries, universities, publications, recruitment,
funding opportunities, researcher profiles, and country campaigns.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class CountryCampaign:
    country: str
    country_code: str
    currency: str
    immigration_dependant_guidance: str
    dependant_visa_policy: str
    immigration_disclaimer: str
    target_deadline: str
    primary_funding_vehicle: str
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CountryCampaign":
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

@dataclass
class UniversityProfile:
    university_id: str
    canonical_name: str
    country: str
    country_code: str
    aliases: List[str]
    official_url: str
    graduate_school_url: str
    research_url: str
    phd_application_url: str
    funding_url: str
    relevant_departments: List[str]
    relevant_research_centres: List[str]
    suitability_score: float = 0.0
    funding_availability_rating: str = "High"  # High, Medium, Moderate
    last_verified: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniversityProfile":
        data = dict(data)
        if "funding_url" not in data and "scholarship_url" in data:
            data["funding_url"] = data.pop("scholarship_url")
        elif "scholarship_url" in data:
            data.pop("scholarship_url", None)
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

@dataclass
class Publication:
    publication_id: str
    title: str
    authors: List[str]
    year: int
    venue: str
    doi_or_url: str
    research_problem: str = ""
    approach: str = ""
    key_contribution: str = ""
    edge_relevance: str = ""
    is_seminal: bool = False
    is_recent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Publication":
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

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
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

@dataclass
class FundingOpportunity:
    opportunity_id: str
    country: str
    university: str
    title: str
    provider: str
    funding_type: str  # FULLY_FUNDED, PARTIALLY_FUNDED, TUITION_ONLY, STIPEND_ONLY, UNKNOWN
    tuition_coverage: str
    stipend_amount: str
    duration: str
    dependant_support: str  # EXCELLENT, GOOD, PERMITTED, NONE, UNKNOWN
    international_eligibility: str  # ELIGIBLE, RESTRICTED, INELIGIBLE, UNKNOWN
    application_deadline: str
    official_url: str
    associated_lab_or_professor: str = ""
    eligibility_notes: str = ""
    last_verified: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FundingOpportunity":
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

@dataclass
class ResearcherProfile:
    researcher_id: str
    name: str
    university: str
    country: str
    department: str
    position: str
    research_group: str
    official_profile_url: str
    personal_website: str = ""
    institutional_email: str = ""
    google_scholar: str = ""
    orcid: str = ""
    dblp: str = ""
    research_interests: List[str] = field(default_factory=list)
    research_summary: str = ""
    edge_relevance: str = ""
    research_trajectory: str = ""
    current_projects: List[str] = field(default_factory=list)
    funding_projects: List[str] = field(default_factory=list)
    research_methods: List[str] = field(default_factory=list)
    systems_testbeds: List[str] = field(default_factory=list)
    recruitment: RecruitmentEvidence = field(
        default_factory=lambda: RecruitmentEvidence(
            status="UNKNOWN",
            confidence=0.5,
            evidence_text="Faculty member active in doctoral research; prospective applicants should check departmental admissions.",
            source_url="",
            source_type="faculty_profile",
            source_date="2026-01-01",
            last_verified="2026-09-15"
        )
    )
    potential_phd_topics: List[str] = field(default_factory=list)
    potential_alignment: str = ""
    priority_tier: str = "Tier 1"  # Tier 1, Tier 2, Tier 3
    publications: List[Publication] = field(default_factory=list)
    alignment_score: float = 0.0
    suitability_score: float = 0.0
    why_suitable: List[str] = field(default_factory=list)
    research_gaps: List[str] = field(default_factory=list)
    last_verified: str = "2026-09-15"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

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
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

@dataclass
class CountryCampaignResult:
    country: str
    country_code: str
    execution_date: str
    universities_count: int
    professors_count: int
    funding_opportunities_count: int
    universities: List[UniversityProfile]
    professors: List[ResearcherProfile]
    funding_opportunities: List[FundingOpportunity]
    generated_dossiers: Dict[str, Dict[str, str]] = field(default_factory=dict)
    country_report_files: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "country": self.country,
            "country_code": self.country_code,
            "execution_date": self.execution_date,
            "universities_count": self.universities_count,
            "professors_count": self.professors_count,
            "funding_opportunities_count": self.funding_opportunities_count,
            "universities": [u.to_dict() for u in self.universities],
            "professors": [p.to_dict() for p in self.professors],
            "funding_opportunities": [f.to_dict() for f in self.funding_opportunities],
            "generated_dossiers": self.generated_dossiers,
            "country_report_files": self.country_report_files
        }
