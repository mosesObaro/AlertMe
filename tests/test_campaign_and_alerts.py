"""
Unit tests for the 10-week campaign manager and daily alert generator.
Verifies milestone tracking, deadline calculation, and duplicate alert suppression.
"""

import unittest
import tempfile
import os
from datetime import date
from hk_supervisor_intel.campaign import CampaignManager
from hk_supervisor_intel.storage import StorageManager
from hk_supervisor_intel.alerts import AlertGenerator

class TestCampaignAndAlerts(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "test_state.json")
        self.storage = StorageManager(state_file=self.state_file)
        self.campaign = CampaignManager(target_deadline="2026-12-01")

    def test_campaign_time_remaining(self):
        test_date = date(2026, 9, 13)
        time_info = self.campaign.get_time_remaining(test_date)
        self.assertEqual(time_info["days_remaining"], 79)
        self.assertEqual(time_info["weeks_remaining"], 12)
        self.assertEqual(time_info["current_campaign_week"], 1)

    def test_campaign_late_phase(self):
        test_date = date(2026, 11, 20)
        time_info = self.campaign.get_time_remaining(test_date)
        self.assertEqual(time_info["days_remaining"], 11)
        self.assertEqual(time_info["weeks_remaining"], 2)
        self.assertEqual(time_info["current_campaign_week"], 9)

    def test_daily_alert_generation(self):
        alert_gen = AlertGenerator(self.storage, self.campaign)
        alert = alert_gen.generate_daily_alert(reference_date=date(2026, 9, 13))
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.priority_tier, "Tier 1")
        self.assertIn("HONG KONG PHD SUPERVISOR INTELLIGENCE", alert.to_markdown())
        self.assertIn("UNIVERSITY:", alert.to_markdown())
        self.assertIn("Professor:", alert.to_markdown())
        self.assertIn("TODAY'S RESEARCH FOCUS", alert.to_markdown())
        self.assertIn("RESEARCH PROBLEM:", alert.to_markdown())

    def test_daily_alert_html_rendering(self):
        alert_gen = AlertGenerator(self.storage, self.campaign)
        alert = alert_gen.generate_daily_alert(reference_date=date(2026, 9, 13))
        
        self.assertIsNotNone(alert)
        html = alert.to_html()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Hong Kong PhD Supervisor Intelligence", html)
        self.assertIn(alert.professor, html)
        self.assertIn(alert.university, html)
        self.assertIn(alert.paper_title, html)
        self.assertIn(alert.recruitment_evidence, html)
        self.assertIn(alert.paper_link, html)
        self.assertIn("Why This Matters for Edge Computing", html)

    def test_duplicate_alert_suppression(self):
        alert_gen = AlertGenerator(self.storage, self.campaign)
        alert1 = alert_gen.generate_daily_alert(reference_date=date(2026, 9, 13))
        
        # Check storage has recorded the alert
        self.assertEqual(len(self.storage.alert_history), 1)
        self.assertTrue(self.storage.has_recent_alert_for_paper(alert1.paper_title, days_window=14))

if __name__ == "__main__":
    unittest.main()
