"""
Funding Intelligence & Classification Engine for Country-Based PhD Systems.
Evaluates doctoral funding types, international student eligibility, dependant support,
and application deadlines with evidence-based criteria.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime, date
from .models import FundingOpportunity

class FundingEngine:
    """Classifies and verifies funding opportunities across countries."""

    @staticmethod
    def classify_funding_type(tuition_coverage: str, stipend_amount: str) -> str:
        """
        Classifies funding as FULLY_FUNDED, PARTIALLY_FUNDED, TUITION_ONLY, STIPEND_ONLY, or UNKNOWN.
        Strictly requires evidence of both tuition and stipend for FULLY_FUNDED.
        """
        t_lower = tuition_coverage.lower() if tuition_coverage else ""
        s_lower = stipend_amount.lower() if stipend_amount else ""

        has_full_tuition = any(kw in t_lower for kw in [
            "full", "100%", "waived", "waiver", "zero tuition", "covered", "free tuition"
        ])
        has_stipend = any(kw in s_lower for kw in [
            "/year", "/yr", "/month", "/mo", "sek/month", "jpy/month", "gbp", "cad", "eur", "usd", "hk$", "stipend", "salary"
        ])

        if has_full_tuition and has_stipend:
            return "FULLY_FUNDED"
        elif has_full_tuition and not has_stipend:
            return "TUITION_ONLY"
        elif not has_full_tuition and has_stipend:
            return "STIPEND_ONLY"
        elif "partial" in t_lower or "partial" in s_lower:
            return "PARTIALLY_FUNDED"
        else:
            return "UNKNOWN"

    @staticmethod
    def classify_dependant_support(details: str) -> str:
        """Classifies dependant support as EXCELLENT, GOOD, PERMITTED, or UNKNOWN."""
        if not details:
            return "UNKNOWN"
        d_lower = details.lower()
        if any(kw in d_lower for kw in ["family allowance", "child allowance", "child supplement", "spouse allowance", "family housing"]):
            return "EXCELLENT"
        elif any(kw in d_lower for kw in ["open work permit", "sowp", "right to work", "right to reside", "dependant visa"]):
            return "GOOD"
        elif any(kw in d_lower for kw in ["permitted", "eligible", "f-2", "j-2", "kazoku"]):
            return "PERMITTED"
        return "UNKNOWN"

    @staticmethod
    def is_opportunity_current(deadline: str, reference_date: Optional[date] = None) -> bool:
        """Checks if a deadline has not yet passed."""
        if not deadline or deadline.lower() in ["continuous", "rolling", "varies"]:
            return True
        ref_date = reference_date or date.today()
        try:
            d_obj = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
            return d_obj >= ref_date
        except Exception:
            return True
