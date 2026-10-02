"""Normalizer engine for Edge Computing events."""

import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
from dateutil import parser as date_parser
from src.events.models import (
    EdgeEvent,
    EventType,
    EventFormat,
    FeeStatus,
    EventStatus,
    DiscountType,
    DiscountOpportunity
)
from src.utils.logger import logger


class EventNormalizer:
    """Normalizes unstructured or semi-structured event data into standardized EdgeEvent domain models."""

    def __init__(self, discount_rules: Optional[Dict[str, Any]] = None):
        self.discount_rules = discount_rules or {}

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """Cleans whitespace, HTML entities, and formatting artifacts."""
        if not text:
            return ""
        # Remove HTML tags if present
        cleaned = re.sub(r'<[^>]+>', ' ', text)
        return " ".join(cleaned.split()).strip()

    def normalize_event_type(self, raw_type: Optional[str], title: str, description: str) -> str:
        """Infers standardized EventType from text and raw hints."""
        combined = f"{raw_type or ''} {title} {description}".lower()

        if any(w in combined for w in ["bootcamp", "boot camp"]):
            return EventType.BOOTCAMP.value
        if any(w in combined for w in ["summer school", "winter school", "spring school", "autumn school"]):
            return EventType.SUMMER_SCHOOL.value
        if any(w in combined for w in ["training program", "training course", "hands-on course", "masterclass", "tutorial series"]):
            return EventType.TRAINING_PROGRAM.value
        if any(w in combined for w in ["webinar", "virtual tech talk", "online seminar", "distinguished lecture"]):
            return EventType.WEBINAR.value
        if any(w in combined for w in ["workshop", "workshops"]):
            return EventType.WORKSHOP.value
        if any(w in combined for w in ["symposium", "symposia"]):
            return EventType.SYMPOSIUM.value
        if any(w in combined for w in ["summit", "industry conference", "world congress", "expo", "kubecon"]):
            return EventType.INDUSTRY_CONFERENCE.value
        if any(w in combined for w in ["conference", "call for papers", "cfp", "infocom", "mobicom", "icdcs", "sensys"]):
            return EventType.ACADEMIC_CONFERENCE.value

        return EventType.ACADEMIC_CONFERENCE.value

    def normalize_format(self, location: str, format_hint: Optional[str] = None) -> str:
        """Determines EventFormat (in_person, online, hybrid)."""
        combined = f"{location} {format_hint or ''}".lower()
        if "hybrid" in combined:
            return EventFormat.HYBRID.value
        if any(w in combined for w in ["online", "virtual", "remote", "webinar", "zoom"]):
            return EventFormat.ONLINE.value
        if location and location.lower() not in ["tbd", "tba", "unknown"]:
            return EventFormat.IN_PERSON.value
        return EventFormat.HYBRID.value

    def parse_dates(self, raw_start: Any, raw_end: Any = None, text: str = "") -> Tuple[Optional[str], Optional[str]]:
        """Parses start and end dates into ISO 8601 YYYY-MM-DD strings."""
        start_str: Optional[str] = None
        end_str: Optional[str] = None

        # Try parsing explicit start/end
        if raw_start:
            try:
                if isinstance(raw_start, (datetime.date, datetime.datetime)):
                    start_str = raw_start.strftime("%Y-%m-%d")
                else:
                    start_dt = date_parser.parse(str(raw_start), fuzzy=True)
                    start_str = start_dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        if raw_end:
            try:
                if isinstance(raw_end, (datetime.date, datetime.datetime)):
                    end_str = raw_end.strftime("%Y-%m-%d")
                else:
                    end_dt = date_parser.parse(str(raw_end), fuzzy=True)
                    end_str = end_dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        # If start_str is missing, look for dates in text (e.g., Nov 10-12, 2026 or 2026-11-10)
        if not start_str and text:
            # Pattern: YYYY-MM-DD
            iso_match = re.search(r'\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b', text)
            if iso_match:
                start_str = iso_match.group(0).replace('/', '-')

        if start_str and not end_str:
            end_str = start_str

        return start_str, end_str

    def parse_fee_and_discounts(
        self,
        raw_fee: str = "",
        text: str = "",
        explicit_discounts: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, str, List[DiscountOpportunity], str]:
        """
        Parses fee information, fee status, list of discount opportunities, and eligibility summary.
        Returns: (registration_fee, fee_status, discounts_list, discount_eligibility_text)
        """
        combined = f"{raw_fee} {text}".lower()
        fee_str = self.clean_text(raw_fee)
        discounts: List[DiscountOpportunity] = []
        eligibility_notes: List[str] = []

        # Determine fee status
        has_free_signal = "free" in raw_fee.lower() or any(w in combined for w in ["100% free", "free registration", "free admission", "free attendance", "no fee", "free to attend", "free virtual", "complimentary registration"])
        has_paid_signal = (bool(raw_fee) and "free" not in raw_fee.lower()) or any(sym in combined for sym in ["$", "€", "£", "¥", "usd", "eur", "gbp", "paid", "regular attendees", "in-person pass", "in-person ticket", "onsite fee"])

        if has_free_signal and has_paid_signal:
            fee_status = FeeStatus.HYBRID_FREE.value
            if not fee_str:
                match = re.search(r'([$€£¥]\s*\d+(?:,\d+)*(?:\.\d+)?|\b\d+\s*(?:usd|eur|gbp))', combined)
                fee_str = f"Free (Virtual) / {match.group(0).upper() if match else 'Paid'}"
        elif has_free_signal:
            fee_status = FeeStatus.FREE.value
            if not fee_str:
                fee_str = "Free"
        elif has_paid_signal:
            fee_status = FeeStatus.PAID.value
            if not fee_str:
                match = re.search(r'([$€£¥]\s*\d+(?:,\d+)*(?:\.\d+)?|\b\d+\s*(?:usd|eur|gbp))', combined)
                if match:
                    fee_str = match.group(0).upper()
        else:
            fee_status = FeeStatus.UNKNOWN.value

        # Parse explicit discounts if provided
        if explicit_discounts:
            for d in explicit_discounts:
                if isinstance(d, DiscountOpportunity):
                    discounts.append(d)
                elif isinstance(d, dict):
                    discounts.append(DiscountOpportunity.from_dict(d))
                if d.get("eligibility") if isinstance(d, dict) else getattr(d, "eligibility", None):
                    elig = d.get("eligibility") if isinstance(d, dict) else getattr(d, "eligibility", "")
                    if elig:
                        eligibility_notes.append(elig)

        # Detect Student Rates in text
        if any(w in combined for w in ["student rate", "student registration", "student discount", "student member", "acm student", "ieee student"]):
            if not any(d.discount_type == DiscountType.STUDENT_RATE.value for d in discounts):
                match = re.search(r'student(?:\s+\w+){0,3}\s*:\s*([$€£¥]?\d+(?:\s*(?:usd|eur|gbp))?)', combined)
                rate_str = match.group(0) if match else "Subsidized student rate available"
                discounts.append(DiscountOpportunity(
                    discount_type=DiscountType.STUDENT_RATE.value,
                    name="Student Registration Rate",
                    amount_or_rate=rate_str,
                    eligibility="Full-time enrolled undergraduate and graduate students with valid student ID."
                ))
                eligibility_notes.append("Enrolled students with valid ID qualify for student rates.")

        # Detect Travel Grants in text
        if any(w in combined for w in ["travel grant", "student travel grant", "travel award", "travel stipend", "stg"]):
            if not any(d.discount_type == DiscountType.TRAVEL_GRANT.value for d in discounts):
                discounts.append(DiscountOpportunity(
                    discount_type=DiscountType.TRAVEL_GRANT.value,
                    name="Student Travel Grant",
                    amount_or_rate="Travel and lodging stipend + conference registration assistance",
                    eligibility="Graduate students presenting papers or participating in doctoral symposium."
                ))
                eligibility_notes.append("Travel grant applications open for participating student researchers.")

        # Detect Scholarships in text
        if any(w in combined for w in ["scholarship", "diversity scholarship", "attendance grant", "inclusion grant"]):
            if not any(d.discount_type == DiscountType.SCHOLARSHIP.value for d in discounts):
                discounts.append(DiscountOpportunity(
                    discount_type=DiscountType.SCHOLARSHIP.value,
                    name="Conference Attendance Scholarship",
                    amount_or_rate="Full registration waiver and travel support",
                    eligibility="Eligible graduate students and underrepresented participants in computing."
                ))
                eligibility_notes.append("Scholarships open to graduate students and underrepresented groups.")

        # Detect Early Bird in text
        if any(w in combined for w in ["early bird", "early-bird", "advance registration", "early registration"]):
            if not any(d.discount_type == DiscountType.EARLY_BIRD.value for d in discounts):
                discounts.append(DiscountOpportunity(
                    discount_type=DiscountType.EARLY_BIRD.value,
                    name="Early-Bird Discount",
                    amount_or_rate="Discounted admission prior to cutoff deadline",
                    eligibility="All attendees registering before the early-bird deadline."
                ))

        # Detect Fee Waivers in text
        if any(w in combined for w in ["fee waiver", "hardship waiver", "complimentary registration", "free virtual", "100% free", "free registration"]):
            if not any(d.discount_type == DiscountType.FEE_WAIVER.value for d in discounts):
                discounts.append(DiscountOpportunity(
                    discount_type=DiscountType.FEE_WAIVER.value,
                    name="Registration Fee Waiver",
                    amount_or_rate="100% Registration fee waiver",
                    eligibility="Available upon request or for virtual attendees."
                ))

        discount_eligibility_str = " ".join(dict.fromkeys(eligibility_notes))
        return fee_str, fee_status, discounts, discount_eligibility_str

    def parse_important_dates(
        self,
        raw_cfp: Optional[str] = None,
        dates_dict: Optional[Dict[str, str]] = None,
        text: str = ""
    ) -> Tuple[Optional[str], Dict[str, str]]:
        """Extracts CFP submission deadline and structured important dates dictionary."""
        structured_dates: Dict[str, str] = dict(dates_dict or {})
        cfp_deadline: Optional[str] = None

        if raw_cfp:
            try:
                cfp_dt = date_parser.parse(str(raw_cfp), fuzzy=True)
                cfp_deadline = cfp_dt.strftime("%Y-%m-%d")
                structured_dates["cfp_deadline"] = cfp_deadline
            except Exception:
                pass

        if not cfp_deadline and text:
            # Look for patterns like "Submission deadline: YYYY-MM-DD" or "CFP: Month DD, YYYY"
            match = re.search(r'(?:submission\s+deadline|paper\s+deadline|cfp\s+deadline|due\s+date)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+20\d{2}|20\d{2}[-/]\d{1,2}[-/]\d{1,2})', text, re.IGNORECASE)
            if match:
                try:
                    cfp_dt = date_parser.parse(match.group(1), fuzzy=True)
                    cfp_deadline = cfp_dt.strftime("%Y-%m-%d")
                    structured_dates["cfp_deadline"] = cfp_deadline
                except Exception:
                    pass

        return cfp_deadline, structured_dates

    def normalize(self, raw_data: Dict[str, Any]) -> EdgeEvent:
        """Converts raw dictionary into a fully normalized EdgeEvent."""
        name = self.clean_text(raw_data.get("event_name") or raw_data.get("title") or "Unnamed Edge Event")
        organizer = self.clean_text(raw_data.get("organizer") or "Professional Organization")
        description = self.clean_text(raw_data.get("description") or raw_data.get("summary") or "")

        event_type = self.normalize_event_type(
            raw_data.get("event_type"),
            name,
            description
        )

        location = self.clean_text(raw_data.get("location") or "")
        format_type = self.normalize_format(location, raw_data.get("format"))

        start_date, end_date = self.parse_dates(
            raw_data.get("start_date"),
            raw_data.get("end_date"),
            f"{name} {description}"
        )

        fee_str, fee_status, discounts, disc_eligibility = self.parse_fee_and_discounts(
            raw_fee=str(raw_data.get("registration_fee") or ""),
            text=description,
            explicit_discounts=raw_data.get("discounts_subsidies")
        )

        cfp_deadline, important_dates = self.parse_important_dates(
            raw_cfp=raw_data.get("cfp_deadline") or raw_data.get("deadline"),
            dates_dict=raw_data.get("important_dates"),
            text=description
        )

        # Topics
        topics = list(raw_data.get("topics") or [])
        if not topics:
            core_edge_topics = [
                "Edge Computing", "Edge AI", "Edge Intelligence", "MEC", "Fog Computing",
                "Distributed Systems", "TinyML", "Cloud-Edge", "IoT", "Federated Learning"
            ]
            combined_desc = f"{name} {description}".lower()
            topics = [t for t in core_edge_topics if t.lower() in combined_desc]
            if not topics:
                topics = ["Edge Computing"]

        # Target audience
        audience = list(raw_data.get("target_audience") or [])
        if not audience:
            audience = ["PhD Researchers", "Distributed Systems Engineers", "Graduate Students"]

        event = EdgeEvent(
            event_name=name,
            organizer=organizer,
            event_type=event_type,
            description=description,
            topics=topics,
            start_date=start_date,
            end_date=end_date,
            location=location or ("Online" if format_type == EventFormat.ONLINE.value else "TBD"),
            format=format_type,
            official_website=self.clean_text(raw_data.get("official_website") or raw_data.get("url") or raw_data.get("link") or ""),
            registration_url=self.clean_text(raw_data.get("registration_url") or raw_data.get("official_website") or ""),
            registration_fee=fee_str,
            fee_status=fee_status,
            discounts_subsidies=discounts,
            discount_eligibility=disc_eligibility,
            cfp_deadline=cfp_deadline,
            important_dates=important_dates,
            target_audience=audience,
            country=self.clean_text(raw_data.get("country") or ""),
            region=self.clean_text(raw_data.get("region") or ""),
            source_url=self.clean_text(raw_data.get("source_url") or raw_data.get("url") or ""),
            source=self.clean_text(raw_data.get("source") or organizer),
            status=raw_data.get("status") or EventStatus.UPCOMING.value,
            raw_metadata=raw_data
        )

        return event
