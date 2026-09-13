"""
Data persistence and storage manager for the Hong Kong PhD Supervisor Intelligence module.
Handles loading authoritative seed data, managing familiarity states, recording alert history,
and verifying data freshness.
"""

import os
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from .models import (
    UniversityProfile, ResearcherProfile, Publication,
    Scholarship, Opportunity, FamiliarityRecord, DailyAlert, RecruitmentEvidence
)
from .config import RECRUITMENT_FRESHNESS_DAYS

class StorageManager:
    """Manages persistence, seed data loading, and state tracking."""
    
    def __init__(self, data_dir: Optional[str] = None, state_file: Optional[str] = None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir
            
        if state_file is None:
            self.state_file = os.path.join(self.data_dir, "state.json")
        else:
            self.state_file = state_file
            
        self.universities: Dict[str, UniversityProfile] = {}
        self.publications: Dict[str, Publication] = {}
        self.researchers: Dict[str, ResearcherProfile] = {}
        self.scholarships: Dict[str, Scholarship] = {}
        self.familiarity: Dict[str, FamiliarityRecord] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.campaign_state: Dict[str, Any] = {}
        
        self.load_all()

    def load_all(self):
        """Loads all static seed records and dynamic runtime state."""
        self._load_universities()
        self._load_publications()
        self._load_scholarships()
        self._load_researchers()
        self._load_state()

    def _load_universities(self):
        filepath = os.path.join(self.data_dir, "universities.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    u = UniversityProfile.from_dict(item)
                    self.universities[u.university_id] = u

    def _load_publications(self):
        filepath = os.path.join(self.data_dir, "publications.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    p = Publication.from_dict(item)
                    self.publications[p.publication_id] = p

    def _load_scholarships(self):
        filepath = os.path.join(self.data_dir, "scholarships.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    s = Scholarship.from_dict(item)
                    self.scholarships[s.scholarship_id] = s

    def _load_researchers(self):
        filepath = os.path.join(self.data_dir, "researchers.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    r = ResearcherProfile.from_dict(item)
                    # Resolve publication IDs to Publication objects if needed
                    resolved_pubs = []
                    for pub in r.publications:
                        if isinstance(pub, str) and pub in self.publications:
                            resolved_pubs.append(self.publications[pub])
                        elif isinstance(pub, Publication):
                            resolved_pubs.append(pub)
                    r.publications = resolved_pubs
                    self.researchers[r.researcher_id] = r

    def _load_state(self):
        """Loads familiarity, alert history, and campaign state."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.alert_history = state.get("alert_history", [])
                    self.campaign_state = state.get("campaign_state", {})
                    fam_data = state.get("familiarity", {})
                    for r_id, f_dict in fam_data.items():
                        self.familiarity[r_id] = FamiliarityRecord.from_dict(f_dict)
            except Exception as e:
                print(f"Warning: Could not load state file ({e}). Starting with fresh state.")
                
        # Initialize missing familiarity records for all researchers
        for r_id in self.researchers:
            if r_id not in self.familiarity:
                self.familiarity[r_id] = FamiliarityRecord(researcher_id=r_id)

    def save_state(self):
        """Saves dynamic runtime state (familiarity, alert logs, campaign progress)."""
        state = {
            "last_updated": datetime.now().isoformat(),
            "familiarity": {r_id: rec.to_dict() for r_id, rec in self.familiarity.items()},
            "alert_history": self.alert_history,
            "campaign_state": self.campaign_state
        }
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def is_recruitment_stale(self, evidence: RecruitmentEvidence, reference_date: Optional[date] = None) -> bool:
        """Enforces the 12-month freshness window rule for recruitment evidence."""
        if reference_date is None:
            ref = date.today()
        else:
            ref = reference_date
            
        try:
            ev_date = datetime.strptime(evidence.source_date, "%Y-%m-%d").date()
            delta = (ref - ev_date).days
            return delta > RECRUITMENT_FRESHNESS_DAYS
        except Exception:
            return True

    def record_alert(self, alert: DailyAlert):
        """Records a daily alert to history to prevent duplicate exposures."""
        alert_dict = alert.to_dict()
        self.alert_history.append(alert_dict)
        
        # Advance familiarity for the researcher
        r_id = alert.alert_id.split("_")[0] if "_" in alert.alert_id else None
        # Locate researcher by name or ID
        for rid, r in self.researchers.items():
            if r.name == alert.professor or rid == r_id:
                rec = self.familiarity.get(rid, FamiliarityRecord(researcher_id=rid))
                rec.last_exposed = alert.date
                rec.exposure_cycle_day = (rec.exposure_cycle_day % 7) + 1
                if alert.paper_title not in rec.papers_exposed:
                    rec.papers_exposed.append(alert.paper_title)
                self.familiarity[rid] = rec
                break
                
        self.save_state()

    def has_recent_alert_for_paper(self, paper_title: str, days_window: int = 14) -> bool:
        """Suppresses duplicate alerts for the same paper within a spaced window."""
        today = date.today()
        for past_alert in reversed(self.alert_history):
            if past_alert.get("paper_title") == paper_title:
                try:
                    past_date = datetime.strptime(past_alert.get("date", ""), "%Y-%m-%d").date()
                    if (today - past_date).days < days_window:
                        return True
                except Exception:
                    continue
        return False
