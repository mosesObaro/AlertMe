"""Transparent 0-10 Multi-factor Relevance Scoring Engine for Edge Events."""

import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
from src.events.models import EdgeEvent, EventScoreBreakdown, EventStatus, EventType, FeeStatus, DiscountType
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger


class EventScorer:
    """Computes transparent, multi-factor relevance scores for academic and industrial Edge events."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        events_cfg = self.config.events if hasattr(self.config, "events") else {}
        search_specs = events_cfg.get("search_specifications", {}) if isinstance(events_cfg, dict) else {}

        # Load keywords from config with robust fallbacks
        self.primary_keywords = search_specs.get("primary_keywords", [
            "Edge Computing", "Edge AI", "Edge Intelligence", "Mobile Edge Computing",
            "Multi-access Edge Computing", "MEC", "Fog Computing", "Cloud-Edge Continuum",
            "Distributed Edge Systems", "Federated Learning at the Edge", "Device-Edge-Cloud",
            "Computation Offloading", "Cloudlets"
        ])
        self.secondary_keywords = search_specs.get("secondary_keywords", [
            "Distributed Systems", "Internet of Things", "IoT", "TinyML",
            "Serverless Computing", "Pervasive Computing", "5G/6G Networks",
            "Edge Security", "Edge Storage", "Edge Mesh", "Microservices at the Edge"
        ])
        self.training_keywords = search_specs.get("training_keywords", [
            "Bootcamp", "Summer School", "Winter School", "Training Program",
            "Hands-on Workshop", "Tutorial", "Doctoral Symposium"
        ])
        self.negative_keywords = search_specs.get("negative_keywords", [
            "crypto", "bitcoin", "nft", "web development bootcamp", "react js",
            "css tips", "affiliate marketing", "dropshipping"
        ])

    def score_event(self, event: EdgeEvent) -> EventScoreBreakdown:
        """Calculates multi-factor score and breakdown for an event."""
        reasons: List[str] = []
        matched_topics: List[str] = []

        # 1. Topic Relevance Score (0 - 4.0)
        topic_score, topics_found = self._compute_topic_score(event, reasons)
        matched_topics.extend(topics_found)

        # 2. Source Credibility Score (0 - 2.5)
        credibility_score = self._compute_credibility_score(event, reasons)

        # 3. Affordability & Subsidies Boost (0 - 1.5)
        affordability_boost = self._compute_affordability_boost(event, reasons)

        # 4. Actionability & Urgency Boost (0 - 1.0)
        actionability_boost = self._compute_actionability_boost(event, reasons)

        # 5. PhD Value & Research Track Boost (0 - 1.0)
        phd_value_boost = self._compute_phd_value_boost(event, reasons)

        # 6. Negative Penalties
        negative_penalty = self._compute_negative_penalty(event, reasons)

        raw_final = (
            topic_score +
            credibility_score +
            affordability_boost +
            actionability_boost +
            phd_value_boost +
            negative_penalty
        )

        final_score = max(0.0, min(10.0, round(raw_final, 1)))

        breakdown = EventScoreBreakdown(
            topic_score=round(topic_score, 2),
            credibility_score=round(credibility_score, 2),
            affordability_boost=round(affordability_boost, 2),
            actionability_boost=round(actionability_boost, 2),
            phd_value_boost=round(phd_value_boost, 2),
            negative_penalty=round(negative_penalty, 2),
            final_score=final_score,
            matched_topics=list(dict.fromkeys(matched_topics)),
            reasons=reasons
        )

        event.score = breakdown
        event.relevance_score = final_score
        return breakdown

    @staticmethod
    def _matches_keyword(keyword: str, text: str) -> bool:
        kw = keyword.strip().lower()
        if not kw or not text:
            return False
        if len(kw) <= 4 or " " not in kw:
            return bool(re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", text.lower()))
        return kw in text.lower()

    def _compute_topic_score(self, event: EdgeEvent, reasons: List[str]) -> Tuple[float, List[str]]:
        title_lower = (event.event_name or "").lower()
        desc_lower = (event.description or "").lower()
        topics_str = " ".join(event.topics).lower()
        combined_text = f"{title_lower} {desc_lower} {topics_str}"

        score = 0.0
        matched = []

        # Check Primary Keywords
        primary_title_hits = []
        primary_body_hits = []

        for kw in self.primary_keywords:
            if self._matches_keyword(kw, title_lower):
                primary_title_hits.append(kw)
                matched.append(kw)
            elif self._matches_keyword(kw, combined_text):
                primary_body_hits.append(kw)
                matched.append(kw)

        if primary_title_hits:
            score += 2.5
            reasons.append(f"Direct Edge core focus in title: {', '.join(primary_title_hits[:3])} (+2.5)")
        elif primary_body_hits:
            score += 1.8
            reasons.append(f"Primary Edge topic match in description: {', '.join(primary_body_hits[:3])} (+1.8)")

        # Additional primary depth
        total_primary = len(primary_title_hits) + len(primary_body_hits)
        if total_primary >= 3:
            score += 1.2
            reasons.append("Multi-topic Edge synergy across tracks (+1.2)")
        elif total_primary >= 2 and score < 3.2:
            score += 0.7
            reasons.append("Multi-topic Edge synergy (+0.7)")

        # Check Secondary Keywords
        sec_hits = [kw for kw in self.secondary_keywords if self._matches_keyword(kw, combined_text)]
        if sec_hits:
            sec_boost = min(0.8, len(sec_hits) * 0.4)
            score += sec_boost
            matched.extend(sec_hits[:2])
            reasons.append(f"Adjacency systems topics matched: {', '.join(sec_hits[:2])} (+{sec_boost:.1f})")

        return min(4.0, score), matched

    def _compute_credibility_score(self, event: EdgeEvent, reasons: List[str]) -> float:
        org_lower = f"{event.organizer} {event.source}".lower()
        website_lower = (event.official_website or "").lower()

        # Tier 1 Professional Organizations
        if any(org in org_lower or org in website_lower for org in ["ieee", "acm", "usenix"]):
            reasons.append(f"Tier 1 professional organization ({event.organizer}) (+2.5)")
            return 2.5

        # Tier 2 Open Source Foundations & Top Academic Labs
        if any(org in org_lower for org in ["linux foundation", "cncf", "openinfra", "tinyml foundation", "harvard", "cambridge", "ictp", "university"]):
            reasons.append(f"Tier 2 established foundation/university ({event.organizer}) (+2.0)")
            return 2.0

        # Tier 3 Industry Associations
        if any(org in org_lower for org in ["topio", "association", "consortium", "eclipse"]):
            reasons.append(f"Tier 3 industry consortium ({event.organizer}) (+1.5)")
            return 1.5

        reasons.append("General event organizer (+1.0)")
        return 1.0

    def _compute_affordability_boost(self, event: EdgeEvent, reasons: List[str]) -> float:
        boost = 0.0

        # Free admission
        if event.fee_status == FeeStatus.FREE.value:
            boost += 1.0
            reasons.append("100% Free registration (+1.0)")
        elif event.fee_status == FeeStatus.HYBRID_FREE.value:
            boost += 0.8
            reasons.append("Free virtual track available (+0.8)")

        # Travel Grant
        if event.has_travel_grant:
            boost += 0.8
            reasons.append("Student travel grant / STG available (+0.8)")

        # Student rate
        if event.has_student_discount:
            boost += 0.5
            reasons.append("Subsidized student rate available (+0.5)")

        # Scholarship or fee waiver
        if event.has_scholarship or event.has_fee_waiver:
            boost += 0.5
            reasons.append("Scholarship / attendance fee waiver supported (+0.5)")

        return min(1.5, boost)

    def _compute_actionability_boost(self, event: EdgeEvent, reasons: List[str]) -> float:
        boost = 0.0
        today = datetime.date.today()

        # Open CFP submission deadline
        if event.cfp_deadline:
            try:
                deadline_dt = datetime.date.fromisoformat(event.cfp_deadline[:10])
                days_to_deadline = (deadline_dt - today).days
                if 0 <= days_to_deadline <= 60:
                    boost += 0.7
                    reasons.append(f"Active CFP deadline in {days_to_deadline} days (+0.7)")
            except Exception:
                pass

        # Early bird deadline active
        if event.has_early_bird:
            boost += 0.3
            reasons.append("Early-bird discount window open (+0.3)")

        # Upcoming within lookahead window
        if event.start_date:
            try:
                start_dt = datetime.date.fromisoformat(event.start_date[:10])
                days_to_start = (start_dt - today).days
                if 0 <= days_to_start <= 120:
                    boost += 0.3
                    reasons.append(f"Event upcoming in {days_to_start} days (+0.3)")
            except Exception:
                pass

        return min(1.0, boost)

    def _compute_phd_value_boost(self, event: EdgeEvent, reasons: List[str]) -> float:
        combined = f"{event.event_name} {event.description} {' '.join(event.topics)}".lower()
        boost = 0.0

        if any(term in combined for term in ["doctoral symposium", "doctoral consortium", "student research competition", "src"]):
            boost += 0.8
            reasons.append("Doctoral symposium / student research competition track (+0.8)")
        elif any(term in combined for term in ["summer school", "winter school", "bootcamp", "training course"]):
            boost += 0.7
            reasons.append("Dedicated doctoral/researcher training program (+0.7)")
        elif any(term in combined for term in ["workshop", "tutorial", "hands-on lab"]):
            boost += 0.5
            reasons.append("Interactive research workshop / tutorial track (+0.5)")
        elif event.event_type in [EventType.ACADEMIC_CONFERENCE.value, EventType.SYMPOSIUM.value]:
            boost += 0.5
            reasons.append("Peer-reviewed academic research conference/symposium (+0.5)")

        return min(1.0, boost)

    def _compute_negative_penalty(self, event: EdgeEvent, reasons: List[str]) -> float:
        penalty = 0.0
        combined = f"{event.event_name} {event.description}".lower()

        # Concluded / expired event
        if event.status == EventStatus.CONCLUDED.value:
            penalty -= 4.0
            reasons.append("Event is already concluded (-4.0)")

        # Negative spam keywords
        for neg in self.negative_keywords:
            if self._matches_keyword(neg, combined):
                penalty -= 3.0
                reasons.append(f"Negative keyword detected '{neg}' (-3.0)")
                break

        return penalty
