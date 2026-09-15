"""
Daily research intelligence alert generator with spaced 7-day progressive exposure.
Progressively teaches the applicant about each supervisor's trajectory, seminal papers,
methodologies, and alignment opportunities while suppressing duplicate alerts.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from .models import ResearcherProfile, Publication, DailyAlert, FamiliarityRecord, Scholarship
from .storage import StorageManager
from .campaign import CampaignManager

class AlertGenerator:
    """Generates daily progressive intelligence briefings for Hong Kong PhD supervisors."""

    def __init__(self, storage: StorageManager, campaign: CampaignManager):
        self.storage = storage
        self.campaign = campaign

    def select_daily_supervisor(self) -> Optional[ResearcherProfile]:
        """
        Selects the most suitable researcher for today's briefing based on:
        1. In-progress transition for Prof. Cao (Day 6 merged final synthesis)
        2. Active 3-day cycle in progress (Day 2 or Day 3)
        3. Next uncompleted Tier 1 / high-alignment candidate
        4. Round-robin fallback if all candidates completed
        """
        all_researchers = list(self.storage.researchers.values())
        if not all_researchers:
            return None

        # Sort researchers: Tier 1 first, then by alignment score descending
        tier_weights = {"Tier 1": 3, "Tier 2": 2, "Tier 3": 1}
        sorted_candidates = sorted(
            all_researchers,
            key=lambda r: (tier_weights.get(r.priority_tier, 1), r.alignment_score),
            reverse=True
        )

        # Check if Prof. Cao has a pending Day 6 final synthesis
        cao_fam = self.storage.familiarity.get("polyu_cao_jiannong")
        if cao_fam and not cao_fam.cycle_completed and cao_fam.exposure_cycle_day >= 6:
            return self.storage.researchers.get("polyu_cao_jiannong")

        # 1. Check if any candidate is currently in an active, in-progress 3-day cycle (Day 2 or Day 3)
        for r in sorted_candidates:
            fam = self.storage.familiarity.get(r.researcher_id, FamiliarityRecord(researcher_id=r.researcher_id))
            if not fam.cycle_completed and 1 < fam.exposure_cycle_day <= 3:
                return r

        # 2. Otherwise pick the highest-priority candidate who has NOT yet completed a 3-day cycle
        uncompleted = [
            r for r in sorted_candidates
            if not self.storage.familiarity.get(r.researcher_id, FamiliarityRecord(researcher_id=r.researcher_id)).cycle_completed
        ]
        if uncompleted:
            return uncompleted[0]

        # 3. Fallback: If all candidates have completed a cycle, sort by lowest familiarity or oldest exposure
        sorted_by_familiarity = sorted(
            sorted_candidates,
            key=lambda r: (
                self.storage.familiarity.get(r.researcher_id, FamiliarityRecord(researcher_id=r.researcher_id)).familiarity_score,
                self.storage.familiarity.get(r.researcher_id, FamiliarityRecord(researcher_id=r.researcher_id)).last_exposed or ""
            )
        )
        return sorted_by_familiarity[0]

    def generate_daily_alert(self, reference_date: Optional[date] = None) -> Optional[DailyAlert]:
        """
        Generates the standard structured daily alert according to the 3-day progressive exposure cycle,
        including dossier generation on Day 3 (or Final Synthesis).
        """
        ref_date = reference_date or date.today()
        time_info = self.campaign.get_time_remaining(ref_date)
        
        supervisor = self.select_daily_supervisor()
        if not supervisor:
            return None

        fam = self.storage.familiarity.get(
            supervisor.researcher_id,
            FamiliarityRecord(researcher_id=supervisor.researcher_id)
        )
        cycle_day = fam.exposure_cycle_day

        # Select corresponding publication
        pubs = supervisor.publications
        seminal_pub = next((p for p in pubs if getattr(p, "is_seminal", False)), pubs[0] if pubs else None)
        recent_pub = next((p for p in pubs if getattr(p, "is_recent", False)), pubs[-1] if pubs else None)

        # Connect scholarship
        matched_scholarship = next(
            (s for s in self.storage.scholarships.values() if s.university == supervisor.university),
            list(self.storage.scholarships.values())[0] if self.storage.scholarships else None
        )

        # Check if this alert completes the cycle (Day 3 or Cao final synthesis)
        is_cao_final = (supervisor.researcher_id == "polyu_cao_jiannong" and cycle_day >= 6)
        is_synthesis_day = is_cao_final or (cycle_day == 3)

        dossier_report_link = None
        dossier_docx_link = None
        dossier_pdf_link = None
        dossier_epub_link = None

        if is_synthesis_day:
            try:
                from .profiler import SupervisorProfiler
                profiler = SupervisorProfiler()
                dossier_files = profiler.generate_all_dossiers(supervisor, matched_scholarship, ref_date)
                dossier_report_link = dossier_files.get("markdown_url")
                dossier_docx_link = dossier_files.get("docx_url")
                dossier_pdf_link = dossier_files.get("pdf_url")
                dossier_epub_link = dossier_files.get("epub_url")
            except Exception as e:
                print(f"Warning: Dossier generation encountered an error ({e}).")

        if is_cao_final:
            focus_title = "Final Synthesis: Methodology, Testbeds & PhD Proposal Outreach"
            selected_pub = recent_pub
            trajectory_text = (
                f"Comprehensive Synthesis: You have evaluated {supervisor.name}'s distributed computing foundations, "
                f"EdgeMesh framework, and 2024 early-exit Edge AI inference. "
                f"Methodological Toolkit: Simulators ({', '.join(supervisor.simulation_tools)}), "
                f"Testbeds ({', '.join(supervisor.systems_testbeds)}), and Active Grants ({'; '.join(supervisor.current_projects)})."
            )
            action_text = (
                f"Download the complete 30-section Dossier (Markdown, PDF, DOCX, EPUB). "
                f"Draft your personalized 1-paragraph outreach email citing the 2024 early-exit paper and proposing a split-inference thesis extension."
            )
            next_step = f"Deep Dive complete for {supervisor.name}! Starting tomorrow: Advance to next high-priority supervisor (Prof. Song Guo / Prof. Wei Wang)."
        elif cycle_day == 1:
            focus_title = "Foundational & Seminal Research Deconstruction"
            selected_pub = seminal_pub
            trajectory_text = (
                f"{supervisor.name} has shaped modern systems research. "
                f"Trajectory: {supervisor.research_trajectory}"
            )
            action_text = f"Review {supervisor.name}'s official lab website and extract core systems models from '{selected_pub.title if selected_pub else 'Key Paper'}'."
            next_step = f"Tomorrow (Day 2): Deep dive into recent breakthrough publications (past 1-2 years), active grants, and methodology."
        elif cycle_day == 2:
            focus_title = "Recent Breakthroughs, Methodology & Active Grants"
            selected_pub = recent_pub
            trajectory_text = (
                f"State-of-the-Art: Active Projects: {'; '.join(supervisor.current_projects)}. "
                f"Methodologies: Simulators ({', '.join(supervisor.simulation_tools)}), Testbeds ({', '.join(supervisor.systems_testbeds)})."
            )
            action_text = f"Deconstruct the evaluation section of '{selected_pub.title if selected_pub else 'Recent Paper'}' and select an active project topic as a thesis anchor."
            next_step = f"Tomorrow (Day 3): Synthesize PhD proposal alignment, target scholarships, and release the complete 4-format suitability dossier."
        else:  # Day 3
            focus_title = "PhD Proposal Alignment, Target Scholarships & Outreach Formulation"
            selected_pub = recent_pub
            trajectory_text = (
                f"Synthesis: You now have a complete picture of {supervisor.name}'s trajectory, "
                f"seminal papers, recent methods, and funded projects."
            )
            action_text = (
                f"Download the 30-section Suitability Dossier (PDF/DOCX/EPUB). "
                f"Finalize a personalized 1-paragraph outreach email citing '{recent_pub.title if recent_pub else 'recent work'}' targeting their active grants."
            )
            next_step = f"3-Day Deep Dive complete for {supervisor.name}! Tomorrow: Advance to next high-priority supervisor candidate."

        sch_conn = (
            f"{matched_scholarship.scholarship_name if matched_scholarship else 'HKPFS / University PGS'} "
            f"({matched_scholarship.funding_amount if matched_scholarship else 'HK$331,200/yr'}). "
            f"Supervisor endorsement significantly strengthens departmental ranking."
        )

        deadline_str = (
            f"{matched_scholarship.application_deadline if matched_scholarship else '2026-12-01'} "
            f"({time_info['days_remaining']} days / {time_info['weeks_remaining']} weeks remaining)"
        )

        p_title = selected_pub.title if selected_pub else "Edge Computing Systems Paper"
        p_author = ", ".join(selected_pub.authors[:3]) if selected_pub else supervisor.name
        p_year = selected_pub.year if selected_pub else 2024
        p_link = selected_pub.doi_or_url if selected_pub else supervisor.official_profile_url
        p_prob = selected_pub.research_problem if selected_pub else "Handling dynamic edge constraints and latency limits."
        p_appr = selected_pub.approach if selected_pub else "Collaborative edge scheduling and decentralized inference."
        p_contr = selected_pub.key_contribution if selected_pub else "Significantly reduced latency and energy consumption."
        p_rel = selected_pub.edge_relevance if selected_pub else supervisor.edge_relevance

        alert = DailyAlert(
            alert_id=f"{supervisor.researcher_id}_day{cycle_day}_{ref_date.strftime('%Y%m%d')}",
            date=ref_date.strftime("%Y-%m-%d"),
            weeks_remaining=time_info["weeks_remaining"],
            days_remaining=time_info["days_remaining"],
            university=supervisor.university,
            professor=supervisor.name,
            department=supervisor.department,
            research_group=supervisor.research_group,
            priority_tier=supervisor.priority_tier,
            research_alignment_pct=int(supervisor.alignment_score),
            recruitment_status=supervisor.recruitment.status,
            recruitment_evidence=f"{supervisor.recruitment.evidence_text} [Source: {supervisor.recruitment.source_type}, Date: {supervisor.recruitment.source_date}]",
            cycle_day=cycle_day,
            today_research_focus=focus_title,
            paper_title=p_title,
            paper_author=p_author,
            paper_year=p_year,
            paper_link=p_link,
            research_problem=p_prob,
            approach=p_appr,
            key_contribution=p_contr,
            why_it_matters_for_edge=p_rel,
            research_trajectory=trajectory_text,
            what_to_read_next=f"Follow up with '{recent_pub.title if recent_pub else p_title}' for current extensions.",
            potential_phd_alignment=f"Potential PhD Topics: {'; '.join(supervisor.potential_phd_topics[:2])}.",
            application_action_today=action_text,
            scholarship_connection=sch_conn,
            deadline_info=deadline_str,
            next_action=next_step,
            dossier_report_link=dossier_report_link,
            dossier_docx_link=dossier_docx_link,
            dossier_pdf_link=dossier_pdf_link,
            dossier_epub_link=dossier_epub_link
        )

        self.storage.record_alert(alert)
        return alert
