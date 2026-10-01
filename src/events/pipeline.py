"""End-to-end pipeline orchestrator for Edge Computing Events."""

import datetime
from typing import List, Dict, Any, Optional
from src.events.models import EdgeEvent, EventStatus
from src.events.collector import EdgeEventCollector
from src.events.normalizer import EventNormalizer
from src.events.deduplicator import EventDeduplicator
from src.events.verifier import EventVerifier
from src.events.scorer import EventScorer
from src.events.state_manager import EventsStateManager
from src.utils.config_loader import ConfigManager
from src.utils.logger import logger
from src.email.sender import EmailSender


class EdgeEventsPipeline:
    """
    Executes the complete event discovery and tracking lifecycle:
    collect → normalize → deduplicate → verify → score → notify → state
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.collector = EdgeEventCollector(config_manager=self.config)
        self.normalizer = EventNormalizer()
        self.deduplicator = EventDeduplicator()
        self.verifier = EventVerifier()
        self.scorer = EventScorer(config_manager=self.config)
        self.state_manager = EventsStateManager()

    def run(
        self,
        min_score: float = 6.5,
        include_concluded: bool = False,
        dry_run: bool = False,
        send_email: bool = False
    ) -> Dict[str, Any]:
        """Runs the full events discovery and tracking pipeline."""
        logger.info(f"=== Starting Edge Computing Events Pipeline (Dry-run: {dry_run}) ===")

        # 1. Collect
        raw_events = self.collector.fetch_events()
        logger.info(f"Collected {len(raw_events)} events from curated and external sources.")

        # 2. Deduplicate
        seen_ids = self.state_manager.load_seen_event_ids() if not dry_run else set()
        unique_events = self.deduplicator.deduplicate(raw_events, seen_ids=seen_ids)
        logger.info(f"Deduplicated to {len(unique_events)} unique events.")

        # 3. Verify
        verified_events = self.verifier.filter_active(unique_events, include_concluded=include_concluded)
        logger.info(f"Verified {len(verified_events)} active/upcoming events.")

        # 4. Score
        scored_events: List[EdgeEvent] = []
        for ev in verified_events:
            self.scorer.score_event(ev)
            if ev.relevance_score >= min_score:
                scored_events.append(ev)

        # Sort by relevance score descending
        scored_events.sort(key=lambda e: e.relevance_score, reverse=True)
        logger.info(f"Scored and filtered {len(scored_events)} events meeting min score {min_score}.")

        # 5. State Persistence
        if not dry_run and scored_events:
            self.state_manager.save_events(scored_events)
            self.state_manager.record_seen_events(scored_events)
            self.state_manager.record_history(scored_events)
            logger.info("Persisted events and updated state records.")

        # 6. Email notification if requested
        email_sent = False
        if send_email and scored_events and not dry_run:
            email_sent = self._dispatch_email_alert(scored_events)

        return {
            "total_collected": len(raw_events),
            "unique_events": len(unique_events),
            "active_events": len(verified_events),
            "qualified_events": len(scored_events),
            "events": scored_events,
            "email_sent": email_sent
        }

    def render_markdown_summary(self, events: List[EdgeEvent]) -> str:
        """Renders formatted Markdown summary of events grouped by type."""
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        lines = [
            f"# Edge Computing Events & Academic/Industrial Opportunities",
            f"**Generated:** {today_str} | **Total Events:** {len(events)}\n",
            "---",
        ]

        if not events:
            lines.append("\n*No upcoming events matching the criteria were found.*\n")
            return "\n".join(lines)

        # Group by event type
        grouped: Dict[str, List[EdgeEvent]] = {}
        for ev in events:
            t = ev.event_type.replace("_", " ").title()
            grouped.setdefault(t, []).append(ev)

        for event_type_title, ev_list in grouped.items():
            lines.append(f"\n## {event_type_title} ({len(ev_list)})\n")
            for ev in ev_list:
                status_badge = f"[{ev.status.upper()}]"
                dates_str = f"{ev.start_date or 'TBA'} to {ev.end_date or 'TBA'}"
                lines.append(f"### {ev.event_name} {status_badge}")
                lines.append(f"- **Organizer:** {ev.organizer}")
                lines.append(f"- **Dates:** {dates_str} | **Location:** {ev.location} ({ev.format.upper()})")
                lines.append(f"- **Relevance Score:** {ev.relevance_score:.1f}/10.0")
                if ev.official_website:
                    lines.append(f"- **Website:** [{ev.official_website}]({ev.official_website})")
                lines.append(f"- **Registration Fee:** {ev.registration_fee or ev.fee_status.title()}")
                if ev.cfp_deadline:
                    lines.append(f"- **CFP Deadline:** **{ev.cfp_deadline}**")
                if ev.discounts_subsidies:
                    lines.append("- **Discounts, Subsidies & Grants:**")
                    for d in ev.discounts_subsidies:
                        lines.append(f"  * **{d.name}** ({d.discount_type.replace('_', ' ').title()}): {d.amount_or_rate}")
                        if d.eligibility:
                            lines.append(f"    - *Eligibility:* {d.eligibility}")
                lines.append(f"- **Description:** {ev.description}")
                lines.append(f"- **Topics:** {', '.join(ev.topics)}")
                lines.append("")

        return "\n".join(lines)

    def _dispatch_email_alert(self, events: List[EdgeEvent]) -> bool:
        """Dispatches an email alert with the qualified events."""
        try:
            email_sender = EmailSender(self.config.email_config)
            today_str = datetime.date.today().strftime("%d %b %Y")
            subject = f"[Edge PhD Events Alert] {today_str} — {len(events)} High-Relevance Opportunities"
            markdown_body = self.render_markdown_summary(events)
            html_body = f"<html><body><pre style='font-family: sans-serif; white-space: pre-wrap;'>{markdown_body}</pre></body></html>"
            return email_sender.send(subject=subject, html_content=html_body, text_content=markdown_body)
        except Exception as e:
            logger.error(f"Failed to dispatch events email alert: {e}")
            return False
