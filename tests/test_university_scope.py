"""
Unit tests for institutional boundaries and university scope enforcement.
Verifies that only the 8 target Hong Kong universities are accepted and outside institutions are strictly rejected.
"""

import unittest
from hk_supervisor_intel.config import TARGET_HONG_KONG_UNIVERSITIES, UNIVERSITY_ALIASES
from hk_supervisor_intel.discovery import DiscoveryEngine
from hk_supervisor_intel.models import ResearcherProfile, RecruitmentEvidence

class TestUniversityScope(unittest.TestCase):
    
    def test_canonical_universities_count(self):
        """Assert exactly 8 target universities are configured."""
        self.assertEqual(len(TARGET_HONG_KONG_UNIVERSITIES), 8)
        self.assertIn("City University of Hong Kong", TARGET_HONG_KONG_UNIVERSITIES)
        self.assertIn("Hong Kong Baptist University", TARGET_HONG_KONG_UNIVERSITIES)
        self.assertIn("Lingnan University", TARGET_HONG_KONG_UNIVERSITIES)
        self.assertIn("The Chinese University of Hong Kong", TARGET_HONG_KONG_UNIVERSITIES)
        self.assertIn("The Education University of Hong Kong", TARGET_HONG_KONG_UNIVERSITIES)
        self.assertIn("The Hong Kong Polytechnic University", TARGET_HONG_KONG_UNIVERSITIES)
        self.assertIn("The Hong Kong University of Science and Technology", TARGET_HONG_KONG_UNIVERSITIES)
        self.assertIn("The University of Hong Kong", TARGET_HONG_KONG_UNIVERSITIES)

    def test_alias_normalization(self):
        """Verifies aliases resolve to the exact canonical names."""
        test_cases = [
            ("CityU", "City University of Hong Kong"),
            ("cityu hk", "City University of Hong Kong"),
            ("HKBU", "Hong Kong Baptist University"),
            ("baptist university", "Hong Kong Baptist University"),
            ("LU", "Lingnan University"),
            ("lingnan u", "Lingnan University"),
            ("CUHK", "The Chinese University of Hong Kong"),
            ("chinese university of hong kong", "The Chinese University of Hong Kong"),
            ("EdUHK", "The Education University of Hong Kong"),
            ("ied", "The Education University of Hong Kong"),
            ("PolyU", "The Hong Kong Polytechnic University"),
            ("hk polyu", "The Hong Kong Polytechnic University"),
            ("HKUST", "The Hong Kong University of Science and Technology"),
            ("ust", "The Hong Kong University of Science and Technology"),
            ("HKU", "The University of Hong Kong"),
            ("u of hong kong", "The University of Hong Kong"),
        ]
        for alias, expected in test_cases:
            normalized = DiscoveryEngine.normalize_university_name(alias)
            self.assertEqual(normalized, expected, f"Failed for alias '{alias}'")

    def test_strict_rejection_of_outside_universities(self):
        """Asserts outside institutions (even in HK or nearby) are strictly rejected."""
        outside_institutions = [
            "Tsinghua University",
            "Peking University",
            "National University of Singapore",
            "Nanyang Technological University",
            "MIT",
            "Stanford University",
            "University of Cambridge",
            "Hong Kong Metropolitan University",
            "Hong Kong Shue Yan University",
            "The Hang Seng University of Hong Kong",
            "Chu Hai College of Higher Education"
        ]
        for inst in outside_institutions:
            normalized = DiscoveryEngine.normalize_university_name(inst)
            self.assertIsNone(normalized, f"Outside institution '{inst}' was not rejected!")
            self.assertFalse(DiscoveryEngine.is_target_university(inst))

    def test_researcher_filtering_and_deduplication(self):
        """Verifies candidate filtering drops outside universities and unifies duplicates."""
        dummy_evidence = RecruitmentEvidence(
            status="CONFIRMED_ACTIVE",
            confidence=0.9,
            evidence_text="Positions open",
            source_url="https://example.com",
            source_type="faculty_homepage",
            source_date="2026-06-01",
            last_verified="2026-09-01"
        )
        
        candidates = [
            ResearcherProfile(
                researcher_id="p1", name="Prof. Valid One", university="HKUST",
                department="CSE", position="Prof", research_group="Lab",
                official_profile_url="", personal_website="", google_scholar="", orcid="", dblp="",
                research_interests=["Edge Computing"], research_summary="", edge_relevance="",
                research_trajectory="", current_projects=[], research_methods=[], datasets=[],
                simulation_tools=[], systems_testbeds=[], recruitment=dummy_evidence,
                potential_phd_topics=[], potential_alignment="", priority_tier="Tier 1"
            ),
            ResearcherProfile(
                researcher_id="p2", name="Prof. Valid One", university="The Hong Kong University of Science and Technology",
                department="CSE", position="Prof", research_group="Lab",
                official_profile_url="", personal_website="", google_scholar="", orcid="", dblp="",
                research_interests=["Edge Computing"], research_summary="", edge_relevance="",
                research_trajectory="", current_projects=[], research_methods=[], datasets=[],
                simulation_tools=[], systems_testbeds=[], recruitment=dummy_evidence,
                potential_phd_topics=[], potential_alignment="", priority_tier="Tier 1"
            ),
            ResearcherProfile(
                researcher_id="p3", name="Prof. Invalid Outside", university="National University of Singapore",
                department="CS", position="Prof", research_group="Lab",
                official_profile_url="", personal_website="", google_scholar="", orcid="", dblp="",
                research_interests=["Edge Computing"], research_summary="", edge_relevance="",
                research_trajectory="", current_projects=[], research_methods=[], datasets=[],
                simulation_tools=[], systems_testbeds=[], recruitment=dummy_evidence,
                potential_phd_topics=[], potential_alignment="", priority_tier="Tier 1"
            )
        ]

        filtered = DiscoveryEngine.filter_by_target_university(candidates)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].university, "The Hong Kong University of Science and Technology")
        
        deduped = DiscoveryEngine.deduplicate_researchers(filtered)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].name, "Prof. Valid One")

if __name__ == "__main__":
    unittest.main()
