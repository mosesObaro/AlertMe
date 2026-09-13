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
        1. Priority Tier (Tier 1 first)
        2. Active 7-day cycle in progress (< Day 7)
        3. Lowest familiarity score to close research gaps
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

        # Check if any candidate is currently in an active 7-day cycle (> 1 and <= 7)
        for r in sorted_candidates:
            fam = self.storage.familiarity.get(r.researcher_id, FamiliarityRecord(researcher_id=r.researcher_id))
            if 1 < fam.exposure_cycle_day <= 7:
                return r

        # Otherwise pick the Tier 1 candidate with the lowest familiarity score
        tier1_candidates = [r for r in sorted_candidates if r.priority_tier == "Tier 1"]
        if tier1_candidates:
            tier1_candidates.sort(
                key=lambda r: self.storage.familiarity.get(r.researcher_id, FamiliarityRecord(researcher_id=r.researcher_id)).familiarity_score
            )
            return tier1_candidates[0]

        return sorted_candidates[0]

    def generate_daily_alert(self, reference_date: Optional[date] = None) -> Optional[DailyAlert]:
        """
        Generates the standard structured daily alert according to the 7-day progressive exposure cycle.
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

        if cycle_day == 1:
            focus_title = "Researcher Introduction & Edge Relevance"
            selected_pub = seminal_pub
            trajectory_text = (
                f"{supervisor.name} has shaped modern systems research. "
                f"Trajectory: {supervisor.research_trajectory}"
            )
            action_text = f"Review {supervisor.name}'s official lab website and note current group members and active projects."
            next_step = f"Tomorrow (Day 2): Deconstruct foundational publication '{selected_pub.title if selected_pub else 'Key Paper'}'."
        elif cycle_day == 2:
            focus_title = "Foundational / Seminal Research Deconstruction"
            selected_pub = seminal_pub
            trajectory_text = (
                f"This foundational work established {supervisor.name}'s reputation. "
                f"It tackled fundamental systems limits that still impact current edge architectures."
            )
            action_text = f"Read the abstract and introduction of '{selected_pub.title if selected_pub else 'Paper'}' and extract the core system model."
            next_step = f"Tomorrow (Day 3): Trace how {supervisor.name}'s research evolved toward modern Edge AI and cloud-edge continuum."
        elif cycle_day == 3:
            focus_title = "Research Evolution Across Key Papers"
            selected_pub = pubs[1] if len(pubs) > 1 else seminal_pub
            trajectory_text = (
                f"Progression: Moved from general distributed networking toward "
                f"{', '.join(supervisor.research_interests[:3])}."
            )
            action_text = "Compare the baseline assumptions between their early work and recent edge computing frameworks."
            next_step = f"Tomorrow (Day 4): Deep dive into recent publication '{recent_pub.title if recent_pub else 'Recent Paper'}'."
        elif cycle_day == 4:
            focus_title = "Recent Breakthrough Research (Past 1-2 Years)"
            selected_pub = recent_pub
            trajectory_text = (
                f"State-of-the-Art: Current publications address real-time edge constraints using "
                f"{supervisor.research_methods[0] if supervisor.research_methods else 'optimization and testbeds'}."
            )
            action_text = f"Deconstruct the evaluation section of '{selected_pub.title if selected_pub else 'Paper'}' (metrics, baselines, and testbeds)."
            next_step = f"Tomorrow (Day 5): Analyze active research grants and current lab projects."
        elif cycle_day == 5:
            focus_title = "Current Research Direction & Active Grants"
            selected_pub = recent_pub
            trajectory_text = (
                f"Active Projects: {'; '.join(supervisor.current_projects)}. "
                f"These funded projects represent the exact areas where new PhD students will be funded."
            )
            action_text = f"Select one of the active project topics ({supervisor.current_projects[0] if supervisor.current_projects else 'Edge AI'}) as a target proposal seed."
            next_step = f"Tomorrow (Day 6): Inspect simulation tools, datasets, and systems testbeds used by {supervisor.name}."
        elif cycle_day == 6:
            focus_title = "Research Methodology, Simulators & Testbeds"
            selected_pub = recent_pub
            trajectory_text = (
                f"Methodological Toolkit: Simulators ({', '.join(supervisor.simulation_tools)}), "
                f"Testbeds ({', '.join(supervisor.systems_testbeds)}), and Datasets ({', '.join(supervisor.datasets)})."
            )
            action_text = f"Check if you have experience with {supervisor.simulation_tools[0] if supervisor.simulation_tools else 'EdgeCloudSim'} from the Edge Computing curriculum."
            next_step = f"Tomorrow (Day 7): Formulate specific PhD Research Questions and prepare supervisor outreach."
        else: # Day 7
            focus_title = "PhD Research Alignment & Outreach Formulation"
            selected_pub = recent_pub
            trajectory_text = (
                f"Synthesis: You now have a complete picture of {supervisor.name}'s trajectory, "
                f"seminal papers, recent methods, and current projects."
            )
            action_text = (
                f"Draft a concise, personalized outreach email citing '{recent_pub.title if recent_pub else 'recent work'}' "
                f"and proposing a 1-paragraph research question extending their work."
            )
            next_step = f"Cycle complete for {supervisor.name}! Tomorrow: Advance to next high-priority supervisor candidate."

        # Connect scholarship
        matched_scholarship = next(
            (s for s in self.storage.scholarships.values() if s.university == supervisor.university),
            list(self.storage.scholarships.values())[0] if self.storage.scholarships else None
        )

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
            next_action=next_step
        )

        self.storage.record_alert(alert)
        return alert
