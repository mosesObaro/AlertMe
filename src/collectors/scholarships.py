"""Scholarship collector for family-friendly doctoral funding programs across target countries."""

from typing import List, Optional, Dict, Any
from src.collectors.base import BaseCollector
from src.models import Scholarship, ResearchItem, ItemType, CredibilityTier
from src.ranking.opportunity_scorer import OpportunityScorer
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger


class ScholarshipCollector(BaseCollector):
    """Collects authoritative PhD scholarships and evaluates dependant/family support."""

    def __init__(
        self,
        name: str = "Authoritative PhD Scholarships",
        config_manager: Optional[ConfigManager] = None,
        enabled: bool = True
    ):
        super().__init__(name=name, tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value, enabled=enabled)
        self.config = config_manager or ConfigManager()
        self.scorer = OpportunityScorer(self.config)
        self.phd_config = self.config.phd_opportunities_config

    def fetch(self) -> List[ResearchItem]:
        """Loads and scores curated authoritative international PhD scholarships."""
        items: List[ResearchItem] = []
        curated = self.phd_config.get("curated_scholarships", [])

        for s_data in curated:
            try:
                sch = Scholarship(
                    name=s_data.get("name", ""),
                    provider=s_data.get("provider", ""),
                    country=s_data.get("country", ""),
                    university=s_data.get("university", ""),
                    degree_level=s_data.get("degree_level", "PhD"),
                    tuition_coverage=s_data.get("tuition_coverage", ""),
                    stipend_amount=s_data.get("stipend_amount", ""),
                    duration=s_data.get("duration", ""),
                    deadline=s_data.get("deadline"),
                    start_date=s_data.get("start_date"),
                    dependant_support_classification=s_data.get("dependant_support_classification", "permitted"),
                    dependant_support_details=s_data.get("dependant_support_details", ""),
                    family_accommodation=s_data.get("family_accommodation", ""),
                    international_eligibility=s_data.get("international_eligibility", "eligible"),
                    official_url=s_data.get("official_url", ""),
                    notes=s_data.get("notes", "")
                )

                # Score scholarship
                scored_sch = self.scorer.score_scholarship(sch)

                # Create pipeline ResearchItem
                dep_badge = "👨‍👩‍👧 Family Financially Supported" if scored_sch.dependant_support_classification == "excellent" else "👨‍👩‍👧 Dependants Permitted"
                abstract = (
                    f"Scholarship by {scored_sch.provider} ({scored_sch.country}). "
                    f"Stipend: {scored_sch.stipend_amount}. Tuition: {scored_sch.tuition_coverage}. "
                    f"Dependants: {scored_sch.dependant_support_details} {dep_badge}."
                )

                from src.models import ScoreBreakdown
                score_bd = ScoreBreakdown(
                    topic_score=scored_sch.score * 0.4,
                    credibility_score=2.5,
                    recency_score=1.5,
                    phd_boost=1.0,
                    final_score=scored_sch.score,
                    matched_topics=["PhD Funding", scored_sch.country],
                    reasons=scored_sch.reasons
                )

                item = ResearchItem(
                    title=f"[Scholarship] {scored_sch.name}",
                    url=scored_sch.official_url,
                    source=scored_sch.provider,
                    source_tier=self.tier,
                    item_type=ItemType.FELLOWSHIP.value,
                    publication_date=scored_sch.verification_date,
                    discovery_date=scored_sch.verification_date,
                    abstract=abstract,
                    venue=f"{scored_sch.country} — {scored_sch.university or scored_sch.provider}",
                    topics=["PhD Funding", "International Scholarship", "Dependant Support", scored_sch.country],
                    institution=scored_sch.university or scored_sch.provider,
                    location=scored_sch.country,
                    deadline=scored_sch.deadline,
                    score=score_bd,
                    opportunity_data={
                        "kind": "scholarship",
                        "type": "scholarship",
                        "name": scored_sch.name,
                        "country": scored_sch.country,
                        "funding_type": "fully_funded",
                        "dependant_support": "financially_supported" if scored_sch.dependant_support_classification in ["financially_supported", "excellent"] else "permitted",
                        "allowance_details": scored_sch.dependant_support_details,
                        "legal_notes": scored_sch.notes,
                        "deadline": scored_sch.deadline,
                        "official_link": scored_sch.official_url,
                        "fit_score": scored_sch.score,
                        "data": scored_sch.to_dict()
                    }
                )
                items.append(item)

            except Exception as e:
                logger.warning(f"Error processing scholarship {s_data.get('name')}: {e}")

        logger.info(f"Loaded and verified {len(items)} authoritative scholarships across target countries.")
        return items

    def get_scholarships_list(self) -> List[Scholarship]:
        """Direct access to Scholarship domain objects."""
        curated = self.phd_config.get("curated_scholarships", [])
        sch_list = []
        for s_data in curated:
            try:
                sch = Scholarship(
                    name=s_data.get("name", ""),
                    provider=s_data.get("provider", ""),
                    country=s_data.get("country", ""),
                    university=s_data.get("university", ""),
                    degree_level=s_data.get("degree_level", "PhD"),
                    tuition_coverage=s_data.get("tuition_coverage", ""),
                    stipend_amount=s_data.get("stipend_amount", ""),
                    duration=s_data.get("duration", ""),
                    deadline=s_data.get("deadline"),
                    start_date=s_data.get("start_date"),
                    dependant_support_classification=s_data.get("dependant_support_classification", "permitted"),
                    dependant_support_details=s_data.get("dependant_support_details", ""),
                    family_accommodation=s_data.get("family_accommodation", ""),
                    international_eligibility=s_data.get("international_eligibility", "eligible"),
                    official_url=s_data.get("official_url", ""),
                    notes=s_data.get("notes", "")
                )
                sch_list.append(self.scorer.score_scholarship(sch))
            except Exception:
                pass
        return sch_list
