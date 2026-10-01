"""Tests for email rendering and delivery dispatchers."""

import pytest
from src.models import ResearchItem, ItemType, ScoreBreakdown, PaperIntelligence
from src.email.renderer import EmailRenderer
from src.email.sender import EmailSender


@pytest.fixture
def sample_items():
    p1 = ResearchItem(
        title="Adaptive Computation Offloading for Edge AI in 6G Networks",
        url="https://ieeexplore.ieee.org/document/1001",
        source="IEEE TMC",
        item_type=ItemType.PAPER.value,
        authors=["J. Zhang", "L. Wang"],
        publication_date="2026-08-24",
        abstract="We optimize computation offloading for edge AI inference in 6G systems.",
        venue="IEEE TMC"
    )
    p1.score = ScoreBreakdown(
        final_score=9.5,
        reasons=["Primary topic: Edge AI", "Tier 1 IEEE source", "Aligned with learning stage"]
    )
    p1.intelligence = PaperIntelligence(
        why_it_matters="Critical for sub-10ms edge AI task offloading.",
        research_problem="Minimizing offloading latency under channel fading.",
        methodology="Lyapunov stochastic queue optimization.",
        key_contribution="Reduces average latency by 32%.",
        potential_gap="Requires evaluation under heterogeneous multi-tenant edge nodes."
    )

    opp = ResearchItem(
        title="Fully Funded PhD Studentship in Edge AI & Distributed Systems",
        url="https://jobs.ac.uk/phd-edge",
        source="University Lab",
        item_type=ItemType.PHD_OPPORTUNITY.value,
        abstract="3.5 year funded position in federated learning and edge computing.",
        institution="TU Wien"
    )
    opp.score = ScoreBreakdown(final_score=9.2, reasons=["PhD position in core topic"])

    conf = ResearchItem(
        title="[SEC 2026] ACM/IEEE Symposium on Edge Computing — CFP",
        url="https://acm-ieee-sec.org",
        source="ACM/IEEE",
        item_type=ItemType.CONFERENCE_CFP.value,
        deadline="2026-09-15",
        venue="ACM SEC 2026",
        abstract="Call for papers in edge architectures, edge intelligence, and edge security."
    )
    conf.score = ScoreBreakdown(final_score=8.8, reasons=["Premier Edge Computing Conference"])

    return [p1, opp, conf]


def test_render_daily_digest(sample_items):
    renderer = EmailRenderer()
    subject, html, text = renderer.render_daily_digest(sample_items)

    assert "[Edge PhD Alert]" in subject
    assert "Adaptive Computation Offloading" in html
    assert "9.5/10" in html
    assert "Why it matters:" in html
    assert "Adaptive Computation Offloading" in text


def test_render_weekly_digest(sample_items):
    renderer = EmailRenderer()
    trends = [{"topic": "Edge AI", "direction": "↑↑", "status": "Surging", "recent_count": 10}]
    supervisors = [{"name": "Mahadev Satyanarayanan", "institution": "CMU", "publication_count": 4, "average_relevance": 9.2}]
    study_guide = {
        "focus_topic": "Computation Offloading",
        "concept": "Lyapunov Optimization for MEC",
        "paper_title": "Adaptive Computation Offloading for Edge AI in 6G Networks",
        "paper_url": "https://ieeexplore.ieee.org/document/1001",
        "practical_exercise": "Simulate 2-node offloading in Python",
        "research_question": "How to guarantee sub-10ms latency?",
        "event_opportunity": {"title": "ACM SEC 2026", "url": "https://acm-ieee-sec.org", "type": "CFP"}
    }

    subject, html, text = renderer.render_weekly_digest(
        sample_items, trends, supervisors, study_guide
    )

    assert "[Edge PhD Weekly Briefing]" in subject
    assert "Recommended Focus for Next Week" in html
    assert "Lyapunov Optimization for MEC" in html
    assert "Emerging Research Trends" in html
    assert "Mahadev Satyanarayanan" in html


def test_render_urgent_alert(sample_items):
    renderer = EmailRenderer()
    subject, html, text = renderer.render_urgent_alert(sample_items[0])
    assert "🚨 [URGENT PhD ALERT]" in subject
    assert "Adaptive Computation Offloading" in html


def test_email_sender_console_dry_run():
    sender = EmailSender({"provider": "console", "recipient_email": "test@example.com"})
    success = sender.send(
        subject="Test Subject",
        html_body="<p>Test HTML</p>",
        text_body="Test Text"
    )
    assert success is True


@pytest.fixture
def sample_event():
    from src.events.models import EdgeEvent, EventType, EventFormat, FeeStatus, DiscountOpportunity, DiscountType
    return EdgeEvent(
        event_name="IEEE International Conference on Edge Computing (EDGE 2026)",
        organizer="IEEE Computer Society",
        event_type=EventType.ACADEMIC_CONFERENCE.value,
        description="Premier academic forum on edge architectures and distributed edge AI systems.",
        topics=["Edge Computing", "Edge AI", "Distributed Systems"],
        start_date="2026-07-06",
        end_date="2026-07-10",
        location="Chicago, IL, USA",
        format=EventFormat.HYBRID.value,
        official_website="https://conferences.computer.org/edge/2026/",
        registration_fee="$550 (Student: $250)",
        fee_status=FeeStatus.PAID.value,
        discounts_subsidies=[
            DiscountOpportunity(
                name="IEEE TCPP Student Travel Grant",
                discount_type=DiscountType.TRAVEL_GRANT.value,
                amount_or_rate="Up to $1,000 USD",
                eligibility="Full-time PhD students"
            ),
            DiscountOpportunity(
                name="Early Bird Student Registration",
                discount_type=DiscountType.STUDENT_RATE.value,
                amount_or_rate="$250 USD",
                eligibility="Active IEEE student members"
            )
        ],
        has_student_discount=True,
        has_travel_grant=True,
        cfp_deadline="2026-03-15",
        relevance_score=9.3
    )


def test_render_daily_digest_with_events(sample_items, sample_event):
    renderer = EmailRenderer()
    subject, html, text = renderer.render_daily_digest(
        items=sample_items,
        events=[sample_event]
    )

    assert "Edge Computing Events & Opportunities" in html
    assert "IEEE International Conference on Edge Computing" in html
    assert "IEEE Computer Society" in html
    assert "Chicago, IL, USA" in html
    assert "2026-03-15" in html
    assert "Student Travel Grant" in html
    assert "Student Rate Available" in html
    assert "Up to $1,000 USD" in html

    # Text digest assertions
    assert "EDGE COMPUTING EVENTS & OPPORTUNITIES" in text
    assert "IEEE International Conference on Edge Computing" in text
    assert "CFP Deadline: 2026-03-15" in text
    assert "[STUDENT TRAVEL GRANT AVAILABLE]" in text
    assert "https://conferences.computer.org/edge/2026/" in text


def test_render_daily_digest_extracted_from_items(sample_items, sample_event):
    renderer = EmailRenderer()
    event_item = sample_event.to_research_item()
    items_with_event = sample_items + [event_item]

    subject, html, text = renderer.render_daily_digest(items=items_with_event)

    assert "Edge Computing Events & Opportunities" in html
    assert "IEEE International Conference on Edge Computing" in html
    assert "EDGE COMPUTING EVENTS & OPPORTUNITIES" in text


def test_render_weekly_digest_with_events(sample_items, sample_event):
    renderer = EmailRenderer()
    trends = [{"topic": "Edge AI", "direction": "↑↑", "status": "Surging", "recent_count": 10}]
    supervisors = [{"name": "Mahadev Satyanarayanan", "institution": "CMU", "publication_count": 4, "average_relevance": 9.2}]
    study_guide = {
        "focus_topic": "Computation Offloading",
        "concept": "Lyapunov Optimization for MEC",
        "paper_title": "Adaptive Computation Offloading for Edge AI in 6G Networks",
        "paper_url": "https://ieeexplore.ieee.org/document/1001",
        "practical_exercise": "Simulate 2-node offloading in Python",
        "research_question": "How to guarantee sub-10ms latency?",
        "event_opportunity": {"title": "ACM SEC 2026", "url": "https://acm-ieee-sec.org", "type": "CFP"}
    }

    subject, html, text = renderer.render_weekly_digest(
        items=sample_items,
        trends=trends,
        supervisors=supervisors,
        study_guide=study_guide,
        events=[sample_event]
    )

    assert "Edge Computing Events & Academic/Industrial Opportunities" in html
    assert "IEEE International Conference on Edge Computing" in html
    assert "UPCOMING EDGE COMPUTING EVENTS & WORKSHOPS" in text
    assert "IEEE International Conference on Edge Computing" in text
