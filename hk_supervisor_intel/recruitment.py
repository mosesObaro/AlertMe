"""
Recruitment verification and classification engine for the Hong Kong PhD Supervisor Intelligence module.
Provides evidence-based classification of PhD recruitment availability and enforces the 12-month freshness window.
"""

from datetime import datetime, date
from typing import Optional, Tuple
from .models import RecruitmentEvidence
from .config import RECRUITMENT_FRESHNESS_DAYS

class RecruitmentEngine:
    """Verifies and classifies PhD recruitment statuses with zero fabrication."""

    @staticmethod
    def classify_recruitment_evidence(
        evidence_text: str,
        source_url: str,
        source_type: str,
        source_date: str,
        reference_date: Optional[date] = None
    ) -> RecruitmentEvidence:
        """
        Classifies recruitment status based on dated text evidence and source authority.
        Enforces a 12-month freshness expiry window.
        """
        if reference_date is None:
            ref_date = date.today()
        else:
            ref_date = reference_date

        text_lower = evidence_text.lower() if evidence_text else ""
        
        # Check date freshness first
        try:
            ev_date = datetime.strptime(source_date, "%Y-%m-%d").date()
            is_stale = (ref_date - ev_date).days > RECRUITMENT_FRESHNESS_DAYS
        except Exception:
            is_stale = True

        # Check explicit negative
        if any(neg in text_lower for neg in [
            "not accepting", "no openings", "lab is full", "not taking new students", "no positions"
        ]):
            status = "NOT_CURRENTLY_RECRUITING"
            confidence = 0.95
        # Check confirmed active
        elif any(act in text_lower for act in [
            "phd students wanted", "phd positions available", "seeking highly motivated phd",
            "openings for phd", "recruiting phd", "looking for phd students", "fall 2027", "2027 entry"
        ]):
            status = "RECRUITMENT_STALE" if is_stale else "CONFIRMED_ACTIVE"
            confidence = 0.60 if is_stale else 0.95
        # Check strong evidence
        elif any(str_ev in text_lower for str_ev in [
            "accepting phd", "prospective phd students", "funded phd", "research assistant / phd",
            "hkpfs applicants", "studentships available", "please submit your application"
        ]):
            status = "RECRUITMENT_STALE" if is_stale else "STRONG_EVIDENCE"
            confidence = 0.50 if is_stale else 0.85
        # Check possible
        elif any(pos in text_lower for pos in [
            "prospective students", "join our group", "interested in research", "contact me"
        ]):
            status = "RECRUITMENT_STALE" if is_stale else "POSSIBLE"
            confidence = 0.40 if is_stale else 0.70
        else:
            status = "UNKNOWN"
            confidence = 0.20

        return RecruitmentEvidence(
            status=status,
            confidence=confidence,
            evidence_text=evidence_text,
            source_url=source_url,
            source_type=source_type,
            source_date=source_date,
            last_verified=ref_date.strftime("%Y-%m-%d")
        )

    @classmethod
    def get_recruitment_score(cls, evidence: RecruitmentEvidence, reference_date: Optional[date] = None) -> float:
        """
        Converts recruitment status into a numerical score (0.0 to 100.0)
        for composite opportunity ranking.
        """
        if reference_date is None:
            ref_date = date.today()
        else:
            ref_date = reference_date

        try:
            ev_date = datetime.strptime(evidence.source_date, "%Y-%m-%d").date()
            if (ref_date - ev_date).days > RECRUITMENT_FRESHNESS_DAYS:
                return 40.0 * evidence.confidence  # Penalty for stale evidence
        except Exception:
            return 30.0

        score_map = {
            "CONFIRMED_ACTIVE": 100.0,
            "STRONG_EVIDENCE": 85.0,
            "POSSIBLE": 60.0,
            "UNKNOWN": 30.0,
            "RECRUITMENT_STALE": 40.0,
            "NOT_CURRENTLY_RECRUITING": 0.0
        }

        base = score_map.get(evidence.status, 30.0)
        return base * evidence.confidence
