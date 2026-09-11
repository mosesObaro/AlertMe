"""Unit tests for PhD Opportunities, Scholarships, and Researcher models."""

import pytest
from src.models import (
    PhDOpportunity,
    Scholarship,
    ResearcherProfile,
    ResearchItem,
    RecruitmentStatus,
    FundingStatus,
    DependantSupportClassification,
    ItemType
)


def test_phd_opportunity_creation_and_id():
    opp = PhDOpportunity(
        title="PhD in Edge Computing and AI",
        university="Technical University of Munich",
        department="Computer Science",
        professor_name="Prof. Weber",
        country="Germany",
        research_areas=["Edge AI", "Distributed Systems"],
        funding_status=FundingStatus.FULLY_FUNDED.value,
        recruitment_status=RecruitmentStatus.ACTIVELY_RECRUITING.value,
        recruitment_evidence="We are actively looking for PhD students."
    )

    assert opp.id.startswith("opp_")
    assert opp.university == "Technical University of Munich"
    assert opp.country == "Germany"

    # Deterministic id
    opp2 = PhDOpportunity(
        title="PhD in Edge Computing and AI",
        university="Technical University of Munich",
        professor_name="Prof. Weber",
        source_url=""
    )
    assert opp.id == opp2.id


def test_phd_opportunity_to_research_item():
    opp = PhDOpportunity(
        title="PhD Position in Fog Computing",
        university="University of Cambridge",
        country="United Kingdom",
        professor_name="Prof. Smith",
        research_areas=["Fog Computing"],
        funding_status=FundingStatus.FULLY_FUNDED.value,
        dependant_support_classification=DependantSupportClassification.PERMITTED.value,
        composite_score=9.2
    )

    item = opp.to_research_item()
    assert isinstance(item, ResearchItem)
    assert item.item_type == ItemType.PHD_OPPORTUNITY.value
    assert item.title == "PhD Position in Fog Computing"
    assert item.score.final_score == 9.2
    assert "United Kingdom" in item.abstract


def test_scholarship_model_and_dependant_support():
    schol = Scholarship(
        name="DAAD Doctoral Research Grant",
        provider="DAAD",
        country="Germany",
        stipend_amount="€1,300 / month",
        tuition_coverage="Full waiver",
        dependant_support_classification=DependantSupportClassification.FINANCIALLY_SUPPORTED.value,
        dependant_support_details="Spouse allowance ~€276/mo and child allowance ~€200/mo.",
        official_url="https://daad.de"
    )

    data = schol.to_dict()
    assert data["name"] == "DAAD Doctoral Research Grant"
    assert data["dependant_support_classification"] == "financially_supported"
    assert "Spouse allowance" in data["dependant_support_details"]


def test_researcher_profile_model():
    prof = ResearcherProfile(
        name="Schahram Dustdar",
        institution="TU Wien",
        country="Germany",
        research_areas=["Edge Intelligence", "Distributed Systems"],
        publication_count=10,
        composite_score=9.4,
        recruitment_status=RecruitmentStatus.ACTIVELY_RECRUITING.value,
        recruitment_quote="Looking for motivated PhD students to join our team."
    )

    data = prof.to_dict()
    assert data["name"] == "Schahram Dustdar"
    assert data["recruitment_status"] == "actively_recruiting"
    assert "Looking for motivated PhD students" in data["recruitment_quote"]

    sup_dict = prof.to_supervisor_dict()
    assert sup_dict["name"] == "Schahram Dustdar"
    assert sup_dict["recruitment_status"] == "actively_recruiting"
    assert sup_dict["composite_score"] == 9.4


def test_research_item_with_opportunity_data_roundtrip():
    item = ResearchItem(
        title="Test Opportunity Paper",
        url="https://example.com/opp",
        source="University Portal",
        item_type=ItemType.PHD_OPPORTUNITY.value,
        opportunity_data={
            "kind": "phd_opportunity",
            "title": "Funded PhD in Edge AI",
            "country": "Germany",
            "fit_score": 9.5
        }
    )

    serialized = item.to_dict()
    assert "opportunity_data" in serialized
    assert serialized["opportunity_data"]["country"] == "Germany"

    deserialized = ResearchItem.from_dict(serialized)
    assert deserialized.opportunity_data["kind"] == "phd_opportunity"
    assert deserialized.opportunity_data["fit_score"] == 9.5
