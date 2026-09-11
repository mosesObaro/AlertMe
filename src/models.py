"""Domain models for Edge PhD Research Intelligence System."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
import datetime
import hashlib
import re


class ItemType(str, Enum):
    PAPER = "paper"
    PREPRINT = "preprint"
    SURVEY = "survey"
    CONFERENCE_CFP = "conference_cfp"
    WORKSHOP = "workshop"
    PHD_OPPORTUNITY = "phd_opportunity"
    FELLOWSHIP = "fellowship"
    STANDARDS_UPDATE = "standards_update"
    BENCHMARK_CODE = "benchmark_code"
    TECH_REPORT = "tech_report"
    EVENT = "event"


class CredibilityTier(str, Enum):
    TIER1_ACADEMIC_STANDARDS = "tier1_academic_standards"
    TIER2_UNIVERSITY_LAB = "tier2_university_lab"
    TIER3_CONFERENCE = "tier3_conference"
    TIER4_INDUSTRY = "tier4_industry"
    UNKNOWN = "unknown"


class RecruitmentStatus(str, Enum):
    ACTIVELY_RECRUITING = "actively_recruiting"
    LIKELY_RECRUITING = "likely_recruiting"
    NOT_VERIFIED = "not_verified"
    NOT_CURRENTLY_RECRUITING = "not_currently_recruiting"


class FundingStatus(str, Enum):
    FULLY_FUNDED = "fully_funded"
    PARTIALLY_FUNDED = "partially_funded"
    SELF_FUNDED = "self_funded"
    UNKNOWN = "unknown"


class DependantSupportClassification(str, Enum):
    FINANCIALLY_SUPPORTED = "financially_supported" # Dedicated financial/child/spouse allowance or family housing
    EXCELLENT = "financially_supported" # Dedicated financial/child/spouse allowance
    GOOD = "good"           # Dependants permitted + stipend designed to support family
    PERMITTED = "permitted" # Legal accompaniment on student visa, but standard single stipend
    UNKNOWN = "unknown"     # No verified information
    RESTRICTED = "restricted" # Visa or funding prohibits/restricts accompanying dependants


class InternationalEligibility(str, Enum):
    ELIGIBLE = "eligible"
    RESTRICTED = "restricted"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"



@dataclass
class ScoreBreakdown:
    topic_score: float = 0.0
    credibility_score: float = 0.0
    recency_score: float = 0.0
    stage_boost: float = 0.0
    phd_boost: float = 0.0
    negative_penalty: float = 0.0
    final_score: float = 0.0
    matched_topics: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PaperIntelligence:
    why_it_matters: str = ""
    research_problem: str = ""
    methodology: str = ""
    key_contribution: str = ""
    potential_gap: str = ""
    relevance_to_phd: str = ""
    is_ai_generated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchItem:
    title: str
    url: str
    source: str
    source_tier: str = CredibilityTier.TIER1_ACADEMIC_STANDARDS.value
    item_type: str = ItemType.PAPER.value
    authors: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    publication_date: str = ""
    discovery_date: str = field(default_factory=lambda: datetime.date.today().isoformat())
    abstract: str = ""
    venue: str = ""
    topics: List[str] = field(default_factory=list)
    institution: str = ""
    location: str = ""
    deadline: Optional[str] = None
    is_urgent: bool = False
    id: str = ""
    score: Optional[ScoreBreakdown] = None
    intelligence: Optional[PaperIntelligence] = None
    opportunity_data: Optional[Dict[str, Any]] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = self.generate_id()
        if not self.publication_date:
            self.publication_date = datetime.date.today().isoformat()

    def generate_id(self) -> str:
        """Generates a deterministic unique hash for deduplication."""
        if self.doi:
            clean_doi = self.doi.strip().lower()
            return f"doi_{hashlib.sha256(clean_doi.encode('utf-8')).hexdigest()[:16]}"
        if self.arxiv_id:
            clean_arxiv = re.sub(r'v\d+$', '', self.arxiv_id.strip().lower())
            return f"arxiv_{hashlib.sha256(clean_arxiv.encode('utf-8')).hexdigest()[:16]}"
        
        # Canonical string from normalized title and url
        norm_title = re.sub(r'[^a-zA-Z0-9]', '', self.title.lower())
        norm_url = re.sub(r'^https?://(www\.)?', '', self.url.lower().rstrip('/'))
        seed = f"{norm_title}|{norm_url}"
        return f"item_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.score:
            data["score"] = self.score.to_dict()
        if self.intelligence:
            data["intelligence"] = self.intelligence.to_dict()
        if self.opportunity_data:
            data["opportunity_data"] = self.opportunity_data
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchItem":
        score_data = data.pop("score", None)
        intel_data = data.pop("intelligence", None)
        score = ScoreBreakdown(**score_data) if score_data else None
        intel = PaperIntelligence(**intel_data) if intel_data else None
        item = cls(**data)
        item.score = score
        item.intelligence = intel
        return item


@dataclass
class PhDOpportunity:
    """Rich domain model for PhD positions, studentships, and lab openings."""
    title: str
    university: str
    department: str = ""
    professor_name: str = ""
    researcher_profile_url: str = ""
    university_url: str = ""
    country: str = "" # Germany, Hong Kong, Canada, United Kingdom, Japan, United States, etc.
    city: str = ""
    research_areas: List[str] = field(default_factory=list)
    opportunity_type: str = "phd_position" # phd_position, phd_studentship, funded_phd, supervisor_seeking_students, scholarship, fellowship, research_assistantship
    funding_status: str = FundingStatus.UNKNOWN.value
    funding_amount: str = ""
    tuition_coverage: str = ""
    duration: str = ""
    deadline: Optional[str] = None
    start_date: Optional[str] = None
    eligibility: str = ""
    international_eligibility: str = InternationalEligibility.ELIGIBLE.value
    dependant_support_info: str = ""
    dependant_support_classification: str = DependantSupportClassification.UNKNOWN.value
    source_url: str = ""
    source: str = ""
    discovery_date: str = field(default_factory=lambda: datetime.date.today().isoformat())
    last_verified_date: str = field(default_factory=lambda: datetime.date.today().isoformat())
    relevance_score: float = 0.0
    funding_score: float = 0.0
    supervisor_fit_score: float = 0.0
    country_score: float = 0.0
    dependant_support_score: float = 0.0
    composite_score: float = 0.0
    recruitment_status: str = RecruitmentStatus.NOT_VERIFIED.value
    recruitment_evidence: str = ""
    confidence: str = "high"
    reasons: List[str] = field(default_factory=list)
    id: str = ""
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = self.generate_id()

    def generate_id(self) -> str:
        norm_title = re.sub(r'[^a-zA-Z0-9]', '', self.title.lower())
        norm_uni = re.sub(r'[^a-zA-Z0-9]', '', self.university.lower())
        norm_prof = re.sub(r'[^a-zA-Z0-9]', '', self.professor_name.lower())
        norm_url = re.sub(r'^https?://(www\.)?', '', self.source_url.lower().rstrip('/'))
        seed = f"{norm_uni}|{norm_prof}|{norm_title}|{norm_url}"
        return f"opp_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhDOpportunity":
        return cls(**data)

    def to_research_item(self) -> ResearchItem:
        """Bridges opportunity into general pipeline ResearchItem."""
        score_breakdown = ScoreBreakdown(
            topic_score=self.relevance_score,
            credibility_score=self.funding_score * 0.25,
            recency_score=1.5,
            phd_boost=1.0,
            final_score=self.composite_score,
            matched_topics=self.research_areas,
            reasons=self.reasons
        )
        return ResearchItem(
            title=self.title,
            url=self.source_url or self.researcher_profile_url or self.university_url,
            source=self.source or self.university,
            source_tier=CredibilityTier.TIER2_UNIVERSITY_LAB.value,
            item_type=ItemType.PHD_OPPORTUNITY.value,
            authors=[self.professor_name] if self.professor_name else [],
            publication_date=self.discovery_date,
            discovery_date=self.discovery_date,
            abstract=f"{self.funding_status.replace('_', ' ').title()} PhD at {self.university} ({self.country}). {self.eligibility} Dependant status: {self.dependant_support_classification}. {self.dependant_support_info}",
            venue=f"{self.university} — {self.country}",
            topics=self.research_areas,
            institution=self.university,
            location=f"{self.city}, {self.country}" if self.city else self.country,
            deadline=self.deadline,
            score=score_breakdown,
            opportunity_data=self.to_dict(),
            id=self.id
        )


@dataclass
class ResearcherProfile:
    """Rich model for professors & researchers investigated for PhD supervision."""
    name: str
    institution: str
    country: str = ""
    department: str = ""
    profile_url: str = ""
    lab_website: str = ""
    research_areas: List[str] = field(default_factory=list)
    academic_fit_score: float = 0.0
    recruitment_status: str = RecruitmentStatus.NOT_VERIFIED.value
    recruitment_evidence: str = ""
    recruitment_quote: str = ""
    recent_papers: List[Dict[str, Any]] = field(default_factory=list)
    publication_count: int = 0
    citations_indicator: str = ""
    h_index: Optional[int] = None
    orcid: Optional[str] = None
    openalex_id: Optional[str] = None
    semantic_scholar_url: Optional[str] = None
    google_scholar_url: Optional[str] = None
    last_checked: str = field(default_factory=lambda: datetime.date.today().isoformat())
    current_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    composite_score: float = 0.0
    average_relevance: float = 0.0

    def __post_init__(self):
        if not self.recruitment_quote and self.recruitment_evidence:
            self.recruitment_quote = self.recruitment_evidence
        elif not self.recruitment_evidence and self.recruitment_quote:
            self.recruitment_evidence = self.recruitment_quote
        if not self.average_relevance and self.composite_score:
            self.average_relevance = self.composite_score
        elif not self.composite_score and self.average_relevance:
            self.composite_score = self.average_relevance

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["topics"] = self.research_areas
        d["average_relevance"] = self.average_relevance or self.composite_score
        d["recruitment_quote"] = self.recruitment_quote or self.recruitment_evidence
        return d

    def to_supervisor_dict(self) -> Dict[str, Any]:
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearcherProfile":
        data_copy = dict(data)
        data_copy.pop("topics", None)
        return cls(**data_copy)


@dataclass
class Scholarship:
    """Rich domain model for international & family-friendly PhD scholarships."""
    name: str
    provider: str = ""
    country: str = ""
    university: str = ""
    degree_level: str = "PhD"
    tuition_coverage: str = ""
    stipend_amount: str = ""
    funding_type: str = "fully_funded"
    duration: str = ""
    deadline: Optional[str] = None
    start_date: Optional[str] = None
    dependant_support_classification: str = DependantSupportClassification.PERMITTED.value
    dependant_support_details: str = ""
    family_accommodation: str = ""
    international_eligibility: str = InternationalEligibility.ELIGIBLE.value
    official_url: str = ""
    verification_date: str = field(default_factory=lambda: datetime.date.today().isoformat())
    score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scholarship":
        return cls(**data)

