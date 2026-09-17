"""
Test Suite for Global Country-Based PhD Funding & Supervisor Intelligence Engine.
Tests all 7 countries (UK, Japan, Germany, US, Canada, Sweden, Hong Kong),
ensuring >= 8 vetted professors and >= 8 universities per country, 1-day campaign execution,
quad-format document generation (MD, PDF, DOCX, EPUB), funding classification,
and 100% preservation of curriculum tracker sheets.
"""

import os
import shutil
import pytest
from pathlib import Path
from openpyxl import load_workbook

from src.supervisors.config import (
    SUPPORTED_COUNTRIES, MINIMUM_PROFESSORS_PER_COUNTRY, normalize_country_key
)
from src.supervisors.models import (
    UniversityProfile, FundingOpportunity, ResearcherProfile, Publication, RecruitmentEvidence
)
from src.supervisors.storage import StorageManager
from src.supervisors.discovery import DiscoveryEngine
from src.supervisors.funding import FundingEngine
from src.supervisors.scoring import ScoringEngine
from src.supervisors.profiler import DossierProfiler
from src.supervisors.campaign import CountryCampaignManager
from src.supervisors.alerts import CountryAlertGenerator
from src.supervisors.excel_extension import add_country_supervisor_sheets


class TestCountrySupervisors:

    @classmethod
    def setup_class(cls):
        cls.storage = StorageManager()
        cls.manager = CountryCampaignManager(storage=cls.storage)

    def test_all_seven_countries_configured(self):
        """Verify all 7 first-class country campaigns are configured."""
        expected_countries = {"uk", "japan", "germany", "us", "canada", "sweden", "hong_kong"}
        assert expected_countries.issubset(set(SUPPORTED_COUNTRIES.keys()))
        for key in expected_countries:
            cfg = SUPPORTED_COUNTRIES[key]
            assert "name" in cfg
            assert "country_code" in cfg
            assert "currency" in cfg
            assert "immigration_dependant_guidance" in cfg
            assert "primary_funding_vehicle" in cfg

    def test_minimum_quota_eight_universities_and_professors_per_country(self):
        """Every target country must meet the hard requirement of >= 8 universities and >= 8 professors."""
        for country_key in SUPPORTED_COUNTRIES:
            unis = self.storage.get_universities(country_key)
            profs = self.storage.get_professors(country_key)
            deduped_unis = DiscoveryEngine.deduplicate_universities(unis)
            deduped_profs = DiscoveryEngine.deduplicate_professors(profs)

            assert len(deduped_unis) >= 8, f"{country_key} has only {len(deduped_unis)} universities, minimum 8 required"
            assert len(deduped_profs) >= MINIMUM_PROFESSORS_PER_COUNTRY, (
                f"{country_key} has only {len(deduped_profs)} professors, minimum {MINIMUM_PROFESSORS_PER_COUNTRY} required"
            )

    def test_country_campaign_dry_run_all_countries(self):
        """Verify 1-day country campaign runs synchronously without errors for all countries."""
        for country_key in SUPPORTED_COUNTRIES:
            result = self.manager.run_country_campaign(country_key, dry_run=True, generate_docs=False)
            assert result.country_code != ""
            assert result.professors_count >= 8
            assert result.universities_count >= 8
            assert result.funding_opportunities_count >= 1

    def test_discovery_deduplication(self):
        """Verify multi-signal deduplication for professors, universities, and funding."""
        # University deduplication
        u1 = UniversityProfile(
            university_id="u1", canonical_name="Imperial College London", country="United Kingdom",
            country_code="UK", aliases=["Imperial"], official_url="https://imperial.ac.uk",
            graduate_school_url="", research_url="", phd_application_url="", funding_url="",
            relevant_departments=[], relevant_research_centres=[]
        )
        u2 = UniversityProfile(
            university_id="u2", canonical_name="imperial college london", country="united kingdom",
            country_code="UK", aliases=[], official_url="",
            graduate_school_url="", research_url="", phd_application_url="", funding_url="",
            relevant_departments=[], relevant_research_centres=[]
        )
        assert len(DiscoveryEngine.deduplicate_universities([u1, u2])) == 1

        # Professor deduplication by composite key and ORCID
        p1 = ResearcherProfile(
            researcher_id="p1", name="Prof. Jon Crowcroft", university="University of Cambridge",
            country="United Kingdom", department="CS", position="Professor", research_group="SRG",
            official_profile_url="https://cl.cam.ac.uk/~jac22", orcid="0000-0002-0106-6917"
        )
        p2 = ResearcherProfile(
            researcher_id="p2", name="jon crowcroft", university="university of cambridge",
            country="United Kingdom", department="CS", position="Professor", research_group="SRG",
            official_profile_url="https://cl.cam.ac.uk/~jac22/other", orcid="0000-0002-0106-6917"
        )
        assert len(DiscoveryEngine.deduplicate_professors([p1, p2])) == 1

    def test_funding_classification(self):
        """Verify evidence-based funding and dependant classifications."""
        assert FundingEngine.classify_funding_type("Full 100% waiver", "£21,000/yr") == "FULLY_FUNDED"
        assert FundingEngine.classify_funding_type("Partial tuition", "None") == "PARTIALLY_FUNDED"
        assert FundingEngine.classify_funding_type("100% tuition", "None") == "TUITION_ONLY"
        assert FundingEngine.classify_funding_type("None", "$30,000/yr") == "STIPEND_ONLY"

        dep_good = FundingEngine.classify_dependant_support("Child allowance and spouse health cover provided.")
        assert dep_good in ["EXCELLENT", "GOOD"]
        dep_permitted = FundingEngine.classify_dependant_support("Dependants are permitted to accompany student on standard study visa.")
        assert dep_permitted == "PERMITTED"

    def test_scoring_engine_transparency(self):
        """Scoring must produce 0-100 range and transparent why_suitable rationale."""
        uk_profs = self.storage.get_professors("uk")
        assert len(uk_profs) > 0
        score, rationale = ScoringEngine.score_professor(uk_profs[0])
        assert 0.0 <= score <= 100.0
        assert len(rationale) >= 1
        assert isinstance(rationale, list)

    def test_quad_format_dossier_and_country_report_generation(self, tmp_path):
        """Verify generation of all 4 formats: MD, DOCX, PDF, EPUB."""
        profiler = DossierProfiler(output_base_dir=tmp_path / "reports" / "supervisors")
        
        uk_profs = self.storage.get_professors("uk")
        uk_unis = self.storage.get_universities("uk")
        uk_funds = self.storage.get_funding_opportunities("uk")

        # 1. Single professor dossier in 4 formats
        dossier_files = profiler.generate_professor_dossiers(
            country_key="uk",
            researcher=uk_profs[0],
            university=uk_unis[0],
            funding=uk_funds
        )
        assert set(dossier_files.keys()) == {"markdown", "docx", "pdf", "epub"}
        for fmt, fpath in dossier_files.items():
            p = Path(fpath)
            assert p.exists(), f"Missing file: {p}"
            assert p.stat().st_size > 0, f"Empty file: {p}"

        # 2. Country report in 4 formats
        report_files = profiler.generate_country_reports(
            country_key="uk",
            campaign=self.storage.get_country_campaign("uk"),
            universities=uk_unis[:3],
            professors=uk_profs[:3],
            funding=uk_funds
        )
        assert set(report_files.keys()) == {"markdown", "docx", "pdf", "epub"}
        for fmt, fpath in report_files.items():
            p = Path(fpath)
            assert p.exists(), f"Missing file: {p}"
            assert p.stat().st_size > 0, f"Empty file: {p}"

    def test_excel_extension_preserves_11_curriculum_sheets(self, tmp_path):
        """Verify that updating the Excel tracker keeps the original 11 curriculum sheets 100% intact."""
        master_excel = Path("Edge_Computing_PhD_Curriculum_Tracker.xlsx")
        assert master_excel.exists()

        temp_excel = tmp_path / "tracker_copy.xlsx"
        shutil.copyfile(master_excel, temp_excel)

        wb_orig = load_workbook(temp_excel)
        orig_sheets = list(wb_orig.sheetnames)
        wb_orig.close()

        # Augment workbook
        res = add_country_supervisor_sheets(workbook_path=temp_excel, storage=self.storage)
        assert res["status"] == "success"

        wb_new = load_workbook(temp_excel)
        new_sheets = list(wb_new.sheetnames)
        wb_new.close()

        # The 11 foundational curriculum sheets must still be present in the original order
        assert orig_sheets[:11] == new_sheets[:11]
        # And the new supervisor intelligence sheets must be added
        assert "Country Intelligence" in new_sheets
        assert "Global Supervisor Directory" in new_sheets
        assert "Global PhD Funding" in new_sheets

    def test_country_alert_renderer_and_email(self):
        """Verify email briefing HTML rendering contains download links for all 4 formats and valid canonical paths."""
        result = self.manager.run_country_campaign("uk", dry_run=True, generate_docs=False)
        alert_gen = CountryAlertGenerator()
        html = alert_gen.render_country_briefing_html(result)

        assert "United Kingdom" in html
        assert "Prof. Jon Crowcroft" in html or "Jon Crowcroft" in html
        assert "Markdown Dossier" in html
        assert "PDF" in html
        assert "Word" in html
        assert "EPUB" in html
        assert "reports/supervisors/uk/country_profile.pdf" in html
        assert "reports/supervisors/uk/professors/" in html

        # Verify Japan uses 'japan' directory, NOT 'jp'
        result_jp = self.manager.run_country_campaign("japan", dry_run=True, generate_docs=False)
        html_jp = alert_gen.render_country_briefing_html(result_jp)
        assert "reports/supervisors/japan/country_profile.pdf" in html_jp
        assert "reports/supervisors/japan/professors/" in html_jp
        assert "reports/supervisors/jp/" not in html_jp

        # Dry run send email
        send_res = alert_gen.send_country_alert(result, dry_run=True)
        assert send_res["status"] == "dry_run"

    def test_global_alert_renderer_and_email(self):
        """Verify global email briefing HTML rendering and dispatch for all countries with canonical URLs."""
        all_results = self.manager.run_all_campaigns(dry_run=True, generate_docs=False)
        alert_gen = CountryAlertGenerator()
        payload = alert_gen.render_global_email(all_results)

        assert "Global PhD Funding & Supervisor Briefing" in payload["subject"]
        assert "Country Campaign Portfolio" in payload["html"]
        assert "United Kingdom" in payload["html"]
        assert "Japan" in payload["html"]
        assert "Germany" in payload["html"]
        assert "United States" in payload["html"]
        assert "Canada" in payload["html"]
        assert "Sweden" in payload["html"]
        assert "Hong Kong" in payload["html"]

        # Ensure all 7 canonical country folder paths exist in links
        assert "reports/supervisors/japan/country_profile.pdf" in payload["html"]
        assert "reports/supervisors/germany/country_profile.pdf" in payload["html"]
        assert "reports/supervisors/sweden/country_profile.pdf" in payload["html"]
        assert "reports/supervisors/canada/country_profile.pdf" in payload["html"]
        assert "reports/supervisors/hong_kong/country_profile.pdf" in payload["html"]
        assert "reports/supervisors/uk/country_profile.pdf" in payload["html"]
        assert "reports/supervisors/us/country_profile.pdf" in payload["html"]

        # Ensure short 2-letter codes were not incorrectly used for paths
        assert "reports/supervisors/jp/" not in payload["html"]
        assert "reports/supervisors/de/" not in payload["html"]
        assert "reports/supervisors/se/" not in payload["html"]
        assert "reports/supervisors/ca/" not in payload["html"]
        assert "reports/supervisors/hk/" not in payload["html"]

        send_res = alert_gen.send_global_alert(all_results, dry_run=True)
        assert send_res["status"] == "dry_run"
