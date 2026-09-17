"""
Email Alert & Briefing Generator for Country-Based PhD Intelligence Campaigns.
Renders responsive HTML and Markdown briefings with direct download call-to-actions
for Country Reports and Professor Research Dossiers across 4 formats.
"""

from typing import Dict, Any, Optional
from datetime import date
from .models import CountryCampaignResult, CountryCampaign

class CountryAlertGenerator:
    """Generates email briefings for country campaign runs."""

    @staticmethod
    def render_country_email(
        result: CountryCampaignResult,
        campaign: CountryCampaign,
        repo_prefix: str = "https://github.com/mosesObaro/AlertMe/blob/main"
    ) -> Dict[str, str]:
        """
        Generates both HTML and text/markdown email bodies for a country campaign run.
        Returns {'subject': ..., 'html': ..., 'text': ...}.
        """
        subject = f"[PhD Intelligence Alert] {campaign.country}: {result.professors_count} Funded Edge Computing Supervisors"

        # Markdown body
        text_lines = [
            f"# {campaign.country.upper()} PhD FUNDING & SUPERVISOR INTELLIGENCE",
            f"Date: {result.execution_date} | Key Deadline: {campaign.target_deadline}",
            "",
            f"## Country Intelligence Overview",
            f"* Primary Funding Vehicle: {campaign.primary_funding_vehicle}",
            f"* Dependant Visa Policy: {campaign.dependant_visa_policy}",
            f"* Universities Monitored: {result.universities_count}",
            f"* Vetted Supervisors: {result.professors_count}",
            "",
            f"## Discovered Top Supervisors & Research Alignment"
        ]

        for p in result.professors[:10]:
            rec = p.recruitment.status if p.recruitment else "UNKNOWN"
            safe_id = p.name.lower().replace(" ", "_").replace(".", "")
            text_lines.append(f"* **{p.name}** ({p.university}) — Fit: {p.alignment_score:.1f}% | Recruitment: {rec}")
            text_lines.append(f"  Research Focus: {', '.join(p.research_interests[:3])}")
            text_lines.append(f"  Dossier: reports/supervisors/{result.country_code.lower()}/professors/{safe_id}/dossier.md")

        text_lines.append("")
        text_lines.append("## Major Doctoral Funding Schemes")
        for fo in result.funding_opportunities[:4]:
            text_lines.append(f"* **{fo.title}** ({fo.university}): {fo.stipend_amount} | Deadline: {fo.application_deadline}")

        text_lines.append("")
        text_lines.append(f"Country Profile Dossiers (MD, PDF, DOCX, EPUB) generated in: reports/supervisors/{result.country_code.lower()}/")
        text_body = "\n".join(text_lines)

        # HTML body
        prof_cards_html = ""
        for p in result.professors:
            rec_status = p.recruitment.status if p.recruitment else "UNKNOWN"
            badge_color = "#15803d" if rec_status in ["CONFIRMED_ACTIVE", "STRONG_EVIDENCE"] else "#854d0e"
            badge_bg = "#dcfce7" if rec_status in ["CONFIRMED_ACTIVE", "STRONG_EVIDENCE"] else "#fef9c3"
            safe_name = p.name.lower().replace(" ", "_").replace(".", "")

            prof_cards_html += f"""
            <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                    <div>
                        <h3 style="margin:0;font-size:16px;color:#1e293b;">{p.name}</h3>
                        <p style="margin:2px 0 0;font-size:13px;color:#64748b;">{p.university} • {p.department}</p>
                    </div>
                    <span style="background:{badge_bg};color:{badge_color};font-size:11px;font-weight:bold;padding:3px 8px;border-radius:12px;">{rec_status}</span>
                </div>
                <p style="margin:8px 0;font-size:13px;color:#334155;line-height:1.4;">
                    <strong>Research Fit: {p.alignment_score:.1f}%</strong> — {p.research_summary[:160]}...
                </p>
                <div style="margin-top:10px;padding-top:10px;border-top:1px dashed #e2e8f0;font-size:12px;">
                    <a href="{repo_prefix}/reports/supervisors/{result.country_code.lower()}/professors/{safe_name}/dossier.md" style="color:#2563eb;text-decoration:none;font-weight:bold;margin-right:12px;">📄 Markdown Dossier</a>
                    <span style="color:#94a3b8;">•</span>
                    <a href="{repo_prefix}/reports/supervisors/{result.country_code.lower()}/professors/{safe_name}/dossier.pdf" style="color:#dc2626;text-decoration:none;font-weight:bold;margin:0 12px;">📕 PDF</a>
                    <span style="color:#94a3b8;">•</span>
                    <a href="{repo_prefix}/reports/supervisors/{result.country_code.lower()}/professors/{safe_name}/dossier.docx" style="color:#2563eb;text-decoration:none;font-weight:bold;margin:0 12px;">📥 Word</a>
                    <span style="color:#94a3b8;">•</span>
                    <a href="{repo_prefix}/reports/supervisors/{result.country_code.lower()}/professors/{safe_name}/dossier.epub" style="color:#059669;text-decoration:none;font-weight:bold;margin-left:12px;">📱 EPUB</a>
                </div>
            </div>
            """

        html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
.container {{ max-width: 720px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }}
.header {{ background: #1B365D; color: #ffffff; padding: 28px 24px; text-align: left; }}
.content {{ padding: 24px; }}
.metric-box {{ background: #f1f5f9; border-radius: 8px; padding: 14px; margin-bottom: 20px; }}
.btn {{ display: inline-block; background: #2563eb; color: #ffffff; padding: 8px 14px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: bold; margin-right: 8px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <span style="background:#3b82f6;color:#ffffff;font-size:11px;font-weight:bold;padding:3px 8px;border-radius:4px;text-transform:uppercase;">Country Campaign Briefing</span>
        <h1 style="margin:8px 0 4px;font-size:22px;">{campaign.country} PhD Supervisor & Funding Intelligence</h1>
        <p style="margin:0;font-size:13px;opacity:0.9;">Target Field: Edge Computing • Key Deadline: {campaign.target_deadline}</p>
    </div>
    <div class="content">
        <div class="metric-box">
            <h4 style="margin:0 0 8px;font-size:13px;text-transform:uppercase;color:#475569;">Ecosystem Summary</h4>
            <p style="margin:0 0 6px;font-size:13px;"><strong>Funding Vehicle:</strong> {campaign.primary_funding_vehicle}</p>
            <p style="margin:0 0 6px;font-size:13px;"><strong>Dependants:</strong> {campaign.dependant_visa_policy}</p>
            <p style="margin:0;font-size:13px;"><strong>Metrics:</strong> {result.universities_count} Universities Discovered • {result.professors_count} Vetted Supervisors Monitored</p>
        </div>

        <div style="margin-bottom:24px;">
            <h3 style="font-size:16px;color:#1B365D;margin-bottom:12px;">Complete Country Dossier (All 4 Formats)</h3>
            <a href="{repo_prefix}/reports/supervisors/{result.country_code.lower()}/country_profile.md" class="btn" style="background:#1B365D;">📄 Country Report (MD)</a>
            <a href="{repo_prefix}/reports/supervisors/{result.country_code.lower()}/country_profile.pdf" class="btn" style="background:#dc2626;">📕 PDF</a>
            <a href="{repo_prefix}/reports/supervisors/{result.country_code.lower()}/country_profile.docx" class="btn" style="background:#2563eb;">📥 Word</a>
            <a href="{repo_prefix}/reports/supervisors/{result.country_code.lower()}/country_profile.epub" class="btn" style="background:#059669;">📱 EPUB</a>
        </div>

        <h3 style="font-size:16px;color:#1B365D;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-bottom:14px;">Top Vetted Supervisors ({result.professors_count})</h3>
        {prof_cards_html}
    </div>
</div>
</body>
</html>"""

        return {
            "subject": subject,
            "text": text_body,
            "html": html_body
        }

    def render_country_briefing_html(
        self,
        result: CountryCampaignResult,
        repo_prefix: str = "https://github.com/mosesObaro/AlertMe/blob/main"
    ) -> str:
        """Renders responsive HTML briefing for a country campaign."""
        from .config import SUPPORTED_COUNTRIES, normalize_country_key
        country_key = normalize_country_key(result.country)
        campaign_data = SUPPORTED_COUNTRIES.get(country_key, {})
        campaign = CountryCampaign.from_dict({
            "country": result.country,
            "country_code": result.country_code,
            "currency": campaign_data.get("currency", "USD"),
            "immigration_dependant_guidance": campaign_data.get("immigration_dependant_guidance", ""),
            "dependant_visa_policy": campaign_data.get("dependant_visa_policy", ""),
            "immigration_disclaimer": campaign_data.get("immigration_disclaimer", ""),
            "target_deadline": campaign_data.get("target_deadline", "2026-12-01"),
            "primary_funding_vehicle": campaign_data.get("primary_funding_vehicle", "")
        })
        return self.render_country_email(result, campaign, repo_prefix)["html"]

    def send_country_alert(
        self,
        result: CountryCampaignResult,
        repo_prefix: str = "https://github.com/mosesObaro/AlertMe/blob/main",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Dispatches rendered country briefing via configured email provider."""
        from .config import SUPPORTED_COUNTRIES, normalize_country_key
        country_key = normalize_country_key(result.country)
        campaign_data = SUPPORTED_COUNTRIES.get(country_key, {})
        campaign = CountryCampaign.from_dict({
            "country": result.country,
            "country_code": result.country_code,
            "currency": campaign_data.get("currency", "USD"),
            "immigration_dependant_guidance": campaign_data.get("immigration_dependant_guidance", ""),
            "dependant_visa_policy": campaign_data.get("dependant_visa_policy", ""),
            "immigration_disclaimer": campaign_data.get("immigration_disclaimer", ""),
            "target_deadline": campaign_data.get("target_deadline", "2026-12-01"),
            "primary_funding_vehicle": campaign_data.get("primary_funding_vehicle", "")
        })
        payload = self.render_country_email(result, campaign, repo_prefix)

        if dry_run:
            return {"status": "dry_run", "subject": payload["subject"]}

        try:
            from src.email.sender import EmailSender
            sender = EmailSender()
            success = sender.send(payload["subject"], payload["html"], payload["text"])
            return {"status": "sent" if success else "failed", "subject": payload["subject"]}
        except Exception as e:
            return {"status": "failed", "error": str(e), "subject": payload["subject"]}

    def render_global_email(
        self,
        results: Dict[str, CountryCampaignResult],
        repo_prefix: str = "https://github.com/mosesObaro/AlertMe/blob/main"
    ) -> Dict[str, str]:
        """
        Renders an executive global briefing covering all 7 target countries.
        Returns {'subject': ..., 'html': ..., 'text': ...}.
        """
        total_profs = sum(r.professors_count for r in results.values())
        total_unis = sum(r.universities_count for r in results.values())
        total_funds = sum(r.funding_opportunities_count for r in results.values())
        
        subject = f"[PhD Intelligence Alert] Global PhD Funding & Supervisor Briefing: {total_profs} Vetted Supervisors across {len(results)} Countries"
        
        # Markdown body
        text_lines = [
            "# GLOBAL PhD FUNDING & SUPERVISOR INTELLIGENCE",
            f"Ecosystem Scope: {len(results)} Target Countries • {total_unis} Universities • {total_profs} Vetted Supervisors • {total_funds} Funding Opportunities",
            "",
            "## 1. Country Intelligence Overview",
            "| Country | Vetted Supervisors | Universities | Major Funding Vehicle | Reports (MD, PDF, DOCX, EPUB) |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        
        for c_key, res in results.items():
            primary_funding = res.funding_opportunities[0].title if res.funding_opportunities else "National Doctoral Schemes"
            code = res.country_code.lower()
            text_lines.append(f"| **{res.country}** ({res.country_code}) | {res.professors_count} professors | {res.universities_count} | {primary_funding} | [View Dossiers]({repo_prefix}/reports/supervisors/{code}/country_profile.md) |")
            
        text_lines.append("")
        text_lines.append("## 2. Featured Top Supervisors by Country")
        for c_key, res in results.items():
            code = res.country_code.lower()
            text_lines.append(f"### {res.country} ({res.country_code})")
            for p in res.professors[:3]:
                safe_id = p.name.lower().replace(" ", "_").replace(".", "")
                rec = p.recruitment.status if p.recruitment else "UNKNOWN"
                text_lines.append(f"* **{p.name}** ({p.university}) — Alignment: {p.alignment_score:.1f}% | Recruitment: {rec}")
                text_lines.append(f"  Focus: {', '.join(p.research_interests[:3])}")
                text_lines.append(f"  Dossier: {repo_prefix}/reports/supervisors/{code}/professors/{safe_id}/dossier.md")
            text_lines.append("")
            
        text_body = "\n".join(text_lines)
        
        # HTML body
        country_rows_html = ""
        for c_key, res in results.items():
            code = res.country_code.lower()
            funding_name = res.funding_opportunities[0].title if res.funding_opportunities else "National Doctoral Schemes"
            country_rows_html += f"""
            <tr style="border-bottom:1px solid #e2e8f0;">
                <td style="padding:10px 8px;font-weight:bold;color:#1e293b;">{res.country}</td>
                <td style="padding:10px 8px;text-align:center;"><span style="background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:bold;">{res.professors_count}</span></td>
                <td style="padding:10px 8px;text-align:center;color:#475569;">{res.universities_count}</td>
                <td style="padding:10px 8px;font-size:12px;color:#334155;">{funding_name[:36]}</td>
                <td style="padding:10px 8px;font-size:12px;white-space:nowrap;">
                    <a href="{repo_prefix}/reports/supervisors/{code}/country_profile.md" style="color:#2563eb;text-decoration:none;font-weight:bold;">MD</a> •
                    <a href="{repo_prefix}/reports/supervisors/{code}/country_profile.pdf" style="color:#dc2626;text-decoration:none;font-weight:bold;">PDF</a> •
                    <a href="{repo_prefix}/reports/supervisors/{code}/country_profile.docx" style="color:#2563eb;text-decoration:none;font-weight:bold;">Word</a> •
                    <a href="{repo_prefix}/reports/supervisors/{code}/country_profile.epub" style="color:#059669;text-decoration:none;font-weight:bold;">EPUB</a>
                </td>
            </tr>
            """

        country_sections_html = ""
        for c_key, res in results.items():
            code = res.country_code.lower()
            prof_cards = ""
            for p in res.professors[:3]:
                safe_name = p.name.lower().replace(" ", "_").replace(".", "")
                rec_status = p.recruitment.status if p.recruitment else "UNKNOWN"
                badge_color = "#15803d" if rec_status in ["CONFIRMED_ACTIVE", "STRONG_EVIDENCE"] else "#854d0e"
                badge_bg = "#dcfce7" if rec_status in ["CONFIRMED_ACTIVE", "STRONG_EVIDENCE"] else "#fef9c3"
                
                prof_cards += f"""
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div>
                            <strong style="color:#1e293b;font-size:14px;">{p.name}</strong>
                            <div style="font-size:12px;color:#64748b;">{p.university} • {p.department}</div>
                        </div>
                        <span style="background:{badge_bg};color:{badge_color};font-size:10px;font-weight:bold;padding:2px 6px;border-radius:8px;">{rec_status}</span>
                    </div>
                    <div style="font-size:12px;color:#334155;margin:6px 0;">
                        <strong>Research Fit: {p.alignment_score:.1f}%</strong> — {', '.join(p.research_interests[:3])}
                    </div>
                    <div style="font-size:11px;padding-top:6px;border-top:1px dashed #cbd5e1;">
                        <a href="{repo_prefix}/reports/supervisors/{code}/professors/{safe_name}/dossier.md" style="color:#2563eb;text-decoration:none;font-weight:bold;margin-right:8px;">📄 MD</a>
                        <a href="{repo_prefix}/reports/supervisors/{code}/professors/{safe_name}/dossier.pdf" style="color:#dc2626;text-decoration:none;font-weight:bold;margin-right:8px;">📕 PDF</a>
                        <a href="{repo_prefix}/reports/supervisors/{code}/professors/{safe_name}/dossier.docx" style="color:#2563eb;text-decoration:none;font-weight:bold;margin-right:8px;">📥 Word</a>
                        <a href="{repo_prefix}/reports/supervisors/{code}/professors/{safe_name}/dossier.epub" style="color:#059669;text-decoration:none;font-weight:bold;">📱 EPUB</a>
                    </div>
                </div>
                """
            
            country_sections_html += f"""
            <div style="margin-bottom:20px;">
                <h4 style="margin:0 0 10px;color:#1B365D;font-size:15px;border-bottom:2px solid #e2e8f0;padding-bottom:4px;">
                    {res.country} ({res.professors_count} Vetted Supervisors)
                </h4>
                {prof_cards}
            </div>
            """

        html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
.container {{ max-width: 720px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }}
.header {{ background: #1B365D; color: #ffffff; padding: 28px 24px; text-align: left; }}
.content {{ padding: 24px; }}
.metric-box {{ background: #f1f5f9; border-radius: 8px; padding: 14px; margin-bottom: 20px; }}
.table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px; }}
.btn {{ display: inline-block; background: #2563eb; color: #ffffff; padding: 8px 14px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: bold; margin-right: 8px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <span style="background:#3b82f6;color:#ffffff;font-size:11px;font-weight:bold;padding:3px 8px;border-radius:4px;text-transform:uppercase;">Global Executive Intelligence</span>
        <h1 style="margin:8px 0 4px;font-size:22px;">Global PhD Funding & Supervisor Intelligence</h1>
        <p style="margin:0;font-size:13px;opacity:0.9;">Scope: 7 Target Countries • {total_unis} Universities • {total_profs} Vetted Supervisors • {total_funds} Funding Opportunities</p>
    </div>
    <div class="content">
        <div class="metric-box">
            <h4 style="margin:0 0 8px;font-size:13px;text-transform:uppercase;color:#475569;">Global Summary</h4>
            <p style="margin:0 0 6px;font-size:13px;"><strong>Target Field:</strong> Edge Computing, Edge AI & Distributed Systems</p>
            <p style="margin:0 0 6px;font-size:13px;"><strong>All 7 Countries:</strong> United Kingdom, Japan, Germany, United States, Canada, Sweden, Hong Kong</p>
            <p style="margin:0;font-size:13px;"><strong>Quad-Format Deliverables:</strong> All Country Reports & Supervisor Dossiers compiled in Markdown, PDF, Word, and EPUB.</p>
        </div>

        <h3 style="font-size:16px;color:#1B365D;margin-bottom:10px;">Country Campaign Portfolio</h3>
        <table class="table">
            <thead>
                <tr style="background:#f1f5f9;border-bottom:2px solid #cbd5e1;text-align:left;">
                    <th style="padding:8px;">Country</th>
                    <th style="padding:8px;text-align:center;">Supervisors</th>
                    <th style="padding:8px;text-align:center;">Unis</th>
                    <th style="padding:8px;">Primary Funding</th>
                    <th style="padding:8px;">Reports</th>
                </tr>
            </thead>
            <tbody>
                {country_rows_html}
            </tbody>
        </table>

        <h3 style="font-size:16px;color:#1B365D;margin-bottom:14px;">Featured Supervisors by Country</h3>
        {country_sections_html}
    </div>
</div>
</body>
</html>"""

        return {
            "subject": subject,
            "text": text_body,
            "html": html_body
        }

    def send_global_alert(
        self,
        results: Dict[str, CountryCampaignResult],
        repo_prefix: str = "https://github.com/mosesObaro/AlertMe/blob/main",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Dispatches rendered global briefing via configured email provider."""
        payload = self.render_global_email(results, repo_prefix)

        if dry_run:
            return {"status": "dry_run", "subject": payload["subject"]}

        try:
            from src.email.sender import EmailSender
            sender = EmailSender()
            success = sender.send(payload["subject"], payload["html"], payload["text"])
            return {"status": "sent" if success else "failed", "subject": payload["subject"]}
        except Exception as e:
            return {"status": "failed", "error": str(e), "subject": payload["subject"]}
