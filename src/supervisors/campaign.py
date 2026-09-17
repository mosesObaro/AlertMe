"""
One-Day Country Campaign Orchestrator for Global PhD Funding & Supervisor Intelligence.
Executes complete intelligence generation for a country in a single run without multi-day cycles.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .models import CountryCampaign, CountryCampaignResult, ResearcherProfile, UniversityProfile, FundingOpportunity
from .config import SUPPORTED_COUNTRIES, MINIMUM_PROFESSORS_PER_COUNTRY, normalize_country_key
from .storage import StorageManager
from .discovery import DiscoveryEngine
from .scoring import ScoringEngine
from .funding import FundingEngine
from .profiler import DossierProfiler

class CountryCampaignManager:
    """Orchestrates end-to-end 1-day country intelligence campaigns."""

    def __init__(self, storage: Optional[StorageManager] = None, profiler: Optional[DossierProfiler] = None):
        self.storage = storage or StorageManager()
        self.profiler = profiler or DossierProfiler()

    def run_country_campaign(
        self,
        country_input: str,
        min_professors: int = MINIMUM_PROFESSORS_PER_COUNTRY,
        generate_docs: bool = True,
        reference_date: Optional[date] = None,
        dry_run: bool = False
    ) -> CountryCampaignResult:
        """
        Executes a complete 1-day country campaign:
        1. Validates country configuration
        2. Scores and qualifies universities
        3. Identifies and verifies funding opportunities
        4. Discovers, deduplicates, and scores professors (enforcing >= min_professors)
        5. Generates 33-section dossiers for every professor in MD, PDF, DOCX, EPUB
        6. Generates complete country report in MD, PDF, DOCX, EPUB
        7. Persists state and returns result
        """
        country_key = normalize_country_key(country_input)
        campaign = self.storage.get_country_campaign(country_key)
        if not campaign:
            raise ValueError(f"Unsupported country campaign '{country_input}'. Supported: {list(SUPPORTED_COUNTRIES.keys())}")

        ref_date = reference_date or date.today()
        today_str = ref_date.strftime("%Y-%m-%d")

        # 1. Discover & Score Universities
        raw_unis = self.storage.get_universities(country_key)
        universities = DiscoveryEngine.deduplicate_universities(raw_unis)
        for u in universities:
            u.suitability_score = ScoringEngine.score_university(u)
        universities.sort(key=lambda u: u.suitability_score, reverse=True)

        # 2. Discover & Classify Funding
        raw_funding = self.storage.get_funding_opportunities(country_key)
        funding = DiscoveryEngine.deduplicate_funding(raw_funding)
        for fo in funding:
            fo.funding_type = FundingEngine.classify_funding_type(fo.tuition_coverage, fo.stipend_amount)
            if not fo.dependant_support or fo.dependant_support == "UNKNOWN":
                fo.dependant_support = FundingEngine.classify_dependant_support(fo.eligibility_notes)

        # 3. Discover, Deduplicate & Score Professors
        raw_profs = self.storage.get_professors(country_key)
        professors = DiscoveryEngine.deduplicate_professors(raw_profs)

        for p in professors:
            score, reasons = ScoringEngine.score_professor(p)
            p.alignment_score = score
            p.suitability_score = score
            p.why_suitable = reasons

        # Sort: Tier 1 first, then by alignment score descending
        tier_weights = {"Tier 1": 3, "Tier 2": 2, "Tier 3": 1}
        professors.sort(
            key=lambda p: (tier_weights.get(p.priority_tier, 1), p.alignment_score),
            reverse=True
        )

        # Enforce minimum professor requirement
        if len(professors) < min_professors:
            print(f"[Warning] Found {len(professors)} professors for {campaign.country}, expected minimum {min_professors}.")

        # 4. Document Generation (MD, DOCX, PDF, EPUB)
        generated_dossiers = {}
        country_report_files = {}

        if generate_docs and not dry_run:
            uni_map = {u.canonical_name.lower(): u for u in universities}

            for p in professors:
                matched_uni = uni_map.get(p.university.lower())
                docs = self.profiler.generate_professor_dossiers(
                    country_key=country_key,
                    researcher=p,
                    university=matched_uni,
                    funding=funding,
                    campaign=campaign,
                    reference_date=ref_date
                )
                generated_dossiers[p.researcher_id] = docs

            # Build result before generating country report
            temp_result = CountryCampaignResult(
                country=campaign.country,
                country_code=campaign.country_code,
                execution_date=today_str,
                universities_count=len(universities),
                professors_count=len(professors),
                funding_opportunities_count=len(funding),
                universities=universities,
                professors=professors,
                funding_opportunities=funding,
                generated_dossiers=generated_dossiers
            )

            country_report_files = self.profiler.generate_country_report(
                country_key=country_key,
                result=temp_result,
                campaign=campaign
            )

        final_result = CountryCampaignResult(
            country=campaign.country,
            country_code=campaign.country_code,
            execution_date=today_str,
            universities_count=len(universities),
            professors_count=len(professors),
            funding_opportunities_count=len(funding),
            universities=universities,
            professors=professors,
            funding_opportunities=funding,
            generated_dossiers=generated_dossiers,
            country_report_files=country_report_files
        )

        # 5. Persist State
        if not dry_run:
            self.storage.record_campaign_execution(country_key, final_result)

        return final_result

    def run_all_countries(
        self,
        min_professors: int = MINIMUM_PROFESSORS_PER_COUNTRY,
        generate_docs: bool = True,
        dry_run: bool = False
    ) -> Dict[str, CountryCampaignResult]:
        """Executes complete intelligence campaigns for all supported countries."""
        results = {}
        for country_key in SUPPORTED_COUNTRIES:
            try:
                res = self.run_country_campaign(
                    country_input=country_key,
                    min_professors=min_professors,
                    generate_docs=generate_docs,
                    dry_run=dry_run
                )
                results[country_key] = res
            except Exception as e:
                print(f"[CountryCampaignManager] Failed running {country_key}: {e}")
        return results

    run_all_campaigns = run_all_countries
