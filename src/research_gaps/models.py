"""Domain models for the Research Gap Analysis / PhD Topic Discovery module."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import datetime
import hashlib
import re


class ProblemStatus:
    """Status values for research problems."""
    NEW = "new"
    INVESTIGATING = "investigating"
    PROMISING = "promising"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    RESOLVED = "resolved"

    ALL = [NEW, INVESTIGATING, PROMISING, SHORTLISTED, REJECTED, RESOLVED]


class LinkStatus:
    """Status values for link verification."""
    VALID = "valid"
    REDIRECTED = "redirected"
    BROKEN = "broken"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"

    ALL = [VALID, REDIRECTED, BROKEN, UNREACHABLE, UNKNOWN]


@dataclass
class ExtractedPaperInfo:
    """Structured information extracted from a single paper for gap analysis."""
    paper_id: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    venue: str = ""
    doi: str = ""
    url: str = ""
    source: str = ""
    research_problem: str = ""
    proposed_approach: str = ""
    methodology: str = ""
    dataset_testbed: str = ""
    evaluation_metrics: List[str] = field(default_factory=list)
    main_contribution: str = ""
    limitations: List[str] = field(default_factory=list)
    future_work: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    abstract: str = ""
    citation_count: int = 0
    discovery_date: str = field(default_factory=lambda: datetime.date.today().isoformat())

    def __post_init__(self):
        if not self.paper_id:
            self.paper_id = self._generate_id()

    def _generate_id(self) -> str:
        if self.doi:
            clean_doi = self.doi.strip().lower()
            return f"paper_{hashlib.sha256(clean_doi.encode('utf-8')).hexdigest()[:16]}"
        norm_title = re.sub(r'[^a-zA-Z0-9]', '', self.title.lower())
        seed = f"{norm_title}|{self.url}"
        return f"paper_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedPaperInfo":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LinkVerificationResult:
    """Result of verifying an external URL."""
    url: str = ""
    canonical_url: str = ""
    link_status: str = LinkStatus.UNKNOWN
    http_status: int = 0
    last_verified: str = ""
    redirect_target: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinkVerificationResult":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ResearchProblem:
    """A tracked research problem/gap, backed by evidence from papers."""
    id: str = ""
    problem_statement: str = ""
    research_area: str = ""
    problem_cluster: str = ""
    supporting_papers: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    frequency: int = 0
    existing_approaches: List[str] = field(default_factory=list)
    known_limitations: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    potential_research_questions: List[str] = field(default_factory=list)
    candidate_methods: List[str] = field(default_factory=list)
    evaluation_metrics: List[str] = field(default_factory=list)
    required_datasets: List[str] = field(default_factory=list)
    infrastructure_requirements: List[str] = field(default_factory=list)
    supervisor_keywords: List[str] = field(default_factory=list)
    status: str = ProblemStatus.NEW
    novelty_notes: str = ""
    significance_notes: str = ""
    feasibility_notes: str = ""
    publication_potential: str = ""
    last_updated: str = field(default_factory=lambda: datetime.date.today().isoformat())
    first_seen: str = field(default_factory=lambda: datetime.date.today().isoformat())

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        norm = re.sub(r'[^a-zA-Z0-9]', '', self.problem_statement.lower())
        seed = f"{norm}|{self.research_area}"
        return f"prob_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchProblem":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ResearchGapCluster:
    """A cluster of related research problems/gaps."""
    cluster_id: str = ""
    name: str = ""
    description: str = ""
    research_area: str = ""
    supporting_papers: List[str] = field(default_factory=list)
    supporting_problems: List[str] = field(default_factory=list)
    recurring_limitations: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    frequency: int = 0
    first_seen: str = field(default_factory=lambda: datetime.date.today().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.date.today().isoformat())

    def __post_init__(self):
        if not self.cluster_id:
            self.cluster_id = self._generate_id()

    def _generate_id(self) -> str:
        norm = re.sub(r'[^a-zA-Z0-9]', '', self.name.lower())
        seed = f"{norm}|{self.research_area}"
        return f"cluster_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchGapCluster":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CandidateResearchDirection:
    """A generated candidate research direction for a PhD, tied to a problem."""
    direction_id: str = ""
    problem_id: str = ""
    research_problem: str = ""
    research_gap: str = ""
    research_questions: List[str] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    potential_contribution: str = ""
    possible_methodology: str = ""
    experimental_strategy: str = ""
    evaluation_metrics: List[str] = field(default_factory=list)
    required_datasets: List[str] = field(default_factory=list)
    infrastructure_requirements: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    unresolved_issues: List[str] = field(default_factory=list)
    evidence_supported: bool = True

    def __post_init__(self):
        if not self.direction_id:
            self.direction_id = self._generate_id()

    def _generate_id(self) -> str:
        norm = re.sub(r'[^a-zA-Z0-9]', '', self.research_problem.lower())
        seed = f"{norm}|{self.problem_id}"
        return f"dir_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateResearchDirection":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class FeasibilityAssessment:
    """Evidence-based feasibility assessment of a research problem for a PhD."""
    problem_id: str = ""
    novelty: str = ""
    novelty_evidence: str = ""
    significance: str = ""
    significance_evidence: str = ""
    feasibility: str = ""
    feasibility_evidence: str = ""
    data_availability: str = ""
    data_evidence: str = ""
    infrastructure_requirements: str = ""
    infrastructure_evidence: str = ""
    supervisor_fit: str = ""
    supervisor_fit_evidence: str = ""
    publication_potential: str = ""
    publication_evidence: str = ""
    phd_depth: str = ""
    phd_depth_evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeasibilityAssessment":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SupervisorMatch:
    """A potential supervisor matched to a research problem."""
    name: str = ""
    institution: str = ""
    country: str = ""
    relevant_research_areas: List[str] = field(default_factory=list)
    relevant_publications: List[Dict[str, Any]] = field(default_factory=list)
    matching_keywords: List[str] = field(default_factory=list)
    profile_url: str = ""
    google_scholar_url: str = ""
    semantic_scholar_url: str = ""
    link_status: str = LinkStatus.UNKNOWN
    match_score: float = 0.0
    match_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SupervisorMatch":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
