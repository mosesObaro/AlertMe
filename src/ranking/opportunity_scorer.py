"""Specialized multi-factor scoring and classification engine for PhD opportunities, scholarships, and researchers."""

import re
from typing import List, Dict, Any, Optional, Tuple
from src.models import (
    PhDOpportunity,
    ResearcherProfile,
    Scholarship,
    RecruitmentStatus,
    FundingStatus,
    DependantSupportClassification,
    InternationalEligibility
)
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger


class OpportunityScorer:
    """Evaluates and ranks PhD opportunities, recruiting researchers, and family scholarships."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.phd_config = self.config.phd_opportunities_config
        self.prefs = self.config.phd_opportunities_preferences
        self.target_countries = [c.get("name") if isinstance(c, dict) else c for c in self.phd_config.get("target_countries", [])]
        if not self.target_countries:
            self.target_countries = ["Germany", "Hong Kong", "Canada", "United Kingdom", "Japan", "United States"]

    # -------------------------------------------------------------------------
    # Classification Utilities
    # -------------------------------------------------------------------------

    def classify_recruitment_status(self, text: str) -> Tuple[str, str]:
        """Classifies text for PhD student recruitment evidence, returning (status, evidence_snippet)."""
        if not text:
            return RecruitmentStatus.NOT_VERIFIED.value, ""

        text_clean = " ".join(text.split())
        text_lower = text_clean.lower()

        # Check negative signals first (regex & keywords)
        neg_patterns = [
            r"not\s+(?:currently\s+)?(?:accepting|taking|recruiting)\s+(?:new\s+|any\s+)?(?:phd|doctoral|graduate)?\s*students",
            r"not\s+(?:accepting|taking)\s+(?:phd|doctoral)\s+applications",
            r"no\s+(?:open|available)?\s*(?:phd|doctoral)?\s*(?:positions|vacancies|openings|studentships)",
            r"(?:group|lab|team)\s+is\s+(?:currently\s+)?full",
            r"not\s+recruiting"
        ]
        for pat in neg_patterns:
            m = re.search(pat, text_lower)
            if m:
                start = max(0, m.start() - 20)
                end = min(len(text_clean), m.end() + 50)
                snippet = text_clean[start:end]
                return RecruitmentStatus.NOT_CURRENTLY_RECRUITING.value, f"...{snippet.strip()}..."

        neg_signals = self.phd_config.get("recruitment_keywords", {}).get("negative_signals", [
            "not accepting students", "not taking phd students", "not recruiting", "group is currently full"
        ])
        for neg in neg_signals:
            if neg in text_lower:
                idx = text_lower.find(neg)
                snippet = text_clean[max(0, idx - 20):min(len(text_clean), idx + len(neg) + 50)]
                return RecruitmentStatus.NOT_CURRENTLY_RECRUITING.value, f"...{snippet.strip()}..."

        # Check explicit active recruitment signals (regex & keywords)
        active_patterns = [
            r"(seeking|looking for|recruiting|accepting)\s+(?:[a-z\-]+\s+)?(?:phd|doctoral)\s+(students|applicants|candidates|applications)",
            r"(open|funded|available)\s+(?:phd|doctoral)\s+(positions|studentships|openings)",
            r"phd\s+studentships?\s+available",
            r"join\s+(?:my|our)\s+research\s+(?:group|lab|team)"
        ]
        for pat in active_patterns:
            m = re.search(pat, text_lower)
            if m:
                start = max(0, m.start() - 20)
                end = min(len(text_clean), m.end() + 50)
                snippet = text_clean[start:end]
                return RecruitmentStatus.ACTIVELY_RECRUITING.value, f"...{snippet.strip()}..."

        active_signals = self.phd_config.get("recruitment_keywords", {}).get("active_signals", [
            "seeking phd students", "looking for phd students", "accepting phd applications",
            "recruiting phd students", "open phd positions", "funded phd position available",
            "phd studentships available", "join my research group"
        ])
        for act in active_signals:
            if act in text_lower:
                idx = text_lower.find(act)
                snippet = text_clean[max(0, idx - 20):min(len(text_clean), idx + len(act) + 60)]
                return RecruitmentStatus.ACTIVELY_RECRUITING.value, f"...{snippet.strip()}..."

        # Check likely recruitment signals
        likely_patterns = [
            r"phd (openings|vacancies|positions)",
            r"(funded|fully funded) (studentship|phd|position)",
            r"prospective (students|applicants)"
        ]
        for pat in likely_patterns:
            m = re.search(pat, text_lower)
            if m:
                start = max(0, m.start() - 20)
                end = min(len(text_clean), m.end() + 50)
                snippet = text_clean[start:end]
                return RecruitmentStatus.LIKELY_RECRUITING.value, f"...{snippet.strip()}..."

        return RecruitmentStatus.NOT_VERIFIED.value, ""

    def classify_dependant_support(self, text: str, country: str = "") -> Tuple[str, str]:
        """Classifies dependant/family support into EXCELLENT, GOOD, PERMITTED, RESTRICTED, UNKNOWN."""
        text_lower = (text or "").lower()

        # 1. Check for dedicated financial or accommodation allowance (EXCELLENT)
        financial_keywords = self.phd_config.get("dependant_support_keywords", {}).get("financial_support", [
            "family allowance", "child allowance", "child supplement", "spouse allowance",
            "dependant allowance", "dependants allowance", "subsidized family housing", "family health insurance"
        ])
        for kw in financial_keywords:
            if kw in text_lower:
                return (
                    DependantSupportClassification.EXCELLENT.value,
                    f"Documented family financial support: '{kw}' specifically provided."
                )

        # 2. Check for explicit spouse work permit / high-stipend family living (GOOD)
        if "spouse open work permit" in text_lower or "spouse can work" in text_lower or (
            country.lower() in ["canada", "hong kong"] and ("fully funded" in text_lower or "high stipend" in text_lower)
        ):
            return (
                DependantSupportClassification.GOOD.value,
                "Dependants permitted under immigration law; funding is designed to support accompanying family."
            )

        # 3. Check for general legal eligibility (PERMITTED)
        # In target countries (DE, UK, CA, HK, JP, US), PhD researchers are legally permitted to bring dependants
        country_norm = country.strip().title()
        if country_norm in ["Germany", "Hong Kong", "Canada", "United Kingdom", "Japan", "United States", "Uk", "Usa"]:
            return (
                DependantSupportClassification.PERMITTED.value,
                f"Dependants permitted under {country_norm} doctoral student visa rules (standard single maintenance stipend)."
            )

        # 4. Check for explicit restriction
        if "dependants not permitted" in text_lower or "single students only" in text_lower or "no family visas" in text_lower:
            return (
                DependantSupportClassification.RESTRICTED.value,
                "Explicitly restricts or excludes accompanying dependants."
            )

        return (
            DependantSupportClassification.UNKNOWN.value,
            "No verified dependant policy documented."
        )

    def classify_funding_status(self, text: str) -> Tuple[str, str]:
        """Determines funding status from title/abstract/metadata."""
        t_low = (text or "").lower()
        if any(w in t_low for w in ["fully funded", "full funding", "tuition and stipend", "full scholarship", "fee waiver and stipend", "stipend + fees"]):
            return FundingStatus.FULLY_FUNDED.value, "Fully funded: Tuition fees and living stipend covered"
        elif any(w in t_low for w in ["partially funded", "tuition only", "fees only", "partial scholarship", "half fee"]):
            return FundingStatus.PARTIALLY_FUNDED.value, "Partially funded: Partial fees or living allowance"
        elif any(w in t_low for w in ["self funded", "self-funded", "no funding"]):
            return FundingStatus.SELF_FUNDED.value, "Self-funded position"
        return FundingStatus.UNKNOWN.value, "Funding status to be confirmed with supervisor/department"

    # -------------------------------------------------------------------------
    # Scoring Engines
    # -------------------------------------------------------------------------

    def score_opportunity(self, opp: PhDOpportunity) -> PhDOpportunity:
        """Computes multi-factor scores and explainability reasons for a PhD Opportunity."""
        reasons = []

        # 1. Research Fit (0 - 10.0)
        fit_score, fit_reasons = self._compute_research_fit(opp.title, opp.eligibility, opp.research_areas)
        opp.relevance_score = fit_score
        reasons.extend(fit_reasons)

        # 2. Recruitment Status Score (0 - 10.0)
        rec_score, rec_reasons = self._compute_recruitment_score(opp.recruitment_status, opp.recruitment_evidence)
        opp.supervisor_fit_score = rec_score
        reasons.extend(rec_reasons)

        # 3. Funding Score (0 - 10.0)
        fund_score, fund_reasons = self._compute_funding_score(opp.funding_status, opp.funding_amount)
        opp.funding_score = fund_score
        reasons.extend(fund_reasons)

        # 4. Country Match Score (0 - 10.0)
        cntry_score, cntry_reasons = self._compute_country_score(opp.country)
        opp.country_score = cntry_score
        reasons.extend(cntry_reasons)

        # 5. Dependant Support Score (0 - 10.0)
        dep_score, dep_reasons = self._compute_dependant_score(opp.dependant_support_classification)
        opp.dependant_support_score = dep_score
        reasons.extend(dep_reasons)

        # 6. Composite Score (0 - 10.0)
        # Weights: Research Fit 35%, Recruitment 20%, Funding 20%, Dependant 15%, Country 10%
        composite = (
            (fit_score * 0.35) +
            (rec_score * 0.20) +
            (fund_score * 0.20) +
            (dep_score * 0.15) +
            (cntry_score * 0.10)
        )
        opp.composite_score = round(min(10.0, max(0.0, composite)), 1)
        opp.reasons = reasons

        return opp

    def score_researcher(self, prof: ResearcherProfile) -> ResearcherProfile:
        """Scores a researcher combining Academic Impact & Verified Recruitment Evidence."""
        reasons = []

        # 1. Academic Research Fit (0 - 10.0)
        fit_score, fit_reasons = self._compute_research_fit(
            prof.name + " " + " ".join(prof.research_areas),
            " ".join([p.get("title", "") for p in prof.recent_papers]),
            prof.research_areas
        )
        prof.academic_fit_score = fit_score
        reasons.extend([f"Academic Fit: {r}" for r in fit_reasons])

        # 2. Activity & Venue Impact (0 - 10.0)
        activity_score = 5.0
        if prof.publication_count >= 5:
            activity_score = 9.0
            reasons.append(f"✓ Strong publication volume: {prof.publication_count}+ papers in target area")
        elif prof.publication_count >= 2:
            activity_score = 7.5
            reasons.append(f"✓ Active recent publication record ({prof.publication_count} papers)")
        if prof.h_index and prof.h_index >= 15:
            activity_score = min(10.0, activity_score + 1.0)
            reasons.append(f"✓ Established academic standing (h-index: {prof.h_index})")

        # 3. Recruitment Verification Signal (0 - 10.0)
        rec_score, rec_reasons = self._compute_recruitment_score(prof.recruitment_status, prof.recruitment_evidence)
        reasons.extend(rec_reasons)

        # 4. Country Match (0 - 10.0)
        cntry_score, cntry_reasons = self._compute_country_score(prof.country)
        reasons.extend(cntry_reasons)

        # Composite Researcher Recommendation:
        # If actively recruiting, heavily boosted. If NOT recruiting, penalized.
        if prof.recruitment_status == RecruitmentStatus.NOT_CURRENTLY_RECRUITING.value:
            composite = fit_score * 0.4 + activity_score * 0.3
        else:
            composite = (fit_score * 0.35) + (activity_score * 0.25) + (rec_score * 0.30) + (cntry_score * 0.10)

        prof.composite_score = round(min(10.0, max(0.0, composite)), 1)
        prof.reasons = reasons

        return prof

    def score_scholarship(self, sch: Scholarship) -> Scholarship:
        """Scores a scholarship focusing on financial coverage, dependant support, and target country."""
        reasons = []
        score = 0.0

        # Dependant Support Rating
        dep_score, dep_reasons = self._compute_dependant_score(sch.dependant_support_classification)
        score += dep_score * 0.40
        reasons.extend(dep_reasons)

        # Target Country
        cntry_score, cntry_reasons = self._compute_country_score(sch.country)
        score += cntry_score * 0.25
        reasons.extend(cntry_reasons)

        # Financial Generosity
        fund_text = f"{sch.tuition_coverage} {sch.stipend_amount} {sch.funding_type}".lower()
        if "full" in fund_text or "€1" in fund_text or "£1" in fund_text or "£2" in fund_text or "cad" in fund_text or "hk$" in fund_text:
            score += 3.5
            reasons.append("✓ Generous international living stipend + tuition waiver")
        else:
            score += 2.0

        sch.score = round(min(10.0, max(0.0, score)), 1)
        sch.reasons = reasons
        return sch

    # -------------------------------------------------------------------------
    # Factor Evaluators
    # -------------------------------------------------------------------------

    def _compute_research_fit(self, title: str, text: str, areas: List[str]) -> Tuple[float, List[str]]:
        reasons = []
        combined = f"{title} {text} {' '.join(areas)}".lower()

        core_topics = [
            "edge computing", "edge intelligence", "edge ai", "distributed systems",
            "mobile edge computing", "fog computing", "computation offloading",
            "federated learning", "internet of things", "iot", "tinyml"
        ]
        matched_core = [t for t in core_topics if t in combined]

        learning_topics = self.config.learning_stage.get("current_topics", [])
        matched_stage = [t for t in learning_topics if t.lower() in combined]

        score = 5.0
        if matched_core:
            score = 8.0 + min(1.5, len(matched_core) * 0.5)
            reasons.append(f"✓ Strong Edge Computing research fit: {', '.join(matched_core[:3])}")
        else:
            reasons.append("• General computer science / systems research area")

        if matched_stage:
            score = min(10.0, score + 0.8)
            reasons.append(f"✓ Direct alignment with active learning stage: {', '.join(matched_stage)}")

        return min(10.0, score), reasons

    def _compute_recruitment_score(self, status: str, evidence: str) -> Tuple[float, List[str]]:
        reasons = []
        if status == RecruitmentStatus.ACTIVELY_RECRUITING.value:
            snippet = f" (\"{evidence[:45]}...\")" if evidence else ""
            reasons.append(f"✓ Actively recruiting PhD students{snippet}")
            return 10.0, reasons
        elif status == RecruitmentStatus.LIKELY_RECRUITING.value:
            reasons.append("✓ Strong recruitment indicators: Recently advertised opening or grant project")
            return 7.5, reasons
        elif status == RecruitmentStatus.NOT_VERIFIED.value:
            reasons.append("• Active researcher in target field; current recruitment status pending lab confirmation")
            return 4.5, reasons
        else:
            reasons.append("⚠ Stated as not currently accepting new students")
            return 0.0, reasons

    def _compute_funding_score(self, status: str, amount: str) -> Tuple[float, List[str]]:
        reasons = []
        if status == FundingStatus.FULLY_FUNDED.value:
            details = f" ({amount})" if amount else ""
            reasons.append(f"✓ Fully funded: Tuition waiver and living maintenance stipend included{details}")
            return 10.0, reasons
        elif status == FundingStatus.PARTIALLY_FUNDED.value:
            reasons.append("• Partially funded: Requires supplementary funding or tuition top-up")
            return 5.0, reasons
        else:
            reasons.append("• Funding terms unspecified; applicant should confirm institutional bursary")
            return 3.0, reasons

    def _compute_country_score(self, country: str) -> Tuple[float, List[str]]:
        reasons = []
        cntry_norm = country.strip().title()
        if cntry_norm in [c.title() for c in self.target_countries]:
            reasons.append(f"✓ Target country priority: {cntry_norm}")
            return 10.0, reasons
        elif country:
            reasons.append(f"• Location: {cntry_norm} (Outside primary 6 target countries)")
            return 4.0, reasons
        return 5.0, ["• Location to be determined"]

    def _compute_dependant_score(self, classification: str) -> Tuple[float, List[str]]:
        reasons = []
        if classification in [DependantSupportClassification.EXCELLENT.value, "financially_supported", "excellent"]:
            reasons.append("✓ High Dependant Support: Family financial allowance or subsidized housing documented")
            return 10.0, reasons
        elif classification == DependantSupportClassification.GOOD.value:
            reasons.append("✓ Dependant Friendly: Dependants legally permitted; generous stipend calibrated for international living")
            return 8.0, reasons
        elif classification == DependantSupportClassification.PERMITTED.value:
            reasons.append("• Dependants Permitted: Accompanying dependants allowed under student visa rules; funding covers single student")
            return 5.5, reasons
        elif classification == DependantSupportClassification.RESTRICTED.value:
            reasons.append("⚠ Dependant Restricted: Accompanying dependants officially limited or restricted")
            return 0.0, reasons
        else:
            reasons.append("• Dependant status unverified; check host country immigration guidance before applying")
            return 3.5, reasons
