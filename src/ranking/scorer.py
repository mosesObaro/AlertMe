"""Transparent 0-10 Multi-factor Relevance Scoring Engine."""

import datetime
import re
from typing import List, Dict, Any, Optional, Tuple
from dateutil import parser as date_parser
from src.models import ResearchItem, ScoreBreakdown, ItemType, CredibilityTier
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger


class RelevanceScorer:
    """Computes transparent, multi-factor relevance scores for academic research items."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()

    def score_item(self, item: ResearchItem) -> ScoreBreakdown:
        """Calculates relevance score and breakdown for a single item."""
        reasons: List[str] = []
        matched_topics: List[str] = []

        # 1. Topic Relevance Score (0 - 4.0 points)
        topic_score, matched = self._compute_topic_score(item, reasons)
        matched_topics.extend(matched)

        # 2. Source Credibility Score (0 - 2.5 points)
        credibility_score = self._compute_credibility_score(item, reasons)

        # 3. Recency Boost (0 - 1.5 points)
        recency_score = self._compute_recency_score(item, reasons)

        # 4. Learning Stage Boost (0 - 1.0 points)
        stage_boost = self._compute_learning_stage_boost(item, reasons)

        # 5. PhD Preparation & Application Mode Boost (0 - 1.0 points)
        phd_boost = self._compute_phd_boost(item, reasons)

        # 6. Negative Penalties
        negative_penalty = self._compute_negative_penalty(item, reasons)

        # Total Calculation
        raw_final = (
            topic_score +
            credibility_score +
            recency_score +
            stage_boost +
            phd_boost +
            negative_penalty
        )

        final_score = max(0.0, min(10.0, round(raw_final, 1)))

        breakdown = ScoreBreakdown(
            topic_score=round(topic_score, 2),
            credibility_score=round(credibility_score, 2),
            recency_score=round(recency_score, 2),
            stage_boost=round(stage_boost, 2),
            phd_boost=round(phd_boost, 2),
            negative_penalty=round(negative_penalty, 2),
            final_score=final_score,
            matched_topics=list(set(matched_topics)),
            reasons=reasons
        )

        item.score = breakdown
        return breakdown

    @staticmethod
    def _matches_topic_in_text(topic: str, text: str) -> bool:
        t_low = topic.strip().lower()
        if not t_low or not text:
            return False
        # For short acronyms/words, require word boundaries to avoid false positives (e.g. "mec" in "mechanism")
        if len(t_low) <= 4 or " " not in t_low:
            return bool(re.search(r"(?<!\w)" + re.escape(t_low) + r"(?!\w)", text))
        return t_low in text

    def _compute_topic_score(self, item: ResearchItem, reasons: List[str]) -> Tuple[float, List[str]]:
        title_lower = (item.title or "").lower()
        abstract_lower = (item.abstract or "").lower()
        combined_text = f"{title_lower} {abstract_lower}"

        primary_topics = self.config.primary_topics
        secondary_topics = self.config.secondary_topics
        research_topics = self.config.research_topics

        matched = []
        primary_matches = []
        secondary_matches = []
        research_matches = []

        # Check Primary Topics
        for topic in primary_topics:
            if self._matches_topic_in_text(topic, title_lower):
                primary_matches.append(f"{topic} (Title)")
                matched.append(topic)
            elif self._matches_topic_in_text(topic, abstract_lower):
                primary_matches.append(f"{topic} (Abstract)")
                matched.append(topic)

        # Check Specific Research Sub-Topics
        for topic in research_topics:
            if self._matches_topic_in_text(topic, title_lower) or self._matches_topic_in_text(topic, abstract_lower):
                research_matches.append(topic)
                matched.append(topic)

        # Check Secondary Topics
        for topic in secondary_topics:
            if self._matches_topic_in_text(topic, title_lower) or self._matches_topic_in_text(topic, abstract_lower):
                secondary_matches.append(topic)
                matched.append(topic)

        score = 0.0

        # Primary / Secondary topic calculation
        if primary_matches:
            # Having primary topic in title gives large points
            title_match_count = sum(1 for m in primary_matches if "(Title)" in m)
            if title_match_count > 0:
                score += 2.8 + min(0.6, (title_match_count - 1) * 0.3)
            else:
                score += 2.2
            reasons.append(f"✓ Primary topic match: {', '.join(primary_matches[:2])}")
        elif secondary_matches and any(r in combined_text for r in ["edge", "mec", "fog", "cloudlet"]):
            score += 2.2
            reasons.append(f"✓ Secondary topic with Edge context: {', '.join(secondary_matches[:2])}")
        elif secondary_matches:
            # Check if secondary topic is in title
            sec_in_title = any(t.lower() in title_lower for t in secondary_topics)
            score += 1.6 if sec_in_title else 1.0
            reasons.append(f"✓ Secondary topic match: {', '.join(secondary_matches[:2])}")
        else:
            reasons.append("⚠ Weak or no direct topic match")

        # Specific research topic synergy
        if research_matches:
            bonus = min(0.8, len(research_matches) * 0.4)
            score += bonus
            reasons.append(f"✓ Key research area match: {', '.join(research_matches[:2])} (+{bonus:.1f})")

        return min(4.0, score), matched

    def _compute_credibility_score(self, item: ResearchItem, reasons: List[str]) -> float:
        tier = item.source_tier
        if tier == CredibilityTier.TIER1_ACADEMIC_STANDARDS.value:
            reasons.append(f"✓ Tier 1 Academic/Standards source: {item.source} (+2.5)")
            return 2.5
        elif tier == CredibilityTier.TIER2_UNIVERSITY_LAB.value:
            reasons.append(f"✓ Tier 2 University/Lab source: {item.source} (+2.0)")
            return 2.0
        elif tier == CredibilityTier.TIER3_CONFERENCE.value:
            reasons.append(f"✓ Tier 3 Conference CFP/Venue: {item.source} (+1.5)")
            return 1.5
        elif tier == CredibilityTier.TIER4_INDUSTRY.value:
            reasons.append(f"✓ Tier 4 Industry Research Lab: {item.source} (+1.0)")
            return 1.0
        else:
            reasons.append(f"• Standard source: {item.source} (+0.5)")
            return 0.5

    def _compute_recency_score(self, item: ResearchItem, reasons: List[str]) -> float:
        if not item.publication_date:
            return 0.5

        try:
            pub_dt = date_parser.parse(item.publication_date).date()
            today = datetime.date.today()
            age_days = (today - pub_dt).days

            if age_days < 0: # Future conference deadline or publication
                reasons.append(f"✓ Upcoming date: {item.publication_date} (+1.5)")
                return 1.5
            elif age_days <= 3:
                reasons.append(f"✓ Freshly published ({age_days}d ago) (+1.5)")
                return 1.5
            elif age_days <= 7:
                reasons.append(f"✓ Published within last week ({age_days}d ago) (+1.2)")
                return 1.2
            elif age_days <= 14:
                reasons.append(f"✓ Published within last 2 weeks ({age_days}d ago) (+0.8)")
                return 0.8
            elif age_days <= 30:
                reasons.append(f"✓ Published within last month ({age_days}d ago) (+0.5)")
                return 0.5
            else:
                reasons.append(f"• Published >30d ago ({age_days}d ago) (+0.2)")
                return 0.2
        except Exception:
            return 0.5

    def _compute_learning_stage_boost(self, item: ResearchItem, reasons: List[str]) -> float:
        learning_stage = self.config.learning_stage
        current_topics = learning_stage.get("current_topics", [])
        if not current_topics:
            return 0.0

        combined = f"{item.title} {item.abstract}".lower()
        matched_stage_topics = [t for t in current_topics if t.lower() in combined]

        if matched_stage_topics:
            reasons.append(f"✓ Matches your current learning stage topic: {', '.join(matched_stage_topics)} (+1.0)")
            return 1.0
        return 0.0

    def _compute_phd_boost(self, item: ResearchItem, reasons: List[str]) -> float:
        boost = 0.0
        phd_target = self.config.phd_target
        target_deadline_str = phd_target.get("target_application_period")

        # Check proximity to application deadline
        is_application_season = False
        if target_deadline_str:
            try:
                target_dt = date_parser.parse(target_deadline_str).date()
                days_left = (target_dt - datetime.date.today()).days
                if 0 <= days_left <= 90:
                    is_application_season = True
            except Exception:
                pass

        if item.item_type == ItemType.PHD_OPPORTUNITY.value:
            boost += 1.0 if not is_application_season else 1.2
            reasons.append(f"✓ PhD / Fellowship Opportunity (+{boost:.1f})")
        elif item.item_type == ItemType.CONFERENCE_CFP.value:
            boost += 0.8
            reasons.append(f"✓ Conference CFP / Submission Track (+{boost:.1f})")
        elif item.item_type == ItemType.SURVEY.value:
            boost += 0.7
            reasons.append(f"✓ Comprehensive Literature Survey / Review (+{boost:.1f})")
        elif item.item_type == ItemType.BENCHMARK_CODE.value:
            boost += 0.5
            reasons.append(f"✓ Open Benchmark / Research Artifact (+{boost:.1f})")

        return min(1.0, boost)

    def _compute_negative_penalty(self, item: ResearchItem, reasons: List[str]) -> float:
        combined = f"{item.title} {item.abstract}".lower()
        negative_keywords = self.config.negative_keywords
        penalty = 0.0

        for kw in negative_keywords:
            if kw.lower() in combined:
                penalty -= 4.0
                reasons.append(f"✕ Filtered by negative keyword: '{kw}' (-4.0)")
                break

        # Check for generic AI or web dev with no edge context
        generic_unrelated = ["react js", "web development", "crypto trading", "affiliate marketing"]
        for kw in generic_unrelated:
            if kw in combined and not any(e in combined for e in ["edge", "mec", "fog", "cloudlet", "distributed"]):
                penalty -= 3.0
                reasons.append(f"✕ Generic off-topic content (-3.0)")
                break

        return penalty

    def filter_and_rank(self, items: List[ResearchItem], min_score: float = 6.5) -> List[ResearchItem]:
        """Scores, filters, and ranks items in descending order of relevance score."""
        scored_items = []
        for item in items:
            self.score_item(item)
            if item.score and item.score.final_score >= min_score:
                scored_items.append(item)

        scored_items.sort(key=lambda x: (x.score.final_score if x.score else 0.0), reverse=True)
        return scored_items
