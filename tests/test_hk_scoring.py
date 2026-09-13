"""
Unit tests for multi-factor scoring algorithms.
Verifies researcher eligibility, composite opportunity ranking, and familiarity scores.
"""

import unittest
from datetime import date
from hk_supervisor_intel.models import (
    ResearcherProfile, RecruitmentEvidence, Scholarship, FamiliarityRecord, Publication
)
from hk_supervisor_intel.scoring import ScoringEngine

class TestScoring(unittest.TestCase):

    def setUp(self):
        self.evidence = RecruitmentEvidence(
            status="CONFIRMED_ACTIVE",
            confidence=0.95,
            evidence_text="Positions open",
            source_url="https://example.com",
            source_type="official_lab_website",
            source_date="2026-06-01",
            last_verified="2026-09-01"
        )
        self.pub = Publication(
            publication_id="pub1",
            title="Sample Edge AI Paper",
            authors=["Prof. Test"],
            year=2024,
            venue="IEEE INFOCOM",
            doi_or_url="https://doi.org/sample",
            research_problem="Latency",
            approach="Offloading",
            key_contribution="Speedup",
            edge_relevance="Edge AI",
            is_seminal=True,
            is_recent=True
        )
        self.researcher = ResearcherProfile(
            researcher_id="test_prof",
            name="Prof. Test Edge",
            university="The Hong Kong Polytechnic University",
            department="COMP",
            position="Chair Professor, IEEE Fellow",
            research_group="Edge Lab",
            official_profile_url="https://example.com",
            personal_website="https://example.com/~test",
            google_scholar="https://scholar.google.com/test",
            orcid="0000-0000-0000-0000",
            dblp="https://dblp.org/test",
            research_interests=["Edge Computing", "Edge AI", "Distributed Systems"],
            research_summary="Pioneering researcher in edge systems and distributed AI.",
            edge_relevance="Direct alignment.",
            research_trajectory="Pioneered edge computing architectures.",
            current_projects=["Edge AI Grant", "FL Systems"],
            research_methods=["Optimization", "Testbeds"],
            datasets=["EdgeBench"],
            simulation_tools=["EdgeCloudSim"],
            systems_testbeds=["Raspberry Pi Cluster"],
            recruitment=self.evidence,
            potential_phd_topics=["Edge Topic 1"],
            potential_alignment="Excellent.",
            priority_tier="Tier 1",
            publications=[self.pub],
            alignment_score=95.0
        )
        self.scholarship = Scholarship(
            scholarship_id="hkpfs",
            university="The Hong Kong Polytechnic University",
            scholarship_name="Hong Kong PhD Fellowship Scheme (HKPFS)",
            phd_program="PhD in Computing",
            eligibility="Top students",
            application_deadline="2026-12-01",
            funding_amount="HK$331,200/yr",
            tuition_coverage="Full waiver",
            living_allowance="HK$27,600/mo",
            duration="4 years",
            dependent_support="None",
            supervisor_requirement="Recommended",
            application_requirements="Standard",
            official_url="https://example.com",
            source="RGC",
            last_verified="2026-09-01"
        )

    def test_researcher_eligibility_scoring(self):
        score = ScoringEngine.calculate_researcher_score(self.researcher, 95.0, date(2026, 9, 1))
        self.assertGreaterEqual(score, 90.0)
        self.assertLessEqual(score, 100.0)

    def test_opportunity_scoring(self):
        fam = FamiliarityRecord(researcher_id="test_prof")
        opp_score = ScoringEngine.calculate_opportunity_score(
            self.researcher,
            self.scholarship,
            days_remaining=45,
            familiarity=fam
        )
        self.assertGreaterEqual(opp_score, 85.0)
        self.assertLessEqual(opp_score, 100.0)

    def test_familiarity_score_growth(self):
        fam = FamiliarityRecord(researcher_id="test_prof")
        score_day1 = ScoringEngine.calculate_familiarity_score(fam, self.researcher)
        
        # Advance exposure cycle
        fam.exposure_cycle_day = 7
        fam.papers_exposed = ["Sample Edge AI Paper"]
        fam.research_trajectory_understood = True
        fam.recruitment_verified = True
        score_day7 = ScoringEngine.calculate_familiarity_score(fam, self.researcher)

        self.assertGreater(score_day7, score_day1)
        self.assertGreaterEqual(score_day7, 75.0)

if __name__ == "__main__":
    unittest.main()
