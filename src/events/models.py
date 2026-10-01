"""Domain models for Edge Computing Events & Academic/Industrial Conferences."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
import datetime
import hashlib
import re
from src.models import ResearchItem, ItemType, CredibilityTier, ScoreBreakdown


class EventType(str, Enum):
    ACADEMIC_CONFERENCE = "academic_conference"
    INDUSTRY_CONFERENCE = "industry_conference"
    WORKSHOP = "workshop"
    SYMPOSIUM = "symposium"
    WEBINAR = "webinar"
    TRAINING_PROGRAM = "training_program"
    SUMMER_SCHOOL = "summer_school"
    BOOTCAMP = "bootcamp"
    COURSE = "course"


class EventFormat(str, Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class FeeStatus(str, Enum):
    FREE = "free"
    PAID = "paid"
    HYBRID_FREE = "hybrid_free"  # e.g., free virtual attendance, paid in-person pass
    UNKNOWN = "unknown"


class EventStatus(str, Enum):
    UPCOMING = "upcoming"
    CFP_OPEN = "cfp_open"
    REGISTRATION_OPEN = "registration_open"
    ONGOING = "ongoing"
    CONCLUDED = "concluded"
    CANCELLED = "cancelled"


class DiscountType(str, Enum):
    STUDENT_RATE = "student_rate"
    TRAVEL_GRANT = "travel_grant"
    SCHOLARSHIP = "scholarship"
    EARLY_BIRD = "early_bird"
    FEE_WAIVER = "fee_waiver"
    MEMBERSHIP_DISCOUNT = "membership_discount"
    DEVELOPING_COUNTRY_RATE = "developing_country_rate"
    DIVERSITY_GRANT = "diversity_grant"


@dataclass
class DiscountOpportunity:
    """Represents a specific discount, scholarship, travel grant, or fee waiver."""
    discount_type: str
    name: str
    amount_or_rate: str = ""
    eligibility: str = ""
    deadline: Optional[str] = None
    application_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiscountOpportunity":
        return cls(**data)


@dataclass
class EventScoreBreakdown:
    """Transparent 0-10 multi-factor relevance scoring breakdown for Edge events."""
    topic_score: float = 0.0          # 0 - 4.0 points (Edge computing, Edge AI, MEC, Fog, etc.)
    credibility_score: float = 0.0      # 0 - 2.5 points (IEEE, ACM, USENIX, LF Edge, CNCF, universities)
    affordability_boost: float = 0.0    # 0 - 1.5 points (Free, travel grant, student rate, waiver)
    actionability_boost: float = 0.0    # 0 - 1.0 points (CFP open, early bird open, upcoming window)
    phd_value_boost: float = 0.0        # 0 - 1.0 points (Doctoral consortium, student tracks, tutorials)
    negative_penalty: float = 0.0       # -5.0 to 0.0 (Crypto, promotional spam, non-technical, expired)
    final_score: float = 0.0            # 0.0 to 10.0
    matched_topics: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventScoreBreakdown":
        return cls(**data)


@dataclass
class EdgeEvent:
    """Rich domain model for Edge Computing academic and industrial events."""
    event_name: str
    organizer: str
    event_type: str = EventType.ACADEMIC_CONFERENCE.value
    description: str = ""
    topics: List[str] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: str = ""
    format: str = EventFormat.HYBRID.value
    official_website: str = ""
    registration_url: str = ""
    registration_fee: str = ""
    fee_status: str = FeeStatus.PAID.value
    discounts_subsidies: List[DiscountOpportunity] = field(default_factory=list)
    discount_eligibility: str = ""
    has_student_discount: bool = False
    has_travel_grant: bool = False
    has_scholarship: bool = False
    has_early_bird: bool = False
    has_fee_waiver: bool = False
    cfp_deadline: Optional[str] = None
    important_dates: Dict[str, str] = field(default_factory=dict)
    target_audience: List[str] = field(default_factory=list)
    country: str = ""
    region: str = ""
    source_url: str = ""
    source: str = ""
    discovery_date: str = field(default_factory=lambda: datetime.date.today().isoformat())
    last_verified_date: str = field(default_factory=lambda: datetime.date.today().isoformat())
    status: str = EventStatus.UPCOMING.value
    relevance_score: float = 0.0
    score: Optional[EventScoreBreakdown] = None
    id: str = ""
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = self.generate_id()
        # Derive boolean flags if discounts are present in list
        if self.discounts_subsidies:
            types = {d.discount_type for d in self.discounts_subsidies}
            if DiscountType.STUDENT_RATE.value in types:
                self.has_student_discount = True
            if DiscountType.TRAVEL_GRANT.value in types:
                self.has_travel_grant = True
            if DiscountType.SCHOLARSHIP.value in types:
                self.has_scholarship = True
            if DiscountType.EARLY_BIRD.value in types:
                self.has_early_bird = True
            if DiscountType.FEE_WAIVER.value in types:
                self.has_fee_waiver = True

    def generate_id(self) -> str:
        """Generates a deterministic unique hash for deduplication."""
        norm_name = re.sub(r'[^a-zA-Z0-9]', '', self.event_name.lower())
        norm_url = re.sub(r'^https?://(www\.)?', '', (self.official_website or self.source_url).lower().rstrip('/'))
        # Include year if detectable from start_date or event_name
        year_match = re.search(r'(20\d{2})', f"{self.start_date or ''} {self.event_name}")
        year_str = year_match.group(1) if year_match else "any"
        seed = f"{norm_name}|{year_str}|{norm_url}"
        return f"evt_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.score:
            data["score"] = self.score.to_dict()
        data["discounts_subsidies"] = [d.to_dict() for d in self.discounts_subsidies]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EdgeEvent":
        data_copy = dict(data)
        score_data = data_copy.pop("score", None)
        discounts_data = data_copy.pop("discounts_subsidies", [])

        score = EventScoreBreakdown.from_dict(score_data) if score_data else None
        discounts = [
            d if isinstance(d, DiscountOpportunity) else DiscountOpportunity.from_dict(d)
            for d in discounts_data
        ]

        event = cls(**data_copy)
        event.score = score
        event.discounts_subsidies = discounts
        return event

    def to_research_item(self) -> ResearchItem:
        """Bridges event into general pipeline ResearchItem for daily/weekly digest integration."""
        item_type = ItemType.EVENT.value
        if self.event_type in [EventType.ACADEMIC_CONFERENCE.value, EventType.INDUSTRY_CONFERENCE.value]:
            item_type = ItemType.CONFERENCE_CFP.value if self.cfp_deadline else ItemType.EVENT.value
        elif self.event_type in [EventType.WORKSHOP.value, EventType.SYMPOSIUM.value]:
            item_type = ItemType.WORKSHOP.value

        # Determine credibility tier
        org_lower = (self.organizer or "").lower()
        if any(top in org_lower for top in ["ieee", "acm", "usenix"]):
            tier = CredibilityTier.TIER1_ACADEMIC_STANDARDS.value
        elif any(lab in org_lower for lab in ["university", "harvard", "cambridge", "ictp", "lab", "poly"]):
            tier = CredibilityTier.TIER2_UNIVERSITY_LAB.value
        elif any(ind in org_lower for ind in ["linux foundation", "cncf", "topio", "industry", "openinfra"]):
            tier = CredibilityTier.TIER4_INDUSTRY.value
        else:
            tier = CredibilityTier.TIER3_CONFERENCE.value

        score_breakdown = ScoreBreakdown(
            topic_score=self.score.topic_score if self.score else (self.relevance_score * 0.4),
            credibility_score=self.score.credibility_score if self.score else 2.0,
            recency_score=1.5,
            stage_boost=self.score.affordability_boost if self.score else 0.5,
            phd_boost=self.score.phd_value_boost if self.score else 0.5,
            negative_penalty=self.score.negative_penalty if self.score else 0.0,
            final_score=self.relevance_score,
            matched_topics=self.topics,
            reasons=self.score.reasons if self.score else [f"Edge Computing event organized by {self.organizer}"]
        )

        abstract = (
            f"[{self.event_type.replace('_', ' ').title()}] {self.description} "
            f"Dates: {self.start_date or 'TBA'} to {self.end_date or 'TBA'}. Location: {self.location} ({self.format}). "
            f"Registration Fee: {self.registration_fee or self.fee_status.title()}."
        )
        if self.discounts_subsidies:
            disc_summary = "; ".join(f"{d.name}: {d.amount_or_rate}" for d in self.discounts_subsidies[:2])
            abstract += f" Subsidies: {disc_summary}."

        is_urgent = False
        if self.cfp_deadline:
            try:
                deadline_dt = datetime.date.fromisoformat(self.cfp_deadline)
                days_left = (deadline_dt - datetime.date.today()).days
                if 0 <= days_left <= 14:
                    is_urgent = True
            except Exception:
                pass

        return ResearchItem(
            title=self.event_name,
            url=self.official_website or self.registration_url or self.source_url,
            source=f"{self.organizer} ({self.source or 'Events'})",
            source_tier=tier,
            item_type=item_type,
            authors=[self.organizer] if self.organizer else [],
            publication_date=self.discovery_date,
            discovery_date=self.discovery_date,
            abstract=abstract,
            venue=f"{self.event_name} — {self.location or self.format}",
            topics=self.topics,
            institution=self.organizer,
            location=self.location,
            deadline=self.cfp_deadline or (self.important_dates.get("early_bird_deadline") if self.important_dates else None),
            is_urgent=is_urgent,
            score=score_breakdown,
            opportunity_data={
                "kind": "event",
                "event_type": self.event_type,
                "event_name": self.event_name,
                "organizer": self.organizer,
                "format": self.format,
                "location": self.location,
                "fee_status": self.fee_status,
                "has_student_discount": self.has_student_discount,
                "has_travel_grant": self.has_travel_grant,
                "discounts_count": len(self.discounts_subsidies),
                "official_website": self.official_website,
                "cfp_deadline": self.cfp_deadline
            },
            id=self.id
        )
