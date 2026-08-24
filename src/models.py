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
