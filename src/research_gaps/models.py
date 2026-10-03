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


class Confidence:
    """Confidence level of an extracted/grouped research problem."""
    NORMAL = "normal"
    LOW = "low"


class ExtractionMethod:
    """How a paper's gap information was produced."""
    RULES = "rules"
    DETERMINISTIC = "deterministic"
    LEGACY_REGEX = "legacy_regex"


LEGACY_LOW_CONFIDENCE_REASON = "legacy_regex_extraction"


# ── Provenance primitives ───────────────────────────────────────────────

def canonical_paper_id(
    doi: Optional[str] = None,
    arxiv_id: Optional[str] = None,
    title: str = "",
    url: str = "",
) -> str:
    """Single source of truth for paper identifiers.

    Delegates to ResearchItem.generate_id() so ExtractedPaperInfo and
    ResearchItem can never disagree (previously one produced ``paper_<hash>``
    and the other ``doi_<hash>`` for the same paper).
    """
    from src.models import ResearchItem
    return ResearchItem(
        title=title or "", url=url or "", source="", doi=doi or None, arxiv_id=arxiv_id or None
    ).generate_id()


def _normalize_doi(doi: Optional[str]) -> Optional[str]:
    if not doi:
        return None
    clean = str(doi).strip()
    clean = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)', '', clean, flags=re.IGNORECASE)
    return clean or None


def _extract_year(date_str: Any) -> int:
    if not date_str:
        return 0
    match = re.search(r'(19|20)\d{2}', str(date_str))
    return int(match.group(0)) if match else 0


@dataclass
class EvidenceClaim:
    """A single claim (limitation / open question) bound to its source paper and text span."""
    claim_text: str = ""
    paper_id: str = ""
    supporting_span: str = ""

    def __str__(self) -> str:
        return self.claim_text

    def __repr__(self) -> str:
        return f"EvidenceClaim(claim_text={self.claim_text!r}, paper_id={self.paper_id!r}, supporting_span={self.supporting_span!r})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.claim_text == other
        if isinstance(other, EvidenceClaim):
            return (self.claim_text, self.paper_id) == (other.claim_text, other.paper_id)
        return False

    def __hash__(self) -> int:
        return hash((self.claim_text, self.paper_id))

    def lower(self) -> str:
        return self.claim_text.lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_text": self.claim_text,
            "paper_id": self.paper_id,
            "supporting_span": self.supporting_span,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceClaim":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def coerce(cls, value: Any, default_paper_id: str = "") -> "EvidenceClaim":
        """Accepts an EvidenceClaim, a dict, or a legacy plain string.

        Legacy strings were sentences lifted verbatim from an abstract by the
        old regex extractor, so the text doubles as its own supporting span.
        """
        if isinstance(value, EvidenceClaim):
            return value
        if isinstance(value, dict):
            return cls.from_dict(value)
        text = str(value)
        return cls(claim_text=text, paper_id=default_paper_id, supporting_span=text)


def coerce_claims(values: Any, default_paper_id: str = "") -> List[EvidenceClaim]:
    return [EvidenceClaim.coerce(v, default_paper_id) for v in (values or [])]


@dataclass
class Citation:
    """Bibliographic record rendered to users in place of internal paper IDs."""
    paper_id: str = ""
    doi: Optional[str] = None
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    venue: str = ""
    url: str = ""

    @classmethod
    def from_research_item(cls, item: Any) -> "Citation":
        return cls(
            paper_id=item.id,
            doi=_normalize_doi(item.doi),
            title=item.title or "",
            authors=list(item.authors or []),
            year=_extract_year(item.publication_date),
            venue=item.venue or "",
            url=item.url or "",
        )

    @property
    def link(self) -> str:
        """Canonical link: https://doi.org/<doi> when a DOI exists, else the source URL."""
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return self.url or ""

    def format_authors(self) -> str:
        names = [a for a in self.authors if a]
        if not names:
            return "Unknown authors"
        if len(names) > 3:
            return f"{names[0]} et al."
        if len(names) == 1:
            return names[0]
        return ", ".join(names[:-1]) + " & " + names[-1]

    def format(self) -> str:
        """'Authors (Year). Title. Venue.'"""
        year = str(self.year) if self.year else "n.d."
        title = (self.title or "Untitled").strip().rstrip('.')
        out = f"{self.format_authors()} ({year}). {title}."
        if self.venue:
            out += f" {self.venue.strip().rstrip('.')}."
        return out

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Citation":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


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
    research_question: str = ""
    why_unresolved: str = ""
    problem_span: str = ""
    proposed_approach: str = ""
    methodology: str = ""
    dataset_testbed: str = ""
    evaluation_metrics: List[str] = field(default_factory=list)
    main_contribution: str = ""
    limitations: List[EvidenceClaim] = field(default_factory=list)
    future_work: List[EvidenceClaim] = field(default_factory=list)  # open questions
    existing_approaches: List[str] = field(default_factory=list)
    candidate_methods: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    abstract: str = ""
    citation_count: int = 0
    extraction_method: str = ExtractionMethod.DETERMINISTIC
    source_scope: str = "abstract"
    prompt_version: str = ""
    confidence: str = Confidence.NORMAL
    low_confidence_reasons: List[str] = field(default_factory=list)
    discovery_date: str = field(default_factory=lambda: datetime.date.today().isoformat())

    def __post_init__(self):
        if not self.paper_id:
            self.paper_id = self._generate_id()
        self.limitations = coerce_claims(self.limitations, self.paper_id)
        self.future_work = coerce_claims(self.future_work, self.paper_id)

    def _generate_id(self) -> str:
        return canonical_paper_id(doi=self.doi, title=self.title, url=self.url)

    def to_citation(self) -> Citation:
        return Citation(
            paper_id=self.paper_id,
            doi=_normalize_doi(self.doi),
            title=self.title,
            authors=list(self.authors),
            year=self.year,
            venue=self.venue,
            url=self.url,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedPaperInfo":
        data = dict(data)
        legacy = "extraction_method" not in data
        pid = data.get("paper_id", "")
        if legacy:
            data["extraction_method"] = ExtractionMethod.LEGACY_REGEX
            data["confidence"] = Confidence.LOW
            data["low_confidence_reasons"] = [LEGACY_LOW_CONFIDENCE_REASON]
            if data.get("proposed_approach") and not data.get("candidate_methods"):
                data["candidate_methods"] = [data["proposed_approach"]]
        data["limitations"] = coerce_claims(data.get("limitations"), pid)
        data["future_work"] = coerce_claims(data.get("future_work"), pid)
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
    research_question: str = ""
    why_unresolved: str = ""
    research_area: str = ""
    problem_cluster: str = ""
    supporting_papers: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    frequency: int = 0
    existing_approaches: List[str] = field(default_factory=list)
    known_limitations: List[EvidenceClaim] = field(default_factory=list)
    unresolved_questions: List[EvidenceClaim] = field(default_factory=list)
    potential_research_questions: List[str] = field(default_factory=list)
    candidate_methods: List[str] = field(default_factory=list)
    evaluation_metrics: List[str] = field(default_factory=list)
    required_datasets: List[str] = field(default_factory=list)
    infrastructure_requirements: List[str] = field(default_factory=list)
    supervisor_keywords: List[str] = field(default_factory=list)
    status: str = ProblemStatus.NEW
    confidence: str = Confidence.NORMAL
    low_confidence_reasons: List[str] = field(default_factory=list)
    extraction_method: str = ExtractionMethod.DETERMINISTIC
    novelty_notes: str = ""
    significance_notes: str = ""
    feasibility_notes: str = ""
    publication_potential: str = ""
    last_updated: str = field(default_factory=lambda: datetime.date.today().isoformat())
    first_seen: str = field(default_factory=lambda: datetime.date.today().isoformat())

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
        default_pid = self.supporting_papers[0] if len(self.supporting_papers) == 1 else ""
        self.known_limitations = coerce_claims(self.known_limitations, default_pid)
        self.unresolved_questions = coerce_claims(self.unresolved_questions, default_pid)

    def _generate_id(self) -> str:
        norm = re.sub(r'[^a-zA-Z0-9]', '', self.problem_statement.lower())
        seed = f"{norm}|{self.research_area}"
        return f"prob_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    def limitation_texts(self) -> List[str]:
        return [c.claim_text for c in self.known_limitations]

    def question_texts(self) -> List[str]:
        return [c.claim_text for c in self.unresolved_questions]

    def mark_low_confidence(self, *reasons: str) -> None:
        self.confidence = Confidence.LOW
        for r in reasons:
            if r and r not in self.low_confidence_reasons:
                self.low_confidence_reasons.append(r)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchProblem":
        """Loads current-schema data and migrates pre-remediation records.

        Migration (records without ``extraction_method``): plain-string
        limitations/questions become EvidenceClaims, and the problem is marked
        low-confidence/legacy until it is regenerated by the new extractor.
        """
        data = dict(data)
        papers = data.get("supporting_papers") or []
        default_pid = papers[0] if len(papers) == 1 else ""
        data["known_limitations"] = coerce_claims(data.get("known_limitations"), default_pid)
        data["unresolved_questions"] = coerce_claims(data.get("unresolved_questions"), default_pid)
        if "extraction_method" not in data:
            data["extraction_method"] = ExtractionMethod.LEGACY_REGEX
            data["confidence"] = Confidence.LOW
            reasons = list(data.get("low_confidence_reasons") or [])
            if LEGACY_LOW_CONFIDENCE_REASON not in reasons:
                reasons.append(LEGACY_LOW_CONFIDENCE_REASON)
            data["low_confidence_reasons"] = reasons
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
