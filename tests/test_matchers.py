"""
Unit tests for Curriculum Matcher and Research Ideas Matcher.
Verifies bidirectional bridging between Hong Kong faculty and the existing curriculum and idea bank.
"""

import unittest
from hk_supervisor_intel.storage import StorageManager
from hk_supervisor_intel.curriculum_matcher import CurriculumMatcher
from hk_supervisor_intel.ideas_matcher import IdeasMatcher

class TestMatchers(unittest.TestCase):

    def setUp(self):
        self.storage = StorageManager()

    def test_curriculum_matcher_distributed_systems(self):
        cao = self.storage.researchers.get("polyu_cao_jiannong")
        self.assertIsNotNone(cao)
        match = CurriculumMatcher.match_researcher_to_curriculum(cao)
        
        self.assertIn(1, match["matched_weeks"])   # Edge Foundations
        self.assertIn(5, match["matched_weeks"])   # Distributed Systems
        self.assertTrue(any("Distributed Systems" in c for c in match["matched_courses"]))

    def test_curriculum_matcher_optimization(self):
        chen = self.storage.researchers.get("cuhk_chen_minghua")
        self.assertIsNotNone(chen)
        match = CurriculumMatcher.match_researcher_to_curriculum(chen)
        
        self.assertIn(15, match["matched_weeks"])  # Task offloading & optimization
        self.assertIn(16, match["matched_weeks"])  # Convex optimization (EE364a)

    def test_ideas_matcher_federated_intelligence(self):
        matches = IdeasMatcher.match_supervisors_for_idea(
            "Federated Edge Intelligence",
            list(self.storage.researchers.values())
        )
        self.assertGreaterEqual(len(matches), 1)
        prof_names = [m["professor"] for m in matches]
        self.assertTrue(any("Song Guo" in name or "Wei Wang" in name for name in prof_names))

    def test_ideas_matcher_v2x_mobility(self):
        matches = IdeasMatcher.match_supervisors_for_idea(
            "Computation Offloading & Mobility",
            list(self.storage.researchers.values())
        )
        prof_names = [m["professor"] for m in matches]
        self.assertTrue(any("Jianping Wang" in name for name in prof_names))

if __name__ == "__main__":
    unittest.main()
