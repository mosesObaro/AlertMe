"""Unit tests for OpportunityScorer, recruitment classification, and dependant scoring."""

import pytest
from src.models import (
    PhDOpportunity,
    Scholarship,
    ResearcherProfile,
    RecruitmentStatus,
    FundingStatus,
    DependantSupportClassification
)
from src.ranking.opportunity_scorer import OpportunityScorer
from src.utils.config_loader import ConfigManager


@pytest.fixture
def scorer():
    return OpportunityScorer()


def test_classify_recruitment_status(scorer):
    # Active positive quotes
    quote1 = "We are seeking motivated PhD students to join our Edge AI group in Fall 2026."
    status1, snippet1 = scorer.classify_recruitment_status(quote1)
    assert status1 == RecruitmentStatus.ACTIVELY_RECRUITING.value
    assert "seeking" in snippet1.lower()

    # Negative signals
    quote2 = "Due to capacity, our group is not accepting PhD students at this time."
    status2, snippet2 = scorer.classify_recruitment_status(quote2)
    assert status2 == RecruitmentStatus.NOT_CURRENTLY_RECRUITING.value
    assert "not accepting" in snippet2.lower()

    # Unverified general text
    quote3 = "The laboratory investigates distributed computing algorithms and parallel architectures."
    status3, snippet3 = scorer.classify_recruitment_status(quote3)
    assert status3 == RecruitmentStatus.NOT_VERIFIED.value
    assert snippet3 == ""


def test_classify_funding_status(scorer):
    text1 = "This is a fully funded PhD studentship covering tuition and living stipend."
    f_status1, desc1 = scorer.classify_funding_status(text1)
    assert f_status1 == FundingStatus.FULLY_FUNDED.value
    assert "Fully funded" in desc1

    text2 = "Position provides partial scholarship covering tuition only."
    f_status2, _ = scorer.classify_funding_status(text2)
    assert f_status2 == FundingStatus.PARTIALLY_FUNDED.value

    text3 = "Applicants must be self-funded or have external institutional sponsorships."
    f_status3, _ = scorer.classify_funding_status(text3)
    assert f_status3 == FundingStatus.SELF_FUNDED.value


def test_classify_dependant_support(scorer):
    # Financially supported with family allowance
    text_financial = "Full TV-L E13 contract with child supplement and monthly family allowance."
    dep_status1, info1 = scorer.classify_dependant_support(text_financial, "Germany")
    assert dep_status1 == DependantSupportClassification.FINANCIALLY_SUPPORTED.value
    assert "family allowance" in info1 or "child supplement" in info1

    # Permitted in target country without dedicated family allowance
    text_general = "Standard doctoral stipend covering student maintenance."
    dep_status2, info2 = scorer.classify_dependant_support(text_general, "United Kingdom")
    assert dep_status2 == DependantSupportClassification.PERMITTED.value
    assert "United Kingdom" in info2

    # Restricted
    text_restricted = "Single students only; dependants not permitted on this exchange programme."
    dep_status3, _ = scorer.classify_dependant_support(text_restricted, "Other")
    assert dep_status3 == DependantSupportClassification.RESTRICTED.value


def test_score_phd_opportunity(scorer):
    opp = PhDOpportunity(
        title="Funded PhD in Edge Computing and Autonomous Intelligence",
        university="Technical University of Munich",
        country="Germany",
        research_areas=["Edge Computing", "Edge Intelligence", "Distributed Systems"],
        funding_status=FundingStatus.FULLY_FUNDED.value,
        recruitment_status=RecruitmentStatus.ACTIVELY_RECRUITING.value,
        recruitment_evidence="We are seeking talented PhD candidates.",
        dependant_support_classification=DependantSupportClassification.FINANCIALLY_SUPPORTED.value
    )

    scored = scorer.score_opportunity(opp)
    assert scored.composite_score >= 8.5
    assert scored.relevance_score >= 8.0
    assert scored.funding_score == 10.0
    assert scored.supervisor_fit_score == 10.0
    assert scored.country_score == 10.0
    assert any("Actively recruiting" in r for r in scored.reasons)
    assert any("Fully funded" in r for r in scored.reasons)


def test_score_scholarship(scorer):
    schol = Scholarship(
        name="DAAD Doctoral Research Grant",
        country="Germany",
        funding_type="fully_funded",
        dependant_support_classification=DependantSupportClassification.FINANCIALLY_SUPPORTED.value,
        dependant_support_details="Family allowance for spouse and children",
        official_url="https://daad.de"
    )

    scored = scorer.score_scholarship(schol)
    assert scored.score == 10.0
    assert any("Family financial allowance" in r for r in scored.reasons)
    assert any("Target country priority" in r for r in scored.reasons)


def test_score_researcher(scorer):
    prof = ResearcherProfile(
        name="Prof. Satya",
        institution="Carnegie Mellon University",
        country="United States",
        research_areas=["Edge Computing", "Cloudlets"],
        recruitment_status=RecruitmentStatus.ACTIVELY_RECRUITING.value,
        recruitment_evidence="Openings available for PhD students in Edge Computing.",
        publication_count=8
    )

    scored = scorer.score_researcher(prof)
    assert scored.composite_score >= 8.0
    assert any("Actively recruiting" in r for r in scored.reasons)
