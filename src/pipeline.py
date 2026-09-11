"""Master pipeline orchestrator for Edge PhD Research Intelligence."""

import os
from typing import List, Dict, Any, Optional
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger
from src.models import (
    ResearchItem, ItemType, CredibilityTier,
    RecruitmentStatus, FundingStatus, DependantSupportClassification
)
from src.collectors.base import BaseCollector
from src.collectors.arxiv import ArxivCollector
from src.collectors.openalex import OpenAlexCollector
from src.collectors.crossref import CrossrefCollector
from src.collectors.semantic_scholar import SemanticScholarCollector
from src.collectors.rss_collector import RssFeedCollector
from src.collectors.conferences import ConferenceCollector
from src.collectors.opportunities import OpportunityCollector
from src.collectors.lab_recruitment import LabRecruitmentCollector
from src.collectors.scholarships import ScholarshipCollector
from src.collectors.github_repos import GitHubRepoCollector
from src.deduplication.deduplicator import Deduplicator
from src.ranking.scorer import RelevanceScorer
from src.summarization.intelligence import IntelligenceEngine
from src.summarization.trends import TrendDetector
from src.summarization.supervisors import SupervisorTracker
from src.summarization.study_guide import StudyGuideGenerator
from src.storage.state_manager import StateManager
from src.storage.dashboard_generator import DashboardGenerator
from src.email.renderer import EmailRenderer
from src.email.sender import EmailSender


class ResearchPipeline:
    """End-to-end pipeline that discovers, filters, scores, analyzes, and delivers academic research intelligence."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.state_manager = StateManager()
        self.deduplicator = Deduplicator()
        self.scorer = RelevanceScorer(self.config)
        self.intelligence_engine = IntelligenceEngine(self.config.profile.get("ai_summarization"))
        self.trend_detector = TrendDetector()
        self.supervisor_tracker = SupervisorTracker()
        self.study_guide_gen = StudyGuideGenerator(self.config)
        self.dashboard_gen = DashboardGenerator(self.state_manager)
        self.email_renderer = EmailRenderer()
        self.email_sender = EmailSender(self.config.email_config)
        self.collectors: List[BaseCollector] = []
        self._init_collectors()

    def _init_collectors(self):
        """Initializes all configured collectors across academic, RSS, conferences, and opportunities."""
        sources = self.config.sources

        # Tier 1 Academic APIs
        self.collectors.append(ArxivCollector(
            name="arXiv Edge Computing",
            query='cat:cs.DC AND (all:"edge computing" OR all:"edge intelligence" OR all:"mobile edge computing" OR all:"edge AI")'
        ))
        self.collectors.append(OpenAlexCollector(
            name="OpenAlex Works",
            search_query="edge computing OR edge intelligence OR mobile edge computing"
        ))
        self.collectors.append(CrossrefCollector(
            name="Crossref Works",
            query="edge computing edge intelligence"
        ))
        self.collectors.append(SemanticScholarCollector(
            name="Semantic Scholar",
            query="edge computing resource allocation offloading"
        ))

        # Tier 1 Standards RSS
        for src in sources.get("tier1_academic_and_standards", []):
            if src.get("type") == "rss" and src.get("enabled", True):
                self.collectors.append(RssFeedCollector(
                    name=src.get("name"),
                    url=src.get("url"),
                    tier=CredibilityTier.TIER1_ACADEMIC_STANDARDS.value,
                    default_item_type=ItemType.STANDARDS_UPDATE.value
                ))

        # Tier 2 University Labs RSS
        for src in sources.get("tier2_universities_and_labs", []):
            if src.get("type") == "rss" and src.get("enabled", True):
                self.collectors.append(RssFeedCollector(
                    name=src.get("name"),
                    url=src.get("url"),
                    tier=CredibilityTier.TIER2_UNIVERSITY_LAB.value,
                    institution=src.get("institution", ""),
                    default_item_type=ItemType.TECH_REPORT.value
                ))

        # Tier 3 Conferences
        confs_list = self.config.conferences.get("conferences", [])
        self.collectors.append(ConferenceCollector(
            name="Conferences & CFPs",
            conferences_config=confs_list
        ))

        # Tier 4 Industry Research RSS
        for src in sources.get("tier4_industry_research", []):
            if src.get("type") == "rss" and src.get("enabled", True):
                self.collectors.append(RssFeedCollector(
                    name=src.get("name"),
                    url=src.get("url"),
                    tier=CredibilityTier.TIER4_INDUSTRY.value,
                    organization=src.get("organization", ""),
                    default_item_type=ItemType.TECH_REPORT.value
                ))

        # Opportunities, Lab Recruitment, and Curated Scholarships
        self.collectors.append(OpportunityCollector(name="PhD & Fellowship Opportunities"))
        self.collectors.append(LabRecruitmentCollector(name="University Lab PhD Opportunities"))
        self.collectors.append(ScholarshipCollector(name="Curated International Scholarships"))

        # GitHub Edge Repos & Benchmarks
        self.collectors.append(GitHubRepoCollector(name="GitHub Benchmarks"))

    def run(self, mode: str = "daily", dry_run: bool = False) -> Dict[str, Any]:
        """Executes full discovery, analysis, persistence, and dispatch pipeline."""
        logger.info(f"=== Starting Research Pipeline (Mode: {mode.upper()}, Dry-Run: {dry_run}) ===")

        # 1. Collect items from all sources
        all_raw_items: List[ResearchItem] = []
        health_records = []

        for collector in self.collectors:
            try:
                items = collector.collect()
                all_raw_items.extend(items)
            except Exception as e:
                logger.error(f"Collector {collector.name} encountered uncaught error: {e}")
            health_records.append(collector.get_health_status())

        # Save collector health
        self.state_manager.save_source_health(health_records)

        # 2. Deduplication
        seen_history_ids = self.state_manager.load_seen_ids()
        unique_items = self.deduplicator.deduplicate(all_raw_items, seen_history_ids=seen_history_ids)

        # 3. Scoring & Ranking
        min_score = self.config.alert_thresholds.get("minimum_score", 6.5)
        ranked_items = self.scorer.filter_and_rank(unique_items, min_score=min_score)

        # Extract PhD opportunities and scholarships
        phd_opportunities: List[Dict[str, Any]] = []
        scholarships: List[Dict[str, Any]] = []

        for item in ranked_items:
            opp_data = item.opportunity_data
            if opp_data:
                kind = opp_data.get("kind")
                if kind == "phd_opportunity":
                    phd_opportunities.append(opp_data)
                elif kind == "scholarship":
                    scholarships.append(opp_data)
            elif item.item_type in [ItemType.PHD_OPPORTUNITY.value, ItemType.FELLOWSHIP.value]:
                phd_opportunities.append({
                    "title": item.title,
                    "university": item.institution or item.source,
                    "department": "",
                    "country": item.location or "",
                    "link": item.url,
                    "fit_score": item.score.final_score if item.score else 7.0,
                    "recruitment_status": "unverified",
                    "funding_status": "partially_funded",
                    "dependant_support": "unspecified",
                    "direct_quote": None,
                    "deadline": item.deadline
                })

        # Persist opportunities and scholarships
        if phd_opportunities:
            prev_opps = self.state_manager.load_opportunities()
            opp_urls = {o.get("link") for o in phd_opportunities if o.get("link")}
            merged_opps = list(phd_opportunities)
            for po in prev_opps:
                if po.get("link") and po.get("link") not in opp_urls:
                    merged_opps.append(po)
            self.state_manager.save_opportunities(merged_opps)

        if scholarships:
            self.state_manager.save_scholarships(scholarships)

        # 4. Intelligence & Deep Structured Analysis
        for item in ranked_items:
            if item.score and item.score.final_score >= 7.5:
                item.intelligence = self.intelligence_engine.analyze(item)

        # 5. Trend Analysis
        history = self.state_manager.load_alert_history()
        trends = self.trend_detector.detect_trends(ranked_items, history_items=history)
        self.state_manager.save_trends(trends)

        # 6. Supervisor / Researcher Registry Update
        existing_supervisors = self.state_manager.load_supervisors()
        updated_supervisors = self.supervisor_tracker.update_and_extract_supervisors(
            ranked_items, existing_supervisors
        )
        self.state_manager.save_supervisors(updated_supervisors)
        top_supervisors = self.supervisor_tracker.get_top_supervisors_to_watch(updated_supervisors)

        existing_watchlist = self.state_manager.load_researcher_watchlist()
        watchlist_dict = existing_watchlist.get("researchers", {}) if isinstance(existing_watchlist, dict) else {}
        updated_watchlist, _ = self.supervisor_tracker.sync_watchlist(watchlist_dict, ranked_items)
        self.state_manager.save_researcher_watchlist({
            "researchers": updated_watchlist,
            "top_supervisors": top_supervisors
        })

        # 7. Update Dashboard Data
        self.dashboard_gen.generate_dashboard_data(
            current_items=ranked_items,
            trends=trends,
            supervisors=top_supervisors,
            opportunities=phd_opportunities,
            scholarships=scholarships,
            researchers=list(updated_watchlist.values()) if updated_watchlist else top_supervisors
        )

        # 8. Email Delivery
        email_sent = False
        daily_min = self.config.alert_thresholds.get("daily_digest_min_score", 7.5)
        weekly_min = self.config.alert_thresholds.get("weekly_digest_min_score", 6.8)
        daily_limit = self.config.alert_thresholds.get("daily_limit", 10)
        weekly_limit = self.config.alert_thresholds.get("weekly_limit", 20)

        # Check for urgent items (including actively recruiting fully-funded PhD openings)
        urgent_min = self.config.alert_thresholds.get("urgent_alert_min_score", 9.0)
        for item in ranked_items:
            opp_data = item.opportunity_data
            if opp_data and opp_data.get("kind") == "phd_opportunity":
                if (
                    opp_data.get("recruitment_status") == RecruitmentStatus.ACTIVELY_RECRUITING.value
                    and opp_data.get("funding_status") == FundingStatus.FULLY_FUNDED.value
                    and (item.score and item.score.final_score >= 8.5)
                ):
                    item.is_urgent = True

        if dry_run:
            self.email_sender.provider = "console"

        if mode == "daily":
            daily_items = [i for i in ranked_items if i.score and i.score.final_score >= daily_min][:daily_limit]
            subject, html, text = self.email_renderer.render_daily_digest(
                items=daily_items,
                opportunities=phd_opportunities[:3],
                scholarships=scholarships[:3]
            )
            email_sent = self.email_sender.send(subject, html, text)
            if not dry_run and daily_items:
                self.state_manager.record_seen_items(daily_items)
                self.state_manager.record_alerts_sent(daily_items, alert_mode="daily")

        elif mode == "weekly":
            weekly_items = [i for i in ranked_items if i.score and i.score.final_score >= weekly_min][:weekly_limit]
            top_papers = [i for i in weekly_items if i.item_type in [ItemType.PAPER.value, ItemType.PREPRINT.value, ItemType.SURVEY.value]]
            confs = [i for i in weekly_items if i.item_type in [ItemType.CONFERENCE_CFP.value, ItemType.WORKSHOP.value]]
            opps = [i for i in weekly_items if i.item_type in [ItemType.PHD_OPPORTUNITY.value, ItemType.FELLOWSHIP.value]]
            
            study_guide = self.study_guide_gen.generate_focus_plan(top_papers, confs, opps)
            subject, html, text = self.email_renderer.render_weekly_digest(
                items=weekly_items,
                trends=trends,
                supervisors=top_supervisors,
                study_guide=study_guide,
                opportunities=phd_opportunities[:5],
                scholarships=scholarships[:5]
            )
            email_sent = self.email_sender.send(subject, html, text)
            if not dry_run and weekly_items:
                self.state_manager.record_seen_items(weekly_items)
                self.state_manager.record_alerts_sent(weekly_items, alert_mode="weekly")

        elif mode == "urgent":
            urgent_items = [i for i in ranked_items if i.is_urgent or (i.score and i.score.final_score >= urgent_min)]
            for u_item in urgent_items[:3]:
                subject, html, text = self.email_renderer.render_urgent_alert(u_item)
                self.email_sender.send(subject, html, text)
                if not dry_run:
                    self.state_manager.record_seen_items([u_item])
                    self.state_manager.record_alerts_sent([u_item], alert_mode="urgent")
            email_sent = True

        logger.info("=== Research Pipeline Execution Finished ===")
        return {
            "mode": mode,
            "raw_items_count": len(all_raw_items),
            "unique_items_count": len(unique_items),
            "ranked_items_count": len(ranked_items),
            "email_sent": email_sent,
            "top_item": ranked_items[0].title if ranked_items else None
        }
