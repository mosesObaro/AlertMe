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


# ==============================================================================
# CANONICAL PROFESSOR DOSSIER DOMAIN MODELS
# ==============================================================================

@dataclass
class DossierMetadata:
    professor_name: str
    university: str
    department: str
    country: str
    country_code: str
    generated_date: str
    last_verified: str
    areas_analyzed_count: int
    publications_analyzed_count: int
    eras_identified_count: int
    gaps_identified_count: int
    potential_directions_count: int
    funding_opportunities_count: int
    sources_consulted: List[str] = field(default_factory=list)
    data_limitations: List[str] = field(default_factory=list)
    confidence_level: str = "High"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DossierMetadata":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class DossierIdentity:
    full_name: str
    academic_title: str
    position: str
    university: str
    department: str
    faculty: str
    country: str
    research_group: str
    official_profile_url: str
    personal_website: str = ""
    institutional_email: str = ""
    google_scholar: str = ""
    orcid: str = ""
    dblp: str = ""
    academic_standing: str = ""
    identity_confidence: str = "VERIFIED"  # VERIFIED, STRONG_CONFIDENCE, AMBIGUOUS
    identity_evidence: List[str] = field(default_factory=list)
    research_interests: List[str] = field(default_factory=list)
    alignment_score: float = 90.0
    priority_tier: str = "Tier 1"

    @property
    def name(self) -> str:
        return self.full_name

    @property
    def verification_status(self) -> str:
        return self.identity_confidence

    @property
    def confidence_level(self) -> str:
        return self.identity_confidence

    @property
    def audit_trail(self) -> List[str]:
        return self.identity_evidence

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DossierIdentity":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ResearchEra:
    era_number: int
    name: str
    period: str
    primary_field: str
    specializations: List[str] = field(default_factory=list)
    core_questions: str = ""
    methods: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    application_domains: List[str] = field(default_factory=list)
    representative_publications: List[str] = field(default_factory=list)
    major_contributions: str = ""
    collaborators: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    later_research_influence: str = ""
    evidence_confidence: str = "Strong"

    @property
    def influence_on_later_work(self) -> str:
        return self.later_research_influence or self.major_contributions

    @property
    def start_year(self) -> int:
        parts = re.findall(r'\d{4}', self.period)
        return int(parts[0]) if parts else 2000

    @property
    def end_year(self) -> int:
        parts = re.findall(r'\d{4}', self.period)
        return int(parts[1]) if len(parts) > 1 else 2026

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchEra":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ResearchFieldTaxonomy:
    field_name: str
    classification: str  # Primary, Secondary, Emerging, Historical, Occasional
    subfields: List[str] = field(default_factory=list)
    core_problem: str = ""
    methodology: str = ""
    application_domain: str = ""
    activity_period: str = ""
    representative_publications: List[str] = field(default_factory=list)
    evidence_level: str = "Documented"

    @property
    def category(self) -> str:
        return self.classification

    @property
    def sub_specializations(self) -> List[str]:
        return self.subfields

    @property
    def description(self) -> str:
        return self.core_problem

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchFieldTaxonomy":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ResearchTransition:
    from_area: str
    to_area: str
    transition_period: str
    connecting_problem: str
    continuity_aspects: str
    current_relevance: str
    explanation_type: str = "Evidence-based interpretation"  # Documented explanation, Evidence-based interpretation, Unknown
    supporting_publications: List[str] = field(default_factory=list)
    evidence: str = ""

    @property
    def from_field(self) -> str:
        return self.from_area

    @property
    def to_field(self) -> str:
        return self.to_area

    @property
    def from_period(self) -> str:
        return self.transition_period.split(" -> ")[0] if " -> " in self.transition_period else self.transition_period

    @property
    def to_period(self) -> str:
        return self.transition_period.split(" -> ")[1] if " -> " in self.transition_period else ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchTransition":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class RecurringTheme:
    theme_name: str
    first_appearance: str
    periods_active: str
    evolution_description: str
    current_relevance: str
    representative_publications: List[str] = field(default_factory=list)
    evidence: str = ""

    @property
    def description(self) -> str:
        return self.evolution_description or self.current_relevance

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecurringTheme":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class MajorPublicationDetail:
    title: str
    year: int
    venue: str
    doi_or_url: str
    research_area: str
    problem_addressed: str
    approach_methodology: str
    key_contribution: str
    why_it_matters: str
    relevance_to_applicant: str
    influence_on_later_work: str = ""
    is_seminal: bool = False
    is_recent: bool = False

    @property
    def approach(self) -> str:
        return self.approach_methodology

    @property
    def relevance_to_phd(self) -> str:
        return self.relevance_to_applicant

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MajorPublicationDetail":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class CurrentSpecialization:
    area_name: str
    classification: str  # Primary Specialization, Secondary Specialization, Emerging Direction
    evidence: str
    recent_publications: List[str] = field(default_factory=list)
    current_projects: List[str] = field(default_factory=list)
    current_activity: str = ""
    confidence: str = "High"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurrentSpecialization":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class CollaborationNetwork:
    institutional_collaborators: List[str] = field(default_factory=list)
    industry_government_partners: List[str] = field(default_factory=list)
    research_communities: List[str] = field(default_factory=list)
    research_style: str = "Lab-based & System-grounded"  # Lab-based, Internationally collaborative, Industry-oriented, Interdisciplinary

    @property
    def academic_collaborators(self) -> str:
        return ", ".join(self.institutional_collaborators) if isinstance(self.institutional_collaborators, list) else str(self.institutional_collaborators)

    @property
    def industry_links(self) -> str:
        return ", ".join(self.industry_government_partners) if isinstance(self.industry_government_partners, list) else str(self.industry_government_partners)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollaborationNetwork":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class SupervisionEvidence:
    supervision_record: str
    supervision_model: str
    student_alumni_placements: List[str] = field(default_factory=list)
    research_group_culture: str = ""
    evidence_status: str = "Public institutional evidence verified"

    @property
    def group_culture(self) -> str:
        return self.research_group_culture or self.supervision_record

    @property
    def alumni_placements(self) -> List[str]:
        return self.student_alumni_placements

    @property
    def supervision_style(self) -> str:
        return self.supervision_model

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SupervisionEvidence":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ApplicantAlignmentDimension:
    applicant_dimension: str
    professor_work: str
    alignment_level: str  # Strong alignment, Moderate alignment, Weak alignment, No obvious alignment, Unknown
    evidence_synergy: str
    potential_connection: str = ""

    @property
    def dimension(self) -> str:
        return self.applicant_dimension

    @property
    def professor_capability(self) -> str:
        return self.professor_work

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApplicantAlignmentDimension":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class PotentialPhDDirection:
    direction_number: int
    title: str
    problem_statement: str
    professor_expertise: str
    candidate_value_add: str
    supporting_publications: List[str] = field(default_factory=list)
    research_gap: str = ""
    potential_contribution: str = ""
    relevant_methodologies: List[str] = field(default_factory=list)
    relevant_technologies: List[str] = field(default_factory=list)
    alignment_score: float = 9.0
    evidence_classification: str = "Potential Research Direction"

    @property
    def professor_expertise_hook(self) -> str:
        return self.professor_expertise

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PotentialPhDDirection":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ResearchGaps:
    explicit_gaps: List[str] = field(default_factory=list)
    evidence_based_gaps: List[str] = field(default_factory=list)
    speculative_opportunities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchGaps":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class PublicationTrends:
    momentum: str
    citation_summary: str
    keyword_evolution: List[str] = field(default_factory=list)
    annual_breakdown: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PublicationTrends":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class CareerComparisonRow:
    dimension: str
    early_career: str
    mid_career: str
    current_specialization: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CareerComparisonRow":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class DossierFundingItem:
    title: str
    provider: str
    funding_type: str
    stipend_amount: str
    tuition_coverage: str
    duration: str
    international_eligibility: str
    dependant_support: str
    application_deadline: str
    status: str = "Active / Available"
    official_url: str = ""
    phd_relevance: str = ""
    last_verified: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DossierFundingItem":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class DossierRecruitmentItem:
    status: str  # Confirmed current recruitment, Recent recruitment evidence, Project-based potential, No current evidence found, Unknown
    confidence: float
    evidence_text: str
    source_url: str
    source_type: str
    source_date: str
    last_verified: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DossierRecruitmentItem":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ResearchEnvironmentDetail:
    university: str
    department: str
    faculty: str
    laboratory: str
    research_centres: List[str] = field(default_factory=list)
    infrastructure_testbeds: List[str] = field(default_factory=list)
    graduate_school_url: str = ""
    doctoral_programme: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchEnvironmentDetail":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ReadingRecommendationItem:
    tier: int  # 1: Current, 2: Evolution, 3: PhD Alignment
    tier_label: str
    paper_title: str
    year: int
    venue: str
    why_read: str
    key_concept: str
    connection_to_research: str
    relevance_to_applicant: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReadingRecommendationItem":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ProposalPositioningDetail:
    what_to_emphasize: List[str] = field(default_factory=list)
    what_to_avoid: List[str] = field(default_factory=list)
    narrative_flow: List[str] = field(default_factory=list)
    papers_to_cite: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProposalPositioningDetail":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class QuestionsForProfessorDetail:
    research_questions: List[str] = field(default_factory=list)
    supervision_questions: List[str] = field(default_factory=list)
    funding_questions: List[str] = field(default_factory=list)
    environment_questions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestionsForProfessorDetail":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class SuitabilityScoreBreakdown:
    scores: Dict[str, float] = field(default_factory=dict)
    explanations: Dict[str, str] = field(default_factory=dict)
    composite_score: float = 0.0
    priority_tier: str = "Tier 1"
    classification: str = "Category A — Strong Potential Supervisor"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuitabilityScoreBreakdown":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class DossierSourcesDetail:
    facts: List[str] = field(default_factory=list)
    evidence_based_inferences: List[str] = field(default_factory=list)
    speculative_directions: List[str] = field(default_factory=list)
    primary_sources: List[str] = field(default_factory=list)
    speculative_opportunities: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.speculative_opportunities and not self.speculative_directions:
            self.speculative_directions = list(self.speculative_opportunities)
        elif self.speculative_directions and not self.speculative_opportunities:
            self.speculative_opportunities = list(self.speculative_directions)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DossierSourcesDetail":
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


@dataclass
class ProfessorDossier:
    metadata: DossierMetadata
    identity: DossierIdentity
    executive_summary: str
    timeline_summary: str
    eras: List[ResearchEra]
    fields_taxonomy: List[ResearchFieldTaxonomy]
    transitions: List[ResearchTransition]
    recurring_themes: List[RecurringTheme]
    major_publications: List[MajorPublicationDetail]
    current_specializations: List[CurrentSpecialization]
    evolution_map_text: str
    collaboration_network: CollaborationNetwork
    funding_and_grants: List[DossierFundingItem]
    supervision: SupervisionEvidence
    applicant_alignment: List[ApplicantAlignmentDimension]
    potential_directions: List[PotentialPhDDirection]
    research_gaps: ResearchGaps
    future_direction: str
    research_fit_table: List[Dict[str, str]]
    suitability_score: SuitabilityScoreBreakdown
    strengths_and_considerations: Dict[str, List[str]]
    questions_for_professor: QuestionsForProfessorDetail
    reading_recommendations: List[ReadingRecommendationItem]
    proposal_positioning: ProposalPositioningDetail
    publication_trends: PublicationTrends
    career_comparison: List[CareerComparisonRow]
    research_environment: ResearchEnvironmentDetail
    final_profile: str
    one_sentence_identity: str
    recommendation: str
    sources: DossierSourcesDetail
    recruitment: DossierRecruitmentItem

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "identity": self.identity.to_dict(),
            "executive_summary": self.executive_summary,
            "timeline_summary": self.timeline_summary,
            "eras": [e.to_dict() for e in self.eras],
            "fields_taxonomy": [f.to_dict() for f in self.fields_taxonomy],
            "transitions": [t.to_dict() for t in self.transitions],
            "recurring_themes": [th.to_dict() for th in self.recurring_themes],
            "major_publications": [p.to_dict() for p in self.major_publications],
            "current_specializations": [c.to_dict() for c in self.current_specializations],
            "evolution_map_text": self.evolution_map_text,
            "collaboration_network": self.collaboration_network.to_dict(),
            "funding_and_grants": [fg.to_dict() for fg in self.funding_and_grants],
            "supervision": self.supervision.to_dict(),
            "applicant_alignment": [aa.to_dict() for aa in self.applicant_alignment],
            "potential_directions": [pd.to_dict() for pd in self.potential_directions],
            "research_gaps": self.research_gaps.to_dict(),
            "future_direction": self.future_direction,
            "research_fit_table": self.research_fit_table,
            "suitability_score": self.suitability_score.to_dict(),
            "strengths_and_considerations": self.strengths_and_considerations,
            "questions_for_professor": self.questions_for_professor.to_dict(),
            "reading_recommendations": [rr.to_dict() for rr in self.reading_recommendations],
            "proposal_positioning": self.proposal_positioning.to_dict(),
            "publication_trends": self.publication_trends.to_dict(),
            "career_comparison": [cc.to_dict() for cc in self.career_comparison],
            "research_environment": self.research_environment.to_dict(),
            "final_profile": self.final_profile,
            "one_sentence_identity": self.one_sentence_identity,
            "recommendation": self.recommendation,
            "sources": self.sources.to_dict(),
            "recruitment": self.recruitment.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfessorDossier":
        data = dict(data)
        return cls(
            metadata=DossierMetadata.from_dict(data["metadata"]),
            identity=DossierIdentity.from_dict(data["identity"]),
            executive_summary=data.get("executive_summary", ""),
            timeline_summary=data.get("timeline_summary", ""),
            eras=[ResearchEra.from_dict(e) for e in data.get("eras", [])],
            fields_taxonomy=[ResearchFieldTaxonomy.from_dict(f) for f in data.get("fields_taxonomy", [])],
            transitions=[ResearchTransition.from_dict(t) for t in data.get("transitions", [])],
            recurring_themes=[RecurringTheme.from_dict(th) for th in data.get("recurring_themes", [])],
            major_publications=[MajorPublicationDetail.from_dict(p) for p in data.get("major_publications", [])],
            current_specializations=[CurrentSpecialization.from_dict(c) for c in data.get("current_specializations", [])],
            evolution_map_text=data.get("evolution_map_text", ""),
            collaboration_network=CollaborationNetwork.from_dict(data.get("collaboration_network", {})),
            funding_and_grants=[DossierFundingItem.from_dict(fg) for fg in data.get("funding_and_grants", [])],
            supervision=SupervisionEvidence.from_dict(data.get("supervision", {})),
            applicant_alignment=[ApplicantAlignmentDimension.from_dict(aa) for aa in data.get("applicant_alignment", [])],
            potential_directions=[PotentialPhDDirection.from_dict(pd) for pd in data.get("potential_directions", [])],
            research_gaps=ResearchGaps.from_dict(data.get("research_gaps", {})),
            future_direction=data.get("future_direction", ""),
            research_fit_table=data.get("research_fit_table", []),
            suitability_score=SuitabilityScoreBreakdown.from_dict(data.get("suitability_score", {})),
            strengths_and_considerations=data.get("strengths_and_considerations", {}),
            questions_for_professor=QuestionsForProfessorDetail.from_dict(data.get("questions_for_professor", {})),
            reading_recommendations=[ReadingRecommendationItem.from_dict(rr) for rr in data.get("reading_recommendations", [])],
            proposal_positioning=ProposalPositioningDetail.from_dict(data.get("proposal_positioning", {})),
            publication_trends=PublicationTrends.from_dict(data.get("publication_trends", {})),
            career_comparison=[CareerComparisonRow.from_dict(cc) for cc in data.get("career_comparison", [])],
            research_environment=ResearchEnvironmentDetail.from_dict(data.get("research_environment", {})),
            final_profile=data.get("final_profile", ""),
            one_sentence_identity=data.get("one_sentence_identity", ""),
            recommendation=data.get("recommendation", ""),
            sources=DossierSourcesDetail.from_dict(data.get("sources", {})),
            recruitment=DossierRecruitmentItem.from_dict(data.get("recruitment", {}))
        )
