"""Comprehensive unit and integration test suite for the ML/Embedded/IoT Events module.
Tests cover:
1. Domain models & research item bridging
2. Normalization & event type / format inference
3. Discount, travel grant, scholarship & fee waiver detection
4. Predatory & suspicious conference filtering
5. Deduplication across URLs, fuzzy titles & acronyms (NeurIPS, SenSys, IPSN, RTSS, etc.)
6. Verification of dates & open/closed CFP detection
7. Transparent 0-10 multi-factor relevance scoring for ML/Embedded/IoT
8. State management & historical persistence
9. MLEmbeddedIoTEventCollector & MLEmbeddedIoTEventsPipeline
10. Daily & weekly email digest rendering & domain badge integration
"""

import datetime
from pathlib import Path
import pytest

from src.events.models import (
    EdgeEvent,
    MLEmbeddedIoTEvent,
    EventItem,
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
from src.events.collector import (
    ConfigurableEventCollector,
    EdgeEventCollector,
    MLEmbeddedIoTEventCollector
)
from src.events.state_manager import EventsStateManager, MLEventsStateManager
from src.events.pipeline import (
    EventsPipeline,
    EdgeEventsPipeline,
    MLEmbeddedIoTEventsPipeline
)
from src.models import ItemType, CredibilityTier
from src.email.renderer import EmailRenderer
from src.utils.config_loader import ConfigManager


# =============================================================================
# 1. MODEL & RESEARCH ITEM BRIDGE TESTS
# =============================================================================

def test_ml_iot_event_model_creation_and_domain():
    discount = DiscountOpportunity(
        discount_type=DiscountType.TRAVEL_GRANT.value,
        name="NeurIPS Student Travel Award",
        amount_or_rate="Up to $1,500 travel and accommodation stipend",
        eligibility="Enrolled graduate students and student authors"
    )
    event = MLEmbeddedIoTEvent(
        event_name="NeurIPS 2026 (Conference on Neural Information Processing Systems)",
        organizer="Neural Information Processing Systems Foundation",
        event_type=EventType.ACADEMIC_CONFERENCE.value,
        description="Premier flagship conference on Machine Learning and Deep Learning systems.",
        topics=["Machine Learning", "Deep Learning", "AI Systems", "Computer Vision"],
        start_date="2026-12-06",
        end_date="2026-12-12",
        location="Sydney, Australia",
        format=EventFormat.HYBRID.value,
        official_website="https://neurips.cc/Conferences/2026",
        domain="ml_embedded_iot",
        discounts_subsidies=[discount],
        cfp_deadline="2026-05-22"
    )

    assert event.domain == "ml_embedded_iot"
    assert event.has_travel_grant is True
    assert event.id.startswith("evt_")

    # Serialization roundtrip
    d = event.to_dict()
    assert d["domain"] == "ml_embedded_iot"
    assert len(d["discounts_subsidies"]) == 1

    rebuilt = MLEmbeddedIoTEvent.from_dict(d)
    assert rebuilt.domain == "ml_embedded_iot"
    assert rebuilt.event_name == event.event_name
    assert rebuilt.has_travel_grant is True


def test_ml_iot_to_research_item_bridge():
    event = MLEmbeddedIoTEvent(
        event_name="ACM SenSys 2026",
        organizer="ACM SIGMOBILE / SIGBED",
        event_type=EventType.ACADEMIC_CONFERENCE.value,
        description="Conference on Embedded Networked Sensor Systems and Intelligent IoT.",
        topics=["Internet of Things", "Sensor Networks", "Embedded Systems", "Intelligent IoT"],
        start_date="2026-11-09",
        end_date="2026-11-12",
        location="Hong Kong, China",
        format=EventFormat.HYBRID.value,
        official_website="https://sensys.acm.org/2026/",
        registration_fee="$320 (Student) / $720 (Regular)",
        fee_status=FeeStatus.PAID.value,
        domain="ml_embedded_iot",
        has_student_discount=True,
        has_travel_grant=True,
        cfp_deadline="2026-06-10"
    )

    research_item = event.to_research_item()
    assert research_item.title == "ACM SenSys 2026"
    assert research_item.item_type == ItemType.CONFERENCE_CFP.value
    assert research_item.source_tier == CredibilityTier.TIER1_ACADEMIC_STANDARDS.value
    assert "Internet of Things" in research_item.topics
    assert research_item.opportunity_data is not None
    assert research_item.opportunity_data["kind"] == "event"
    assert research_item.opportunity_data["domain"] == "ml_embedded_iot"
    assert research_item.opportunity_data["has_travel_grant"] is True


# =============================================================================
# 2. NORMALIZER TESTS FOR ML / EMBEDDED / IOT
# =============================================================================

def test_normalizer_infers_ml_iot_types_and_formats():
    normalizer = EventNormalizer()

    # Summer School inference
    raw_school = {
        "event_name": "Oxford Machine Learning Summer School (OxML 2027)",
        "organizer": "University of Oxford",
        "description": "Intensive doctoral summer school on deep learning theory and computer vision.",
        "location": "Oxford, UK",
        "format": "hybrid",
        "start_date": "2027-07-05",
        "end_date": "2027-07-16"
    }
    ev_school = normalizer.normalize(raw_school)
    assert ev_school.event_type == EventType.SUMMER_SCHOOL.value
    assert ev_school.format == EventFormat.HYBRID.value

    # Bootcamp inference
    raw_bootcamp = {
        "event_name": "Arm & Edge Impulse Embedded AI Hands-on Bootcamp",
        "organizer": "Arm Ltd. & Edge Impulse",
        "description": "Virtual hands-on bootcamp on microcontrollers and TinyML.",
        "location": "Online",
        "registration_fee": "Free"
    }
    ev_bootcamp = normalizer.normalize(raw_bootcamp)
    assert ev_bootcamp.event_type == EventType.BOOTCAMP.value
    assert ev_bootcamp.format == EventFormat.ONLINE.value
    assert ev_bootcamp.fee_status == FeeStatus.FREE.value

    # Webinar inference
    raw_webinar = {
        "event_name": "tinyML Talks Technical Webinar Series",
        "organizer": "TinyML Foundation",
        "description": "Bi-weekly distinguished lecture webinar series on low-power ML.",
        "location": "Zoom"
    }
    ev_webinar = normalizer.normalize(raw_webinar)
    assert ev_webinar.event_type == EventType.WEBINAR.value
    assert ev_webinar.format == EventFormat.ONLINE.value


def test_normalizer_extracts_discounts_and_subsidies_from_text():
    normalizer = EventNormalizer()

    raw_event = {
        "event_name": "International IoT & Cyber-Physical Systems Summit 2027",
        "organizer": "IEEE",
        "description": (
            "Leading event on IoT networks. Subsidized student registration rate of $150 available. "
            "Authors can apply for the NSF student travel grant providing $1000 stipend. "
            "Early-bird advance registration ends April 1. Free virtual attendee passes offered."
        ),
        "registration_fee": "$500"
    }
    ev = normalizer.normalize(raw_event)
    assert ev.has_student_discount is True
    assert ev.has_travel_grant is True
    assert ev.has_early_bird is True
    assert ev.has_fee_waiver is True
    assert len(ev.discounts_subsidies) >= 3


# =============================================================================
# 3. PREDATORY & SPAM FILTERING TESTS
# =============================================================================

def test_verifier_filters_predatory_conferences():
    verifier = EventVerifier()

    # WASET predatory conference
    waset_event = MLEmbeddedIoTEvent(
        event_name="International Conference on Machine Learning and IoT (ICMLIOT 2026)",
        organizer="WASET",
        description="Global gathering on machine learning and sensor networks.",
        official_website="https://waset.org/icmliot-2026"
    )
    ev_waset, is_active1 = verifier.verify_event(waset_event)
    assert is_active1 is False
    assert ev_waset.status == EventStatus.CANCELLED.value

    # Suspicious "review in 24 hours guaranteed acceptance"
    fake_event = MLEmbeddedIoTEvent(
        event_name="Global Summit on Embedded AI & IoT",
        organizer="Unknown Publisher",
        description="Publish your paper fast! Guaranteed acceptance with review in 24 hours.",
        official_website="https://fakeconf.com"
    )
    ev_fake, is_active2 = verifier.verify_event(fake_event)
    assert is_active2 is False
    assert ev_fake.status == EventStatus.CANCELLED.value


def test_scorer_heavily_penalizes_predatory_and_cancelled_events():
    scorer = EventScorer(domain="ml_iot")

    predatory_event = MLEmbeddedIoTEvent(
        event_name="OMICS International Summit on Deep Learning & Embedded Systems",
        organizer="OMICS Group",
        description="Conference on machine learning and IoT with instant acceptance certificate.",
        status=EventStatus.CANCELLED.value
    )
    breakdown = scorer.score_event(predatory_event)
    assert breakdown.negative_penalty <= -5.0
    assert breakdown.final_score <= 2.0


# =============================================================================
# 4. DEDUPLICATION & ACRONYM RECOGNITION TESTS
# =============================================================================

def test_deduplicator_recognizes_ml_iot_acronyms():
    deduplicator = EventDeduplicator()

    # NeurIPS acronym matching across naming variations
    ev1 = MLEmbeddedIoTEvent(
        event_name="38th Annual Conference on Neural Information Processing Systems (NeurIPS 2026)",
        organizer="NeurIPS Foundation",
        start_date="2026-12-06",
        official_website="https://neurips.cc/2026"
    )
    ev2 = MLEmbeddedIoTEvent(
        event_name="NeurIPS 2026 Call For Papers",
        organizer="NeurIPS",
        start_date="2026-12-06",
        source_url="https://wikicfp.com/cfp/servlet/event.showcfp?eventid=1234"
    )

    is_dup, match = deduplicator.is_duplicate(ev2, [ev1])
    assert is_dup is True
    assert match is ev1


def test_deduplicator_merges_ml_iot_metadata():
    deduplicator = EventDeduplicator()

    base_event = MLEmbeddedIoTEvent(
        event_name="ACM SenSys 2026",
        organizer="ACM",
        description="Sensor systems conference.",
        start_date="2026-11-09",
        official_website="https://sensys.acm.org/2026/"
    )
    incoming_event = MLEmbeddedIoTEvent(
        event_name="ACM SenSys 2026",
        organizer="ACM SIGBED",
        description="Longer description detailing Intelligent IoT and Cyber-Physical perception.",
        start_date="2026-11-09",
        end_date="2026-11-12",
        cfp_deadline="2026-06-10",
        discounts_subsidies=[
            DiscountOpportunity(discount_type="travel_grant", name="SIGBED STG", amount_or_rate="$1,200")
        ]
    )

    deduped = deduplicator.deduplicate([base_event, incoming_event])
    assert len(deduped) == 1
    merged = deduped[0]
    assert merged.end_date == "2026-11-12"
    assert merged.cfp_deadline == "2026-06-10"
    assert merged.has_travel_grant is True
    assert len(merged.description) > 30


# =============================================================================
# 5. RELEVANCE SCORING FOR ML / EMBEDDED / IOT
# =============================================================================

def test_scorer_scores_high_for_top_ml_iot_venues():
    config_mgr = ConfigManager()
    scorer = EventScorer(config_manager=config_mgr, domain="ml_iot")

    # Top ML conference: NeurIPS 2026
    neurips = MLEmbeddedIoTEvent(
        event_name="NeurIPS 2026 (Conference on Neural Information Processing Systems)",
        organizer="Neural Information Processing Systems Foundation",
        description="Flagship international conference on Machine Learning, Deep Learning, and AI Systems.",
        topics=["Machine Learning", "Deep Learning", "AI Systems", "Computer Vision"],
        start_date="2026-12-06",
        end_date="2026-12-12",
        official_website="https://neurips.cc",
        registration_fee="$250 (Student)",
        has_student_discount=True,
        has_travel_grant=True,
        has_scholarship=True,
        cfp_deadline="2026-05-22"
    )
    b_neurips = scorer.score_event(neurips)
    assert b_neurips.final_score >= 8.5
    assert b_neurips.topic_score >= 3.0
    assert b_neurips.credibility_score >= 2.0
    assert b_neurips.affordability_boost >= 1.0

    # Embedded Systems venue: Embedded World 2027
    ew = MLEmbeddedIoTEvent(
        event_name="Embedded World 2027 (Exhibition & Conference)",
        organizer="NürnbergMesse / WEKA",
        description="World leading conference for embedded systems, IoT hardware, and microcontrollers.",
        topics=["Embedded Systems", "Internet of Things", "Microcontrollers", "Hardware Acceleration"],
        start_date="2027-03-09",
        end_date="2027-03-11",
        official_website="https://www.embedded-world.de/en",
        fee_status=FeeStatus.HYBRID_FREE.value,
        has_student_discount=True,
        has_fee_waiver=True
    )
    b_ew = scorer.score_event(ew)
    assert b_ew.final_score >= 7.0
    assert b_ew.topic_score >= 2.5
    assert b_ew.affordability_boost >= 1.0


def test_scorer_scores_tiny_ml_and_summer_schools():
    config_mgr = ConfigManager()
    scorer = EventScorer(config_manager=config_mgr, domain="ml_iot")

    oxml = MLEmbeddedIoTEvent(
        event_name="Oxford Machine Learning Summer School (OxML 2027)",
        organizer="University of Oxford",
        event_type=EventType.SUMMER_SCHOOL.value,
        description="Intensive doctoral training on Machine Learning, Deep Learning, and AI theory.",
        topics=["Machine Learning", "Deep Learning", "AI Systems"],
        start_date="2027-07-05",
        end_date="2027-07-16",
        has_student_discount=True,
        has_scholarship=True
    )
    b_oxml = scorer.score_event(oxml)
    assert b_oxml.final_score >= 7.0
    assert b_oxml.phd_value_boost >= 0.7  # Doctoral training boost


# =============================================================================
# 6. STATE MANAGEMENT FOR ML / IOT
# =============================================================================

def test_ml_events_state_manager_persistence(tmp_path):
    state_mgr = MLEventsStateManager(data_dir=tmp_path)

    event = MLEmbeddedIoTEvent(
        event_name="ACM/IEEE IPSN 2027",
        organizer="ACM / IEEE",
        start_date="2027-05-10",
        domain="ml_embedded_iot",
        relevance_score=8.5
    )

    # Save and reload
    state_mgr.save_events([event])
    loaded = state_mgr.load_events()
    assert len(loaded) == 1
    assert loaded[0].event_name == "ACM/IEEE IPSN 2027"
    assert loaded[0].domain == "ml_embedded_iot"

    # Seen tracking
    state_mgr.record_seen_events([event])
    seen_ids = state_mgr.load_seen_event_ids()
    assert event.id in seen_ids

    # History tracking
    state_mgr.record_history([event])
    history = state_mgr.load_history()
    assert len(history) == 1
    assert history[0]["event_name"] == "ACM/IEEE IPSN 2027"


# =============================================================================
# 7. COLLECTOR & PIPELINE INTEGRATION
# =============================================================================

def test_ml_embedded_iot_collector_fetches_curated_events():
    config_mgr = ConfigManager()
    collector = MLEmbeddedIoTEventCollector(config_manager=config_mgr)

    events = collector.fetch_events()
    assert len(events) >= 10

    names = [e.event_name for e in events]
    assert any("NeurIPS" in n for n in names)
    assert any("SenSys" in n for n in names)
    assert any("IPSN" in n for n in names)
    assert any("Embedded World" in n for n in names)
    assert any("tinyML" in n for n in names)

    # All should have domain tag set
    for ev in events:
        assert ev.domain == "ml_embedded_iot"
        assert ev.relevance_score > 0.0

    # BaseCollector fetch() bridge
    research_items = collector.fetch()
    assert len(research_items) == len(events)
    for item in research_items:
        assert item.opportunity_data["kind"] == "event"
        assert item.opportunity_data["domain"] == "ml_embedded_iot"


def test_ml_embedded_iot_events_pipeline_execution():
    config_mgr = ConfigManager()
    pipeline = MLEmbeddedIoTEventsPipeline(config_manager=config_mgr)

    res = pipeline.run(min_score=6.5, dry_run=True, send_email=False)
    assert res["total_collected"] >= 10
    assert res["unique_events"] >= 10
    assert res["active_events"] >= 10
    assert res["qualified_events"] >= 8

    # Markdown summary rendering
    md = pipeline.render_markdown_summary(res["events"])
    assert "ML, Embedded Systems & IoT Events & Opportunities" in md
    assert "Academic Conference" in md
    assert "NeurIPS" in md or "SenSys" in md


# =============================================================================
# 8. EMAIL RENDERER & DAILY DIGEST INTEGRATION
# =============================================================================

def test_daily_digest_renders_edge_and_ml_iot_events_with_badges():
    renderer = EmailRenderer()

    edge_ev = EdgeEvent(
        event_name="ACM/IEEE SEC 2026",
        organizer="ACM / IEEE",
        event_type="academic_conference",
        format="hybrid",
        location="Seattle, WA",
        official_website="https://acm-ieee-sec.org/2026/",
        relevance_score=8.9,
        domain="edge_computing",
        topics=["Edge Computing", "Edge AI"],
        has_student_discount=True,
        has_travel_grant=True,
        description="Top forum for edge computing systems."
    )

    ml_ev = MLEmbeddedIoTEvent(
        event_name="NeurIPS 2026",
        organizer="NeurIPS Foundation",
        event_type="academic_conference",
        format="hybrid",
        location="Sydney, Australia",
        official_website="https://neurips.cc/2026",
        relevance_score=9.1,
        domain="ml_embedded_iot",
        topics=["Machine Learning", "Deep Learning", "AI Systems"],
        has_student_discount=True,
        has_travel_grant=True,
        description="Premier flagship Machine Learning conference."
    )

    subject, html_content, text_content = renderer.render_daily_digest(
        items=[],
        opportunities=[],
        scholarships=[],
        events=[edge_ev, ml_ev]
    )

    # 1. Check updated section headers
    assert "Edge Computing Events & Opportunities" in html_content
    assert "EDGE COMPUTING EVENTS & OPPORTUNITIES" in text_content

    # 2. Check event cards
    assert "ACM/IEEE SEC 2026" in html_content
    assert "NeurIPS 2026" in html_content
    assert "ACM/IEEE SEC 2026" in text_content
    assert "NeurIPS 2026" in text_content

    # 3. Check domain badges rendered
    assert "🤖 ML / Embedded / IoT" in html_content
    assert "⚡ Edge Systems" in html_content
