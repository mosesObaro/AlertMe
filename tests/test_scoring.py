"""Tests for transparent relevance scoring and PhD preparation alignment."""

import datetime
import pytest
from src.models import ResearchItem, ItemType, CredibilityTier
from src.ranking.scorer import RelevanceScorer
from src.utils.config_loader import ConfigManager


@pytest.fixture
def scorer():
    return RelevanceScorer()


def test_score_critical_edge_ai_paper(scorer):
    """Test Score 9-10: Adaptive Computation Offloading for Edge AI in 6G Networks."""
    today_str = datetime.date.today().isoformat()
    item = ResearchItem(
        title="Adaptive Computation Offloading for Edge AI in 6G Networks",
        url="https://ieeexplore.ieee.org/document/123456",
        source="IEEE Transactions on Mobile Computing",
        source_tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value,
        item_type=ItemType.PAPER.value,
        abstract="We formulate an energy-efficient computation offloading algorithm for mobile edge computing under stochastic wireless channels.",
        publication_date=today_str,
        venue="IEEE TMC"
    )

    breakdown = scorer.score_item(item)
    assert breakdown.final_score >= 8.5
    assert any("Primary topic match" in r for r in breakdown.reasons)
    assert any("Tier 1 Academic" in r for r in breakdown.reasons)
    assert breakdown.recency_score >= 1.0


def test_score_medium_relevance_kubernetes_paper(scorer):
    """Test Score 5-6: Kubernetes Scheduling Optimization (Secondary topic without strong edge context)."""
    item = ResearchItem(
        title="Kubernetes Scheduling Optimization in Cloud Clusters",
        url="https://example.com/k8s",
        source="Journal of Cloud Computing",
        source_tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value,
        item_type=ItemType.PAPER.value,
        abstract="We evaluate container placement policies across data center servers.",
        publication_date="2026-07-01"
    )

    breakdown = scorer.score_item(item)
    assert 4.0 <= breakdown.final_score <= 7.0
    assert any("Secondary topic match" in r for r in breakdown.reasons)


def test_score_low_relevance_generic_article_filtered(scorer):
    """Test Score 0-3: 10 Best AI Tools for Developers (Negative keyword penalty)."""
    item = ResearchItem(
        title="10 Best AI Tools for Developers in 2026",
        url="https://medium.com/generic-ai",
        source="Medium",
        source_tier=CredibilityTier.UNKNOWN.value,
        item_type=ItemType.TECH_REPORT.value,
        abstract="A quick look at modern developer plugins and web development tools."
    )

    breakdown = scorer.score_item(item)
    assert breakdown.final_score < 4.0
    assert breakdown.negative_penalty < 0
    assert any("negative keyword" in r.lower() or "generic" in r.lower() for r in breakdown.reasons)


def test_learning_stage_boost(scorer):
    """Test that items matching current learning stage receive an explicit boost."""
    today_str = datetime.date.today().isoformat()
    item = ResearchItem(
        title="Dynamic Computation Offloading and Distributed Inference in Edge Networks",
        url="https://arxiv.org/abs/2608.9999",
        source="arXiv",
        source_tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value,
        publication_date=today_str,
        abstract="We optimize distributed inference latencies on edge nodes."
    )

    breakdown = scorer.score_item(item)
    assert breakdown.stage_boost > 0
    assert any("learning stage" in r.lower() for r in breakdown.reasons)


def test_phd_opportunity_boost(scorer):
    """Test that PhD studentships receive the PhD boost."""
    item = ResearchItem(
        title="Fully Funded PhD Position in Edge AI & Distributed Systems",
        url="https://www.jobs.ac.uk/phd-edge",
        source="Academic Positions",
        source_tier=CredibilityTier.TIER2_UNIVERSITY_LAB.value,
        item_type=ItemType.PHD_OPPORTUNITY.value,
        abstract="Fully funded PhD position in mobile edge intelligence."
    )

    breakdown = scorer.score_item(item)
    assert breakdown.phd_boost > 0
    assert any("PhD / Fellowship Opportunity" in r for r in breakdown.reasons)


def test_acronym_word_boundary_avoids_substring_collision(scorer):
    """Test that short acronyms like MEC do not trigger on words like mechanism or mechanical."""
    item = ResearchItem(
        title="Biochemical Mechanisms of Cell Division",
        url="https://example.com/bio",
        source="Biology Journal",
        abstract="We analyze the enzymatic mechanism of cell regeneration."
    )
    breakdown = scorer.score_item(item)
    assert "MEC (Title)" not in breakdown.reasons
    assert "MEC (Abstract)" not in breakdown.reasons
    assert breakdown.topic_score == 0.0
