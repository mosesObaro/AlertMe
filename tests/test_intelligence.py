"""Tests for paper intelligence, trend detection, supervisor tracking, and study guide."""

import pytest
from src.models import ResearchItem, ItemType
from src.summarization.intelligence import IntelligenceEngine
from src.summarization.trends import TrendDetector
from src.summarization.supervisors import SupervisorTracker
from src.summarization.study_guide import StudyGuideGenerator


def test_deterministic_paper_intelligence():
    engine = IntelligenceEngine({"enabled": False})
    item = ResearchItem(
        title="Adaptive Computation Offloading in Heterogeneous Edge Computing",
        url="https://example.com/paper",
        source="IEEE Transactions",
        abstract="However, minimizing latency under stochastic network conditions remains a key bottleneck. We propose a Lyapunov optimization framework. Simulation results show that our approach reduces offloading latency by 28% compared to state-of-the-art baselines.",
        topics=["Computation Offloading", "Edge AI"]
    )

    intel = engine.analyze(item)
    assert intel is not None
    assert "bottleneck" in intel.research_problem.lower() or "challenge" in intel.research_problem.lower() or intel.research_problem != ""
    assert "lyapunov" in intel.methodology.lower() or "propose" in intel.methodology.lower()
    assert "potential research direction" in intel.potential_gap.lower()
    assert not intel.is_ai_generated


def test_trend_detector():
    detector = TrendDetector(monitored_topics=["Edge AI", "Federated Learning", "6G + Edge"])
    items = [
        ResearchItem(title="Edge AI Offloading", url="http://a.com", source="arXiv", abstract="Edge AI systems."),
        ResearchItem(title="Edge AI Inference", url="http://b.com", source="arXiv", abstract="Edge AI latency."),
        ResearchItem(title="Edge AI Models", url="http://c.com", source="arXiv", abstract="Edge AI compression.")
    ]

    trends = detector.detect_trends(items, history_items=[])
    assert len(trends) == 3
    edge_ai_trend = next(t for t in trends if t["topic"] == "Edge AI")
    assert edge_ai_trend["recent_count"] >= 3
    assert edge_ai_trend["direction"] in ["↑↑", "↑"]


def test_supervisor_tracker():
    tracker = SupervisorTracker()
    from src.models import ScoreBreakdown

    item1 = ResearchItem(
        title="Paper 1 on Edge Cloudlets",
        url="http://a.com",
        source="IEEE",
        authors=["Mahadev Satyanarayanan", "Co-author A"],
        topics=["Cloudlets", "Edge Computing"],
        institution="Carnegie Mellon University"
    )
    item1.score = ScoreBreakdown(final_score=9.0)

    item2 = ResearchItem(
        title="Paper 2 on Wearable Cognitive Assistance",
        url="http://b.com",
        source="ACM",
        authors=["Mahadev Satyanarayanan", "Co-author B"],
        topics=["Cloudlets", "Edge AI"],
        institution="Carnegie Mellon University"
    )
    item2.score = ScoreBreakdown(final_score=9.4)

    registry = tracker.update_and_extract_supervisors([item1, item2])
    assert "Mahadev Satyanarayanan" in registry
    satya = registry["Mahadev Satyanarayanan"]
    assert satya["publication_count"] == 2
    assert satya["average_relevance"] >= 9.0

    top_sups = tracker.get_top_supervisors_to_watch(registry, min_publications=2)
    assert len(top_sups) == 1
    assert top_sups[0]["name"] == "Mahadev Satyanarayanan"


def test_study_guide_generator():
    gen = StudyGuideGenerator()
    paper = ResearchItem(
        title="Task Scheduling in Multi-access Edge Computing",
        url="https://arxiv.org/abs/2608.1234",
        source="arXiv"
    )
    plan = gen.generate_focus_plan(top_papers=[paper], conferences=[], opportunities=[])
    assert plan["focus_topic"] is not None
    assert plan["concept"] != ""
    assert plan["paper_title"] == "Task Scheduling in Multi-access Edge Computing"
    assert plan["practical_exercise"] != ""
    assert plan["research_question"] != ""
