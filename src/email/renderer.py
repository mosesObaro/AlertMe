"""Email template rendering using Jinja2."""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.models import ResearchItem, ItemType

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


class EmailRenderer:
    """Renders HTML and Plain Text emails for research intelligence alerts."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(["html", "xml"])
        )

    def render_daily_digest(
        self,
        items: List[ResearchItem],
        dashboard_url: str = "https://example.github.io/edge-phd-alert/"
    ) -> Tuple[str, str, str]:
        """Renders Daily Digest email (subject, html, text)."""
        today_str = datetime.date.today().strftime("%d %b %Y")
        subject = f"[Edge PhD Alert] {today_str} — {len(items)} High-Relevance Items"

        # Group items
        top_devs = [i for i in items if i.score and i.score.final_score >= 8.5]
        papers = [i for i in items if i.item_type in [ItemType.PAPER.value, ItemType.PREPRINT.value, ItemType.SURVEY.value] and i not in top_devs]
        opps = [i for i in items if i.item_type in [ItemType.PHD_OPPORTUNITY.value, ItemType.FELLOWSHIP.value]]
        confs = [i for i in items if i.item_type in [ItemType.CONFERENCE_CFP.value, ItemType.WORKSHOP.value]]

        ctx = {
            "subject": subject,
            "date_str": today_str,
            "total_items": len(items),
            "top_developments": top_devs,
            "papers": papers,
            "opportunities": opps,
            "conferences": confs,
            "dashboard_url": dashboard_url
        }

        html_tpl = self.env.get_template("daily_digest.html")
        text_tpl = self.env.get_template("daily_digest.txt")

        html_content = html_tpl.render(**ctx)
        text_content = text_tpl.render(**ctx)

        return subject, html_content, text_content

    def render_weekly_digest(
        self,
        items: List[ResearchItem],
        trends: List[Dict[str, Any]],
        supervisors: List[Dict[str, Any]],
        study_guide: Dict[str, Any],
        dashboard_url: str = "https://example.github.io/edge-phd-alert/"
    ) -> Tuple[str, str, str]:
        """Renders Weekly Digest email (subject, html, text)."""
        today_str = datetime.date.today().strftime("%d %b %Y")
        subject = f"[Edge PhD Weekly Briefing] {today_str} — Research Intelligence Digest"

        top_devs = [i for i in items if i.score and i.score.final_score >= 8.0][:5]
        papers = [i for i in items if i.item_type in [ItemType.PAPER.value, ItemType.PREPRINT.value, ItemType.SURVEY.value] and i not in top_devs][:8]
        opps = [i for i in items if i.item_type in [ItemType.PHD_OPPORTUNITY.value, ItemType.FELLOWSHIP.value]][:4]
        confs = [i for i in items if i.item_type in [ItemType.CONFERENCE_CFP.value, ItemType.WORKSHOP.value]][:4]

        ctx = {
            "subject": subject,
            "date_str": today_str,
            "total_items": len(items),
            "top_developments": top_devs,
            "papers": papers,
            "opportunities": opps,
            "conferences": confs,
            "trends": trends,
            "supervisors": supervisors,
            "study_guide": study_guide,
            "dashboard_url": dashboard_url
        }

        html_tpl = self.env.get_template("weekly_digest.html")
        text_tpl = self.env.get_template("weekly_digest.txt")

        return subject, html_tpl.render(**ctx), text_tpl.render(**ctx)

    def render_urgent_alert(self, item: ResearchItem) -> Tuple[str, str, str]:
        """Renders Urgent immediate alert email."""
        subject = f"🚨 [URGENT PhD ALERT] {item.title[:60]}"
        ctx = {"subject": subject, "item": item}
        html_tpl = self.env.get_template("urgent_alert.html")
        text_tpl = self.env.get_template("urgent_alert.txt")
        return subject, html_tpl.render(**ctx), text_tpl.render(**ctx)
