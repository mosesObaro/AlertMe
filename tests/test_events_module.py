"""Comprehensive tests for the Edge Computing Events module.
Covers collection, normalization, deduplication, verification, discounts/subsidies, scoring, and state tracking.
"""

import datetime
from pathlib import Path
import pytest
from src.events.models import (
    EdgeEvent,
    EventType,
    EventFormat,
    FeeStatus,
    EventStatus,
    DiscountType,
    DiscountOpportunity,
    EventScoreBreakdown
)
from src.events.normalizer import EventNormalizer
from src.events.deduplicator import EventDeduplicator
from src.events.verifier import EventVerifier
from src.events.scorer import EventScorer
from src.events.collector import EdgeEventCollector
from src.events.state_manager import EventsStateManager
from src.events.pipeline import EdgeEventsPipeline
from src.models import ItemType, CredibilityTier


# =============================================================================
# 1. MODEL TESTS
# =============================================================================

def test_event_model_serialization_and_id():
    discount = DiscountOpportunity(
        discount_type=DiscountType.STUDENT_RATE.value,
        name="Student Registration",
        amount_or_rate="$150",
        eligibility="Full time students with valid ID",
        deadline="2026-10-15"
    )
    event = EdgeEvent(
        event_name="ACM/IEEE Symposium on Edge Computing (SEC 2026)",
        organizer="ACM / IEEE Computer Society",
        event_type=EventType.ACADEMIC_CONFERENCE.value,
        description="Flagship forum for edge computing systems.",
        topics=["Edge Computing", "Edge AI", "Cloudlets"],
        start_date="2026-11-10",
        end_date="2026-11-12",
        location="Seattle, WA, USA",
        format=EventFormat.HYBRID.value,
        official_website="https://acm-ieee-sec.org/2026/",
        discounts_subsidies=[discount],
        cfp_deadline="2026-06-15"
    )

    # Boolean flag auto-derived in __post_init__
    assert event.has_student_discount is True
    assert event.id.startswith("evt_")

    # Roundtrip serialization
    d = event.to_dict()
    assert d["event_name"] == event.event_name
    assert len(d["discounts_subsidies"]) == 1
    assert d["discounts_subsidies"][0]["amount_or_rate"] == "$150"

    rebuilt = EdgeEvent.from_dict(d)
    assert rebuilt.event_name == event.event_name
    assert rebuilt.id == event.id
    assert rebuilt.has_student_discount is True
    assert len(rebuilt.discounts_subsidies) == 1
    assert rebuilt.discounts_subsidies[0].discount_type == DiscountType.STUDENT_RATE.value


def test_event_to_research_item_bridge():
    event = EdgeEvent(
        event_name="IEEE INFOCOM 2027",
        organizer="IEEE Communications Society",
        event_type=EventType.ACADEMIC_CONFERENCE.value,
        description="Top-tier conference on networking and mobile edge computing.",
        topics=["Mobile Edge Computing", "Distributed Algorithms"],
        start_date="2027-04-18",
        end_date="2027-04-21",
        location="London, UK",
        format=EventFormat.IN_PERSON.value,
        official_website="https://infocom2027.ieee-infocom.org/",
        registration_fee="£420 (Student) / £890 (Regular)",
        fee_status=FeeStatus.PAID.value,
        has_student_discount=True,
        has_travel_grant=True,
        cfp_deadline="2026-10-15"
    )

    research_item = event.to_research_item()
    assert research_item.title == "IEEE INFOCOM 2027"
    assert research_item.item_type == ItemType.CONFERENCE_CFP.value
    assert research_item.source_tier == CredibilityTier.TIER1_ACADEMIC_STANDARDS.value
    assert "Mobile Edge Computing" in research_item.topics
    assert research_item.opportunity_data is not None
    assert research_item.opportunity_data.get("kind") == "event"
    assert research_item.opportunity_data.get("has_travel_grant") is True


# =============================================================================
# 2. NORMALIZATION TESTS
# =============================================================================

def test_normalizer_infers_event_types():
    normalizer = EventNormalizer()

    assert normalizer.normalize_event_type(None, "LF Edge Developer Bootcamp 2026", "") == EventType.BOOTCAMP.value
    assert normalizer.normalize_event_type(None, "TinyML Summer School 2027", "") == EventType.SUMMER_SCHOOL.value
    assert normalizer.normalize_event_type(None, "IEEE ComSoc Technical Webinar on 6G", "") == EventType.WEBINAR.value
    assert normalizer.normalize_event_type(None, "ACM EdgeSys Workshop", "") == EventType.WORKSHOP.value
    assert normalizer.normalize_event_type(None, "ACM/IEEE Symposium on Edge Computing", "") == EventType.SYMPOSIUM.value
    assert normalizer.normalize_event_type(None, "KubeCon + CloudNativeCon Europe", "Industry summit") == EventType.INDUSTRY_CONFERENCE.value
    assert normalizer.normalize_event_type(None, "IEEE INFOCOM 2027", "") == EventType.ACADEMIC_CONFERENCE.value


def test_normalizer_parses_dates_and_formats():
    normalizer = EventNormalizer()

    # Explicit dates
    s, e = normalizer.parse_dates("2026-11-10", "2026-11-12")
    assert s == "2026-11-10"
    assert e == "2026-11-12"

    # Inferred format
    assert normalizer.normalize_format("Seattle, WA, USA", "hybrid") == EventFormat.HYBRID.value
    assert normalizer.normalize_format("Online / Virtual", None) == EventFormat.ONLINE.value
    assert normalizer.normalize_format("Munich, Germany", None) == EventFormat.IN_PERSON.value


def test_normalizer_detects_subsidies_and_fees():
    normalizer = EventNormalizer()

    desc = (
        "Registration is $400 for regular attendees. A subsidized student rate of $150 is available for enrolled students. "
        "ACM SIGMOBILE offers a student travel grant of up to $1,000. Early-bird registration closes October 1st. "
        "Virtual attendees receive 100% free registration."
    )

    fee_str, fee_status, discounts, elig = normalizer.parse_fee_and_discounts(
        raw_fee="$400",
        text=desc
    )

    assert fee_status == FeeStatus.HYBRID_FREE.value
    types = {d.discount_type for d in discounts}
    assert DiscountType.STUDENT_RATE.value in types
    assert DiscountType.TRAVEL_GRANT.value in types
    assert DiscountType.EARLY_BIRD.value in types
    assert DiscountType.FEE_WAIVER.value in types
    assert len(elig) > 0


# =============================================================================
# 3. DEDUPLICATION TESTS
# =============================================================================

def test_deduplicator_exact_url_and_id_match():
    deduplicator = EventDeduplicator()

    ev1 = EdgeEvent(
        event_name="ACM/IEEE Symposium on Edge Computing (SEC 2026)",
        organizer="ACM / IEEE",
        official_website="https://acm-ieee-sec.org/2026/",
        start_date="2026-11-10"
    )

    ev2 = EdgeEvent(
        event_name="SEC 2026 Edge Computing Symposium",
        organizer="ACM Computer Society",
        official_website="https://acm-ieee-sec.org/2026",
        start_date="2026-11-10"
    )

    is_dup, match = deduplicator.is_duplicate(ev2, [ev1])
    assert is_dup is True
    assert match == ev1


def test_deduplicator_acronym_and_year_matching():
    deduplicator = EventDeduplicator()

    ev1 = EdgeEvent(
        event_name="IEEE INFOCOM 2027",
        organizer="IEEE ComSoc",
        start_date="2027-04-18"
    )

    ev2 = EdgeEvent(
        event_name="INFOCOM 2027 Conference on Computer Communications",
        organizer="IEEE",
        start_date="2027-04-18"
    )

    is_dup, match = deduplicator.is_duplicate(ev2, [ev1])
    assert is_dup is True


def test_deduplicator_year_sensitivity():
    deduplicator = EventDeduplicator()

    # SEC 2026 vs SEC 2027 must NOT be considered duplicates
    ev2026 = EdgeEvent(
        event_name="ACM SEC 2026",
        organizer="ACM",
        start_date="2026-11-10"
    )
    ev2027 = EdgeEvent(
        event_name="ACM SEC 2027",
        organizer="ACM",
        start_date="2027-11-15"
    )

    is_dup, _ = deduplicator.is_duplicate(ev2027, [ev2026])
    assert is_dup is False


def test_deduplicator_merges_discounts_and_subsidies():
    deduplicator = EventDeduplicator()

    ev1 = EdgeEvent(
        event_name="HotEdge 2027",
        organizer="USENIX",
        official_website="https://www.usenix.org/conference/hotedge27",
        discounts_subsidies=[
            DiscountOpportunity(discount_type="student_rate", name="Student Pass", amount_or_rate="$150")
        ]
    )

    ev2 = EdgeEvent(
        event_name="HotEdge 2027 Workshop",
        organizer="USENIX",
        official_website="https://www.usenix.org/conference/hotedge27",
        discounts_subsidies=[
            DiscountOpportunity(discount_type="travel_grant", name="USENIX STG", amount_or_rate="$800")
        ]
    )

    deduped = deduplicator.deduplicate([ev1, ev2])
    assert len(deduped) == 1
    merged = deduped[0]
    types = {d.discount_type for d in merged.discounts_subsidies}
    assert "student_rate" in types
    assert "travel_grant" in types
    assert merged.has_student_discount is True
    assert merged.has_travel_grant is True


# =============================================================================
# 4. VERIFICATION TESTS
# =============================================================================

def test_verifier_flags_concluded_events():
    ref_date = datetime.date(2026, 10, 1)
    verifier = EventVerifier(reference_date=ref_date)

    past_event = EdgeEvent(
        event_name="Past Edge Conference 2025",
        organizer="IEEE",
        start_date="2025-05-10",
        end_date="2025-05-12"
    )

    ev, is_active = verifier.verify_event(past_event)
    assert is_active is False
    assert ev.status == EventStatus.CONCLUDED.value


def test_verifier_detects_open_and_closed_cfps():
    ref_date = datetime.date(2026, 10, 1)
    verifier = EventVerifier(reference_date=ref_date)

    # Open CFP: deadline is in future (e.g. 2026-11-15)
    future_cfp = EdgeEvent(
        event_name="Future CFP Conference 2027",
        organizer="ACM",
        start_date="2027-05-01",
        end_date="2027-05-03",
        cfp_deadline="2026-11-15"
    )
    ev_open, is_active1 = verifier.verify_event(future_cfp)
    assert is_active1 is True
    assert ev_open.status == EventStatus.CFP_OPEN.value

    # Closed CFP: deadline is in past (e.g. 2026-08-01)
    past_cfp = EdgeEvent(
        event_name="Registration Open Conference 2026",
        organizer="ACM",
        start_date="2026-11-20",
        end_date="2026-11-22",
        cfp_deadline="2026-08-01"
    )
    ev_closed, is_active2 = verifier.verify_event(past_cfp)
    assert is_active2 is True
    assert ev_closed.status == EventStatus.REGISTRATION_OPEN.value


def test_verifier_filters_active_events():
    ref_date = datetime.date(2026, 10, 1)
    verifier = EventVerifier(reference_date=ref_date)

    past = EdgeEvent(event_name="Past 2024", organizer="ACM", start_date="2024-01-01", end_date="2024-01-02")
    future = EdgeEvent(event_name="Future 2027", organizer="IEEE", start_date="2027-04-18", end_date="2027-04-20")

    active_only = verifier.filter_active([past, future], include_concluded=False)
    assert len(active_only) == 1
    assert active_only[0].event_name == "Future 2027"

    all_events = verifier.filter_active([past, future], include_concluded=True)
    assert len(all_events) == 2


# =============================================================================
# 5. RELEVANCE SCORING TESTS
# =============================================================================

def test_scorer_topic_relevance_and_credibility():
    scorer = EventScorer()

    # Core Edge Conference by ACM / IEEE
    sec_event = EdgeEvent(
        event_name="ACM/IEEE Symposium on Edge Computing (SEC 2026)",
        organizer="ACM / IEEE Computer Society",
        description="Top forum for edge computing, edge intelligence, and device-edge systems.",
        topics=["Edge Computing", "Edge AI", "Cloudlets"],
        start_date="2026-11-10",
        end_date="2026-11-12",
        has_student_discount=True,
        has_travel_grant=True
    )

    breakdown = scorer.score_event(sec_event)
    assert breakdown.final_score >= 8.0
    assert breakdown.topic_score >= 3.0
    assert breakdown.credibility_score == 2.5
    assert breakdown.affordability_boost >= 1.0
    assert "Edge Computing" in breakdown.matched_topics


def test_scorer_penalizes_negative_keywords_and_concluded_events():
    scorer = EventScorer()

    # Crypto / spam event
    spam_event = EdgeEvent(
        event_name="Crypto & NFT Edge Web Development Bootcamp",
        organizer="Anonymous",
        description="Learn bitcoin trading and react js web development bootcamp.",
        topics=["Crypto", "Web Development"]
    )
    breakdown_spam = scorer.score_event(spam_event)
    assert breakdown_spam.negative_penalty < 0
    assert breakdown_spam.final_score < 4.0

    # Concluded event
    concluded_event = EdgeEvent(
        event_name="Edge Computing Workshop 2024",
        organizer="IEEE",
        status=EventStatus.CONCLUDED.value,
        topics=["Edge Computing"]
    )
    breakdown_concluded = scorer.score_event(concluded_event)
    assert breakdown_concluded.negative_penalty <= -4.0


def test_scorer_affordability_boost():
    scorer = EventScorer()

    free_webinar = EdgeEvent(
        event_name="LF Edge Technical Webinar on Akraino",
        organizer="The Linux Foundation",
        fee_status=FeeStatus.FREE.value,
        topics=["Edge Computing", "Akraino"]
    )
    breakdown_free = scorer.score_event(free_webinar)
    assert breakdown_free.affordability_boost >= 1.0


# =============================================================================
# 6. COLLECTOR & PIPELINE INTEGRATION TESTS
# =============================================================================

def test_collector_loads_curated_events():
    collector = EdgeEventCollector()
    events = collector.fetch_events()

    # Must find all 14 curated events from events.yaml
    assert len(events) >= 10
    event_names = [e.event_name for e in events]
    assert any("SEC" in name for name in event_names)
    assert any("INFOCOM" in name for name in event_names)
    assert any("KubeCon" in name for name in event_names)
    assert any("TinyML" in name for name in event_names)
    assert any("Webinar" in name for name in event_names)


def test_events_pipeline_end_to_end_and_state_persistence(tmp_path):
    pipeline = EdgeEventsPipeline()
    # Configure temporary state files
    pipeline.state_manager = EventsStateManager(data_dir=tmp_path)

    result = pipeline.run(min_score=6.5, dry_run=False)

    assert result["total_collected"] >= 10
    assert result["unique_events"] >= 10
    assert result["qualified_events"] >= 5
    assert len(result["events"]) == result["qualified_events"]

    # Verify atomic state was written to disk
    events_file = tmp_path / "events.json"
    seen_file = tmp_path / "seen_events.json"
    history_file = tmp_path / "events_history.json"

    assert events_file.exists()
    assert seen_file.exists()
    assert history_file.exists()

    loaded = pipeline.state_manager.load_events()
    assert len(loaded) == result["qualified_events"]

    # Test Markdown summary generation
    md_summary = pipeline.render_markdown_summary(result["events"])
    assert "# Edge Computing Events" in md_summary
    assert "Academic Conference" in md_summary or "Symposium" in md_summary
