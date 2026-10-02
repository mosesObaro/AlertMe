"""Deduplication engine for academic and industrial Edge Computing events."""

import re
import difflib
from typing import List, Tuple, Optional, Set
from src.events.models import EdgeEvent, DiscountOpportunity
from src.utils.logger import logger


def normalize_event_url(url: str) -> str:
    """Canonicalizes event URL by stripping protocol, www, trailing slashes, and anchor tags."""
    if not url:
        return ""
    cleaned = url.strip().lower()
    cleaned = re.sub(r'^https?://', '', cleaned)
    cleaned = re.sub(r'^www\.', '', cleaned)
    cleaned = re.sub(r'[?#].*$', '', cleaned)
    return cleaned.rstrip('/')


def normalize_event_title(title: str) -> str:
    """Normalizes title string for robust fuzzy comparison."""
    if not title:
        return ""
    # Strip brackets like [CFP], [SEC 2026], [Workshop]
    cleaned = re.sub(r'^\[[^\]]+\]\s*', '', title)
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned.lower())
    return " ".join(cleaned.split())


def extract_event_year(text: str) -> Optional[str]:
    """Extracts 4-digit year from text (e.g., 2026 or 2027)."""
    match = re.search(r'\b(20\d{2})\b', text)
    return match.group(1) if match else None


def extract_acronym(text: str) -> Optional[str]:
    """Extracts known conference acronyms (e.g., SEC, INFOCOM, MOBICOM, NEURIPS, SENSYS, IPSN, RTSS, etc.)."""
    common_acronyms = [
        # Edge & Systems
        "sec", "infocom", "mobicom", "atc", "nsdi", "icdcs", "sensys",
        "secon", "edgesys", "hotedge", "kubecon", "openinfra", "mobisys",
        # Machine Learning / AI
        "neurips", "iclr", "icml", "cvpr", "eccv", "iccv", "aaai", "ijcai", "tinyml",
        # Embedded Systems & IoT
        "emsoft", "ipsn", "rtss", "rtas", "iccps", "date", "dac", "cases", "codes",
        "iotdi", "ewsn", "iotswc"
    ]
    words = re.findall(r'\b[a-zA-Z0-9\-]+\b', text.lower())
    for w in words:
        if w in common_acronyms:
            return w
    return None


class EventDeduplicator:
    """Deduplicates events across URLs, acronyms, and fuzzy titles with rich metadata merging."""

    def __init__(self, similarity_threshold: float = 0.82):
        self.similarity_threshold = similarity_threshold

    def is_duplicate(self, event: EdgeEvent, pool: List[EdgeEvent]) -> Tuple[bool, Optional[EdgeEvent]]:
        """Checks if event matches any existing event in the pool."""
        ev_url = normalize_event_url(event.official_website or event.source_url)
        ev_norm_title = normalize_event_title(event.event_name)
        ev_year = extract_event_year(f"{event.event_name} {event.start_date or ''}")
        ev_acronym = extract_acronym(event.event_name)

        for existing in pool:
            # 1. Exact ID match
            if event.id and existing.id and event.id == existing.id:
                return True, existing

            # 2. Exact Canonical URL match
            exist_url = normalize_event_url(existing.official_website or existing.source_url)
            if ev_url and exist_url and ev_url == exist_url:
                return True, existing

            # Check year alignment: if both have years and they differ, they are distinct editions (e.g. 2026 vs 2027)
            exist_year = extract_event_year(f"{existing.event_name} {existing.start_date or ''}")
            if ev_year and exist_year and ev_year != exist_year:
                continue

            # 3. Acronym Match (if same year)
            exist_acronym = extract_acronym(existing.event_name)
            if ev_acronym and exist_acronym and ev_acronym == exist_acronym:
                if (ev_year and exist_year and ev_year == exist_year) or (not ev_year and not exist_year):
                    return True, existing

            # 4. Fuzzy Title Similarity
            exist_norm_title = normalize_event_title(existing.event_name)
            if ev_norm_title and exist_norm_title:
                ratio = difflib.SequenceMatcher(None, ev_norm_title, exist_norm_title).ratio()
                if ratio >= self.similarity_threshold:
                    return True, existing

        return False, None

    def merge_events(self, base: EdgeEvent, incoming: EdgeEvent) -> EdgeEvent:
        """Merges richer metadata from incoming event into the base event."""
        # Merge descriptions
        if len(incoming.description) > len(base.description):
            base.description = incoming.description

        # Merge website links
        if not base.official_website and incoming.official_website:
            base.official_website = incoming.official_website
        if not base.registration_url and incoming.registration_url:
            base.registration_url = incoming.registration_url

        # Merge dates if missing
        if not base.start_date and incoming.start_date:
            base.start_date = incoming.start_date
        if not base.end_date and incoming.end_date:
            base.end_date = incoming.end_date
        if not base.cfp_deadline and incoming.cfp_deadline:
            base.cfp_deadline = incoming.cfp_deadline

        # Merge discounts & subsidies
        existing_types = {d.discount_type for d in base.discounts_subsidies}
        for inc_d in incoming.discounts_subsidies:
            if inc_d.discount_type not in existing_types:
                base.discounts_subsidies.append(inc_d)
                existing_types.add(inc_d.discount_type)

        # Merge topics
        combined_topics = list(dict.fromkeys(base.topics + incoming.topics))
        base.topics = combined_topics

        # Re-derive boolean flags
        base.has_student_discount = base.has_student_discount or incoming.has_student_discount
        base.has_travel_grant = base.has_travel_grant or incoming.has_travel_grant
        base.has_scholarship = base.has_scholarship or incoming.has_scholarship
        base.has_early_bird = base.has_early_bird or incoming.has_early_bird
        base.has_fee_waiver = base.has_fee_waiver or incoming.has_fee_waiver

        return base

    def deduplicate(
        self,
        events: List[EdgeEvent],
        seen_ids: Optional[Set[str]] = None
    ) -> List[EdgeEvent]:
        """Deduplicates a list of events against each other and against seen IDs."""
        seen_ids = seen_ids or set()
        unique_events: List[EdgeEvent] = []

        for event in events:
            if event.id in seen_ids:
                continue

            is_dup, existing_match = self.is_duplicate(event, unique_events)
            if is_dup and existing_match:
                self.merge_events(existing_match, event)
            else:
                unique_events.append(event)

        return unique_events
