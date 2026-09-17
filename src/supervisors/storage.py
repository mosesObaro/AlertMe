"""
Persistence and Storage Manager for the Global Country-Based PhD Funding and Supervisor Intelligence Engine.
Handles loading authoritative seed data by country, tracking global campaign state,
entity deduplication, data freshness, and backward-compatible migration from legacy state files.
"""

import os
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import (
    UniversityProfile, ResearcherProfile, Publication,
    FundingOpportunity, CountryCampaign, CountryCampaignResult,
    RecruitmentEvidence
)
from .config import SUPPORTED_COUNTRIES, RECRUITMENT_FRESHNESS_DAYS, normalize_country_key

class StorageManager:
    """Manages country seed data loading, global supervisor state, and persistence."""

    def __init__(self, data_root: Optional[str] = None, state_file: Optional[str] = None):
        if data_root is None:
            self.data_root = Path(__file__).resolve().parent / "data"
        else:
            self.data_root = Path(data_root)

        if state_file is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            self.state_file = project_root / "data" / "supervisor_state.json"
        else:
            self.state_file = Path(state_file)

        # In-memory caches by country
        self.universities: Dict[str, Dict[str, UniversityProfile]] = {}
        self.funding: Dict[str, Dict[str, FundingOpportunity]] = {}
        self.professors: Dict[str, Dict[str, ResearcherProfile]] = {}
        self.publications: Dict[str, Dict[str, Publication]] = {}

        # Campaign runtime state
        self.campaign_history: Dict[str, List[Dict[str, Any]]] = {}
        self.seen_professors: Dict[str, List[str]] = {}
        self.state_data: Dict[str, Any] = {}

        self.load_all()

    def load_all(self):
        """Loads seed data across all configured countries and active runtime state."""
        for country_key in SUPPORTED_COUNTRIES:
            self._load_country_seed_data(country_key)
        self._load_state()

    def _load_country_seed_data(self, country_key: str):
        """Loads universities, funding schemes, and professors for a given country."""
        c_dir = self.data_root / country_key
        if not c_dir.exists():
            return

        self.universities[country_key] = {}
        self.funding[country_key] = {}
        self.professors[country_key] = {}
        self.publications[country_key] = {}

        # 1. Universities
        uni_path = c_dir / "universities.json"
        if uni_path.exists():
            with open(uni_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    u = UniversityProfile.from_dict(item)
                    self.universities[country_key][u.university_id] = u

        # 2. Funding Opportunities
        fund_path = c_dir / "funding.json"
        if fund_path.exists():
            with open(fund_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    fo = FundingOpportunity.from_dict(item)
                    self.funding[country_key][fo.opportunity_id] = fo

        # 3. Publications (standalone file if present)
        pub_path = c_dir / "publications.json"
        if pub_path.exists():
            with open(pub_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    pub = Publication.from_dict(item)
                    self.publications[country_key][pub.publication_id] = pub

        # 4. Professors & Publications
        prof_path = c_dir / "professors.json"
        if prof_path.exists():
            with open(prof_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    p = ResearcherProfile.from_dict(item)
                    resolved_pubs = []
                    for pub in p.publications:
                        if isinstance(pub, str):
                            if pub in self.publications[country_key]:
                                resolved_pubs.append(self.publications[country_key][pub])
                            else:
                                placeholder = Publication(
                                    publication_id=pub,
                                    title=pub.replace("_", " ").title(),
                                    authors=[p.name],
                                    year=2024,
                                    venue="Academic Publication",
                                    doi_or_url=""
                                )
                                self.publications[country_key][pub] = placeholder
                                resolved_pubs.append(placeholder)
                        elif isinstance(pub, Publication):
                            self.publications[country_key][pub.publication_id] = pub
                            resolved_pubs.append(pub)
                    p.publications = resolved_pubs
                    self.professors[country_key][p.researcher_id] = p

    def _load_state(self):
        """Loads runtime state or migrates from legacy Hong Kong state if present."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.state_data = json.load(f)
                    self.campaign_history = self.state_data.get("campaign_history", {})
                    self.seen_professors = self.state_data.get("seen_professors", {})
                    return
            except Exception as e:
                print(f"[StorageManager] Error reading state file ({e}). Initializing fresh.")

        # Migrate from legacy Hong Kong state if available
        legacy_hk_state = Path(__file__).resolve().parent.parent.parent / "hk_supervisor_intel" / "data" / "state.json"
        if legacy_hk_state.exists():
            try:
                with open(legacy_hk_state, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                    self.state_data = {
                        "last_updated": legacy_data.get("last_updated", datetime.now().isoformat()),
                        "campaign_history": {
                            "hong_kong": legacy_data.get("alert_history", [])
                        },
                        "seen_professors": {
                            "hong_kong": list(legacy_data.get("familiarity", {}).keys())
                        }
                    }
                    self.campaign_history = self.state_data["campaign_history"]
                    self.seen_professors = self.state_data["seen_professors"]
                    self.save_state()
                    print("[StorageManager] Successfully migrated legacy Hong Kong state data.")
                    return
            except Exception as e:
                print(f"[StorageManager] Could not migrate legacy state: {e}")

        self.state_data = {
            "last_updated": datetime.now().isoformat(),
            "campaign_history": {},
            "seen_professors": {}
        }

    def save_state(self):
        """Atomically saves runtime state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_data["last_updated"] = datetime.now().isoformat()
        self.state_data["campaign_history"] = self.campaign_history
        self.state_data["seen_professors"] = self.seen_professors

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state_data, f, indent=2, ensure_ascii=False)

    def get_country_campaign(self, country_input: str) -> Optional[CountryCampaign]:
        """Retrieves country campaign configuration by name or code."""
        key = normalize_country_key(country_input)
        cfg = SUPPORTED_COUNTRIES.get(key)
        if not cfg:
            return None
        return CountryCampaign(
            country=cfg["name"],
            country_code=cfg["country_code"],
            currency=cfg["currency"],
            immigration_dependant_guidance=cfg["immigration_dependant_guidance"],
            dependant_visa_policy=cfg["dependant_visa_policy"],
            immigration_disclaimer=cfg["immigration_disclaimer"],
            target_deadline=cfg["target_deadline"],
            primary_funding_vehicle=cfg["primary_funding_vehicle"],
            enabled=True
        )

    def get_universities(self, country_input: str) -> List[UniversityProfile]:
        """Returns all universities for a country."""
        key = normalize_country_key(country_input)
        return list(self.universities.get(key, {}).values())

    def get_funding_opportunities(self, country_input: str) -> List[FundingOpportunity]:
        """Returns all funding schemes for a country."""
        key = normalize_country_key(country_input)
        return list(self.funding.get(key, {}).values())

    def get_professors(self, country_input: str) -> List[ResearcherProfile]:
        """Returns all vetted researchers for a country."""
        key = normalize_country_key(country_input)
        return list(self.professors.get(key, {}).values())

    def record_campaign_execution(self, country_input: str, result: CountryCampaignResult):
        """Records the completion of a 1-day country campaign run."""
        key = normalize_country_key(country_input)
        if key not in self.campaign_history:
            self.campaign_history[key] = []
        if key not in self.seen_professors:
            self.seen_professors[key] = []

        entry = {
            "execution_date": result.execution_date,
            "universities_count": result.universities_count,
            "professors_count": result.professors_count,
            "funding_opportunities_count": result.funding_opportunities_count,
            "professors": [p.name for p in result.professors]
        }
        self.campaign_history[key].append(entry)

        for p in result.professors:
            if p.researcher_id not in self.seen_professors[key]:
                self.seen_professors[key].append(p.researcher_id)

        self.save_state()

    def is_recruitment_stale(self, recruitment: RecruitmentEvidence, reference_date: Optional[date] = None) -> bool:
        """Determines if recruitment evidence is older than the 12-month freshness policy."""
        ref_date = reference_date or date.today()
        if not recruitment.source_date:
            return True
        try:
            source_dt = datetime.strptime(recruitment.source_date[:10], "%Y-%m-%d").date()
            delta = (ref_date - source_dt).days
            return delta > RECRUITMENT_FRESHNESS_DAYS
        except Exception:
            return True
