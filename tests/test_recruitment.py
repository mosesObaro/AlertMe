"""
Unit tests for recruitment classification and the 12-month freshness window.
Verifies evidence-based categorization and stale evidence detection.
"""

import unittest
from datetime import date, timedelta
from hk_supervisor_intel.recruitment import RecruitmentEngine
from hk_supervisor_intel.models import RecruitmentEvidence

class TestRecruitment(unittest.TestCase):

    def setUp(self):
        self.ref_date = date(2026, 9, 1)

    def test_classification_confirmed_active(self):
        recent_date = (self.ref_date - timedelta(days=60)).strftime("%Y-%m-%d")
        evidence = RecruitmentEngine.classify_recruitment_evidence(
            evidence_text="Seeking highly motivated PhD students for Fall 2027 under HKPFS.",
            source_url="https://example.com/lab",
            source_type="official_lab_website",
            source_date=recent_date,
            reference_date=self.ref_date
        )
        self.assertEqual(evidence.status, "CONFIRMED_ACTIVE")
        self.assertGreaterEqual(evidence.confidence, 0.90)

    def test_classification_strong_evidence(self):
        recent_date = (self.ref_date - timedelta(days=90)).strftime("%Y-%m-%d")
        evidence = RecruitmentEngine.classify_recruitment_evidence(
            evidence_text="Accepting PhD students with strong math/systems backgrounds.",
            source_url="https://example.com/faculty",
            source_type="faculty_homepage",
            source_date=recent_date,
            reference_date=self.ref_date
        )
        self.assertEqual(evidence.status, "STRONG_EVIDENCE")

    def test_classification_not_currently_recruiting(self):
        recent_date = (self.ref_date - timedelta(days=30)).strftime("%Y-%m-%d")
        evidence = RecruitmentEngine.classify_recruitment_evidence(
            evidence_text="Lab is full; not accepting new PhD students this academic cycle.",
            source_url="https://example.com/faculty",
            source_type="faculty_homepage",
            source_date=recent_date,
            reference_date=self.ref_date
        )
        self.assertEqual(evidence.status, "NOT_CURRENTLY_RECRUITING")
        score = RecruitmentEngine.get_recruitment_score(evidence, self.ref_date)
        self.assertEqual(score, 0.0)

    def test_freshness_window_stale_detection(self):
        # 400 days old (> 365 days)
        old_date = (self.ref_date - timedelta(days=400)).strftime("%Y-%m-%d")
        evidence = RecruitmentEngine.classify_recruitment_evidence(
            evidence_text="Seeking highly motivated PhD students for 2024.",
            source_url="https://example.com/lab",
            source_type="official_lab_website",
            source_date=old_date,
            reference_date=self.ref_date
        )
        self.assertEqual(evidence.status, "RECRUITMENT_STALE")
        
        # Freshness penalty applied in score
        score = RecruitmentEngine.get_recruitment_score(evidence, self.ref_date)
        self.assertLess(score, 50.0)

    def test_freshness_window_active_under_12_months(self):
        # 180 days old (< 365 days)
        fresh_date = (self.ref_date - timedelta(days=180)).strftime("%Y-%m-%d")
        evidence = RecruitmentEngine.classify_recruitment_evidence(
            evidence_text="PhD positions available for prospective students.",
            source_url="https://example.com/lab",
            source_type="official_lab_website",
            source_date=fresh_date,
            reference_date=self.ref_date
        )
        self.assertIn(evidence.status, ["CONFIRMED_ACTIVE", "STRONG_EVIDENCE"])

if __name__ == "__main__":
    unittest.main()
