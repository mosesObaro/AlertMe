"""
Comprehensive Unit and Integration Tests for the Generic Evidence-Driven Supervisor Dossier Engine.
Verifies:
1. Canonical ProfessorDossier model serialization / deserialization roundtrip.
2. Multi-country, multi-professor generic synthesis (UK, Germany, Japan, Hong Kong).
3. Authoritative identity verification with official domain matching & ambiguity detection.
4. Quad-format document generation (MD, DOCX, PDF, EPUB, JSON) from single canonical model.
5. Complete 1-run dossier generation without multi-day progressive familiarity delays.
6. Absolute absence of hardcoded bias or professor-specific text.
"""

import os
import json
import pytest
from pathlib import Path
from datetime import date

from src.supervisors.models import (
    ProfessorDossier, DossierMetadata, DossierIdentity, ResearchEra,
    ResearchFieldTaxonomy, ResearchTransition, RecurringTheme,
    MajorPublicationDetail, CurrentSpecialization, CollaborationNetwork,
    SupervisionEvidence, ApplicantAlignmentDimension, PotentialPhDDirection,
    ResearchGaps, PublicationTrends, CareerComparisonRow, DossierFundingItem,
    DossierRecruitmentItem, ResearchEnvironmentDetail, ReadingRecommendationItem,
    ProposalPositioningDetail, QuestionsForProfessorDetail, SuitabilityScoreBreakdown,
    DossierSourcesDetail, ResearcherProfile, UniversityProfile, FundingOpportunity,
    Publication, CountryCampaign
)
from src.supervisors.identity import IdentityVerifier
from src.supervisors.analyzer import DossierSynthesizer
from src.supervisors.profiler import DossierProfiler
from src.supervisors.storage import StorageManager


class TestGenericDossierEngine:

    @pytest.fixture(autouse=True)
    def setup_engine(self, tmp_path):
        self.tmp_path = tmp_path
        self.storage = StorageManager()
        self.synthesizer = DossierSynthesizer()
        self.profiler = DossierProfiler(output_base_dir=tmp_path / "reports" / "supervisors")

    def test_canonical_model_serialization_roundtrip(self):
        """Verify full fidelity serialization and deserialization of ProfessorDossier."""
        uk_profs = self.storage.get_professors("uk")
        uk_unis = self.storage.get_universities("uk")
        uk_funds = self.storage.get_funding_opportunities("uk")

        dossier = self.synthesizer.synthesize(
            researcher=uk_profs[0],
            university=uk_unis[0],
            funding=uk_funds
        )

        dossier_dict = dossier.to_dict()
        assert isinstance(dossier_dict, dict)
        assert dossier_dict["metadata"]["professor_name"] == uk_profs[0].name
        assert len(dossier_dict["eras"]) >= 2
        assert len(dossier_dict["major_publications"]) >= 1
        assert dossier_dict["suitability_score"]["composite_score"] > 0

        # Deserialization
        restored = ProfessorDossier.from_dict(dossier_dict)
        assert restored.identity.full_name == dossier.identity.full_name
        assert restored.metadata.university == dossier.metadata.university
        assert len(restored.potential_directions) == len(dossier.potential_directions)
        assert restored.suitability_score.composite_score == dossier.suitability_score.composite_score

    def test_generic_synthesis_multiple_countries_and_professors(self):
        """Test dossier generation across diverse countries without any professor-specific logic."""
        test_cases = [
            ("uk", 0),
            ("germany", 0),
            ("japan", 0),
            ("singapore", 0)
        ]

        for country, idx in test_cases:
            profs = self.storage.get_professors(country)
            unis = self.storage.get_universities(country)
            funds = self.storage.get_funding_opportunities(country)
            campaign = self.storage.get_country_campaign(country)

            if not profs:
                continue

            prof = profs[idx]
            uni = next((u for u in unis if u.canonical_name.lower() in prof.university.lower() or prof.university.lower() in u.canonical_name.lower()), unis[0])

            dossier = self.synthesizer.synthesize(
                researcher=prof,
                university=uni,
                funding=funds,
                campaign=campaign
            )

            assert dossier.identity.full_name == prof.name
            assert prof.university.lower() in dossier.identity.university.lower() or uni.canonical_name.lower() in dossier.identity.university.lower()
            assert len(dossier.eras) >= 2
            assert len(dossier.fields_taxonomy) >= 2
            assert len(dossier.transitions) >= 1
            assert len(dossier.recurring_themes) >= 3
            assert len(dossier.potential_directions) >= 3
            assert len(dossier.reading_recommendations) >= 3
            assert dossier.suitability_score.composite_score >= 5.0
            assert len(dossier.research_fit_table) >= 3

    def test_authoritative_identity_verification(self):
        """Test domain matching, ambiguity detection, and audit trail generation."""
        # Case 1: Valid university domain
        prof = ResearcherProfile(
            researcher_id="test_valid",
            name="Prof. Alan Turing",
            university="University of Cambridge",
            country="United Kingdom",
            department="Department of Computer Science and Technology",
            position="Chair Professor",
            research_group="Systems Research Group",
            official_profile_url="https://www.cam.ac.uk/people/alan-turing",
            institutional_email="alan.turing@cam.ac.uk",
            google_scholar="https://scholar.google.com/citations?user=test_turing",
            dblp="https://dblp.org/pid/t/AlanTuring.html"
        )
        uni = UniversityProfile(
            university_id="cambridge",
            canonical_name="University of Cambridge",
            country="United Kingdom",
            country_code="GB",
            aliases=["Cambridge"],
            official_url="https://www.cam.ac.uk",
            graduate_school_url="https://www.postgraduate.study.cam.ac.uk",
            research_url="https://www.cam.ac.uk/research",
            phd_application_url="https://www.postgraduate.study.cam.ac.uk/apply",
            funding_url="https://www.cambridgetrust.org",
            relevant_departments=["Computer Science"],
            relevant_research_centres=["Systems Research Centre"]
        )

        identity = IdentityVerifier.verify_identity(prof, uni)
        assert identity.identity_confidence == "VERIFIED"
        assert any("domain cross-check verified" in ev for ev in identity.identity_evidence)
        assert any("Email domain matches institutional namespace" in ev for ev in identity.identity_evidence)

        # Case 2: Ambiguous single-token name and missing official faculty profile
        prof_ambiguous = ResearcherProfile(
            researcher_id="test_ambiguous",
            name="Turing",
            university="University of Cambridge",
            country="United Kingdom",
            department="Computing",
            position="Lecturer",
            research_group="Lab",
            official_profile_url=""
        )
        identity_amb = IdentityVerifier.verify_identity(prof_ambiguous, uni)
        assert "AMBIGUOUS" in identity_amb.identity_confidence
        assert any("single-word" in ev.lower() for ev in identity_amb.identity_evidence)

    def test_quad_format_rendering_from_canonical_model(self):
        """Verify that MD, DOCX, PDF, EPUB, and JSON are all produced from single model."""
        uk_profs = self.storage.get_professors("uk")
        uk_unis = self.storage.get_universities("uk")
        uk_funds = self.storage.get_funding_opportunities("uk")

        dossier_files = self.profiler.generate_professor_dossiers(
            country_key="uk",
            researcher=uk_profs[0],
            university=uk_unis[0],
            funding=uk_funds
        )

        assert set(dossier_files.keys()) == {"markdown", "docx", "pdf", "epub"}
        for fmt, path_str in dossier_files.items():
            fpath = Path(path_str)
            assert fpath.exists(), f"File {fmt} was not created: {fpath}"
            assert fpath.stat().st_size > 0, f"File {fmt} is empty: {fpath}"

        # Verify JSON audit model is also stored in the folder
        json_path = Path(dossier_files["markdown"]).parent / "dossier.json"
        assert json_path.exists()
        assert json_path.stat().st_size > 0

        with open(json_path, "r", encoding="utf-8") as jf:
            audit_data = json.load(jf)
            assert audit_data["identity"]["full_name"] == uk_profs[0].name

        # Verify Markdown content contains comprehensive 33 sections
        with open(dossier_files["markdown"], "r", encoding="utf-8") as mf:
            md_text = mf.read()
            assert "# Comprehensive Research Profile & PhD Supervisor Suitability Analysis" in md_text
            assert "## 1. Executive Summary" in md_text
            assert "## 4. Research Eras" in md_text
            assert "## 6. Research Transition Analysis" in md_text
            assert "## 12. Research Evolution Map" in md_text
            assert "## 16. My Research Fit" in md_text
            assert "## 17. Potential PhD Research Directions" in md_text
            assert "## 21. Supervisor Suitability Score" in md_text
            assert "## 23. Questions to Ask the Professor" in md_text
            assert "## 24. Recommended Reading List" in md_text
            assert "## 32. Sources & Evidence Requirements" in md_text
            assert "## 33. Verification Metadata" in md_text

    def test_complete_one_run_generation_without_progressive_wait(self):
        """Verify that a full dossier is generated immediately without waiting for Day 3."""
        uk_prof = self.storage.get_professors("uk")[0]
        uk_uni = self.storage.get_universities("uk")[0]

        # Generate dossier on reference date (simulating Day 1)
        dossier = self.synthesizer.synthesize(
            researcher=uk_prof,
            university=uk_uni,
            reference_date=date(2026, 9, 13)
        )

        assert dossier.metadata.eras_identified_count >= 2
        assert dossier.metadata.potential_directions_count >= 3
        assert dossier.suitability_score.composite_score > 0
        assert len(dossier.potential_directions) >= 3

    def test_no_hardcoded_professor_bias(self):
        """Verify that synthetic professor from a different country produces zero Hong Kong or Cao text."""
        synthetic_prof = ResearcherProfile(
            researcher_id="de_schmidt_klaus",
            name="Prof. Klaus Schmidt",
            university="Technical University of Munich",
            country="Germany",
            department="Department of Informatics",
            position="W3 Professor of Autonomous Distributed Systems",
            research_group="Decentralized Cloud Computing Group",
            official_profile_url="https://www.tum.de/faculty/klaus-schmidt",
            personal_website="https://www.in.tum.de/~schmidt",
            institutional_email="klaus.schmidt@tum.de",
            google_scholar="https://scholar.google.com/citations?user=kschmidt_tum",
            orcid="0000-0002-9876-5432",
            dblp="https://dblp.org/pid/s/KlausSchmidt.html",
            research_interests=["Serverless Computing", "Edge Cloud Offloading", "Edge AI Accelerators"],
            research_summary="Pioneering lightweight hypervisors and real-time execution frameworks for factory edge clusters.",
            edge_relevance="Direct focus on deterministic latency execution in industrial edge computing.",
            research_trajectory="Evolution from distributed real-time OS to hardware-assisted container virtualization at the edge.",
            current_projects=["BMBF Industrial Edge Automation", "DFG Resilient Micro-Clouds"],
            funding_projects=["BMBF Grant 2024-2028", "DFG Excellence Cluster"],
            research_methods=["Kernel BPF Tracing", "Microbenchmark Profiling", "Deterministic Scheduling"],
            systems_testbeds=["50-node Industrial ARM Edge Cluster", "FPGA Hardware In-The-Loop Rig"],
            potential_phd_topics=["Deterministic Micro-VM Dispatch over Heterogeneous Industrial Edge Nodes"],
            priority_tier="Tier 1",
            publications=[
                Publication(
                    publication_id="schmidt_2025",
                    title="Deterministic Micro-VM Scheduling for Industrial Edge Nodes",
                    authors=["Klaus Schmidt", "Stefan Weber"],
                    year=2025,
                    venue="ACM EuroSys",
                    doi_or_url="https://doi.org/10.1145/eurosys.2025.101",
                    research_problem="Unpredictable scheduling jitter in multi-tenant edge nodes.",
                    approach="BPF kernel runtime with sub-microsecond preemption.",
                    key_contribution="Reduced 99th percentile tail latency by 85%.",
                    edge_relevance="Directly targets hard real-time edge computing."
                ),
                Publication(
                    publication_id="schmidt_2018",
                    title="Real-Time Hypervisors for Critical Embedded Systems",
                    authors=["Klaus Schmidt", "Hans Meyer"],
                    year=2018,
                    venue="IEEE RTSS",
                    doi_or_url="https://doi.org/10.1109/rtss.2018.001",
                    research_problem="Shared memory bus contention in multicore automotive edge controllers.",
                    approach="Coloring memory partitions with hardware cache isolation.",
                    key_contribution="Zero bus contention for critical real-time tasks.",
                    edge_relevance="Foundational resource isolation for edge nodes."
                )
            ],
            alignment_score=94.5
        )

        synthetic_uni = UniversityProfile(
            university_id="tum",
            canonical_name="Technical University of Munich",
            country="Germany",
            country_code="DE",
            aliases=["TUM"],
            official_url="https://www.tum.de",
            graduate_school_url="https://www.gs.tum.de",
            research_url="https://www.tum.de/en/research",
            phd_application_url="https://www.tum.de/en/studies/degree-programs",
            funding_url="https://www.daad.de",
            relevant_departments=["Department of Informatics"],
            relevant_research_centres=["Munich Data Science Institute"]
        )

        dossier = self.synthesizer.synthesize(
            researcher=synthetic_prof,
            university=synthetic_uni
        )

        md = self.profiler.render_professor_dossier_markdown(dossier)

        # Confirm dynamically synthesized text
        assert "Prof. Klaus Schmidt" in md
        assert "Technical University of Munich" in md
        assert "Germany" in md
        assert "Deterministic Micro-VM Scheduling" in md

        # Confirm NO residual hardcoded Hong Kong / Cao data leaked in
        assert "Jiannong Cao" not in md
        assert "PolyU" not in md
        assert "IMCL" not in md
        assert "HKPFS" not in md
        assert "Hong Kong Polytechnic" not in md
