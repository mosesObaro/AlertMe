"""
Data models for the Hong Kong PhD Supervisor Intelligence module.
Provides strongly-typed dataclasses for universities, researchers, publications,
recruitment evidence, scholarships, opportunities, and daily intelligence alerts.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class UniversityProfile:
    university_id: str
    canonical_name: str
    aliases: List[str]
    official_url: str
    graduate_school_url: str
    research_url: str
    phd_application_url: str
    scholarship_url: str
    relevant_departments: List[str]
    relevant_research_centres: List[str]
    last_verified: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniversityProfile":
        return cls(**data)

@dataclass
class Publication:
    publication_id: str
    title: str
    authors: List[str]
    year: int
    venue: str
    doi_or_url: str
    research_problem: str
    approach: str
    key_contribution: str
    edge_relevance: str
    is_seminal: bool = False
    is_recent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Publication":
        return cls(**data)

@dataclass
class RecruitmentEvidence:
    status: str  # CONFIRMED_ACTIVE, STRONG_EVIDENCE, POSSIBLE, UNKNOWN, NOT_CURRENTLY_RECRUITING, RECRUITMENT_STALE
    confidence: float  # 0.0 to 1.0
    evidence_text: str
    source_url: str
    source_type: str  # official_lab_website, faculty_homepage, call_for_phd, department_directory
    source_date: str  # YYYY-MM-DD
    last_verified: str  # YYYY-MM-DD

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecruitmentEvidence":
        return cls(**data)

@dataclass
class ResearcherProfile:
    researcher_id: str
    name: str
    university: str
    department: str
    position: str
    research_group: str
    official_profile_url: str
    personal_website: str
    google_scholar: str
    orcid: str
    dblp: str
    research_interests: List[str]
    research_summary: str
    edge_relevance: str
    research_trajectory: str
    current_projects: List[str]
    research_methods: List[str]
    datasets: List[str]
    simulation_tools: List[str]
    systems_testbeds: List[str]
    recruitment: RecruitmentEvidence
    potential_phd_topics: List[str]
    potential_alignment: str
    priority_tier: str  # Tier 1, Tier 2, Tier 3
    relevant_curriculum_weeks: List[int] = field(default_factory=list)
    relevant_curriculum_courses: List[str] = field(default_factory=list)
    publications: List[Publication] = field(default_factory=list)
    alignment_score: float = 0.0
    familiarity_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearcherProfile":
        data = dict(data)
        if isinstance(data.get("recruitment"), dict):
            data["recruitment"] = RecruitmentEvidence.from_dict(data["recruitment"])
        if "publications" in data:
            data["publications"] = [
                Publication.from_dict(p) if isinstance(p, dict) else p
                for p in data["publications"]
            ]
        return cls(**data)

@dataclass
class Scholarship:
    scholarship_id: str
    university: str
    scholarship_name: str
    phd_program: str
    eligibility: str
    application_deadline: str
    funding_amount: str
    tuition_coverage: str
    living_allowance: str
    duration: str
    dependent_support: str
    supervisor_requirement: str
    application_requirements: str
    official_url: str
    source: str
    last_verified: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scholarship":
        return cls(**data)

@dataclass
class Opportunity:
    opportunity_id: str
    university: str
    phd_program: str
    scholarship: Scholarship
    supervisor: ResearcherProfile
    research_alignment_score: float
    recruitment_score: float
    scholarship_quality_score: float
    application_feasibility_score: float
    deadline_urgency_score: float
    familiarity_gap_score: float
    composite_opportunity_score: float
    priority: str  # High, Medium, Low
    days_remaining: int
    status: str = "Identified"  # Identified, Shortlisted, Outreach Sent, Applying, Submitted

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class FamiliarityRecord:
    researcher_id: str
    papers_exposed: List[str] = field(default_factory=list)
    papers_read: List[str] = field(default_factory=list)
    topics_exposed: List[str] = field(default_factory=list)
    research_projects_exposed: List[str] = field(default_factory=list)
    research_trajectory_understood: bool = False
    recruitment_verified: bool = False
    familiarity_score: float = 0.0
    last_exposed: Optional[str] = None
    exposure_cycle_day: int = 1  # 1 through 7

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FamiliarityRecord":
        return cls(**data)

@dataclass
class DailyAlert:
    alert_id: str
    date: str
    weeks_remaining: int
    days_remaining: int
    university: str
    professor: str
    department: str
    research_group: str
    priority_tier: str
    research_alignment_pct: int
    recruitment_status: str
    recruitment_evidence: str
    cycle_day: int
    today_research_focus: str
    paper_title: str
    paper_author: str
    paper_year: int
    paper_link: str
    research_problem: str
    approach: str
    key_contribution: str
    why_it_matters_for_edge: str
    research_trajectory: str
    what_to_read_next: str
    potential_phd_alignment: str
    application_action_today: str
    scholarship_connection: str
    deadline_info: str
    next_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        """Formats the alert matching the prompt's required daily alert specification."""
        return f"""HONG KONG PHD SUPERVISOR INTELLIGENCE

Date: {self.date}
Weeks Remaining: {self.weeks_remaining}
Days Remaining: {self.days_remaining}

UNIVERSITY: {self.university}
Professor: {self.professor}
Department: {self.department}
Research Group: {self.research_group}

SUPERVISOR PRIORITY: {self.priority_tier}
RESEARCH ALIGNMENT: {self.research_alignment_pct}%
RECRUITMENT STATUS: {self.recruitment_status}
RECRUITMENT EVIDENCE: {self.recruitment_evidence}

TODAY'S RESEARCH FOCUS (Day {self.cycle_day} of 7-Day Familiarity Cycle):
Focus: {self.today_research_focus}

Paper: {self.paper_title}
Author: {self.paper_author}
Year: {self.paper_year}
Link: {self.paper_link}

RESEARCH PROBLEM:
{self.research_problem}

APPROACH:
{self.approach}

KEY CONTRIBUTION:
{self.key_contribution}

WHY THIS MATTERS FOR EDGE COMPUTING:
{self.why_it_matters_for_edge}

RESEARCH TRAJECTORY:
{self.research_trajectory}

WHAT TO READ NEXT:
{self.what_to_read_next}

POTENTIAL PHD ALIGNMENT:
{self.potential_phd_alignment}

APPLICATION ACTION TODAY:
{self.application_action_today}

SCHOLARSHIP CONNECTION:
{self.scholarship_connection}

DEADLINE:
{self.deadline_info}

NEXT ACTION:
{self.next_action}
"""

    def to_html(self) -> str:
        """Renders a polished, modern, responsive HTML email for the supervisor intelligence alert."""
        recruitment_badge_color = "#10B981" if "ACTIVE" in self.recruitment_status else "#3B82F6" if "STRONG" in self.recruitment_status else "#6B7280"
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[HK PhD Supervisor Alert] Day {self.cycle_day}/7: {self.professor} ({self.university})</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F3F4F6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1F2937;">
  <div style="max-width: 680px; margin: 24px auto; background-color: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
    
    <!-- Top Header -->
    <div style="background: linear-gradient(135deg, #1B365D 0%, #0F2537 100%); padding: 28px 24px; color: #FFFFFF;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span style="font-size: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #93C5FD;">Hong Kong PhD Supervisor Intelligence</span>
        <span style="background-color: #2563EB; color: #FFFFFF; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 9999px;">⏳ {self.weeks_remaining} WEEKS TO DEC 1</span>
      </div>
      <h1 style="margin: 0 0 6px 0; font-size: 22px; font-weight: 800; line-height: 1.3;">{self.professor}</h1>
      <p style="margin: 0; font-size: 14px; color: #E0E7FF;">{self.university} &bull; {self.department}</p>
    </div>

    <!-- Subheader Stats Bar -->
    <div style="background-color: #F8FAFC; border-bottom: 1px solid #E2E8F0; padding: 12px 24px; font-size: 12px; line-height: 1.8;">
      <span style="margin-right: 16px;"><strong>Priority:</strong> <span style="color: #1B365D; font-weight: 700;">{self.priority_tier}</span></span>
      <span style="margin-right: 16px;"><strong>Alignment:</strong> <span style="color: #059669; font-weight: 700;">{self.research_alignment_pct}% Match</span></span>
      <span style="margin-right: 16px;"><strong>Recruitment:</strong> <span style="color: {recruitment_badge_color}; font-weight: 700;">● {self.recruitment_status}</span></span>
      <span><strong>Cycle:</strong> <span style="color: #4F46E5; font-weight: 700;">Day {self.cycle_day} of 7</span></span>
    </div>

    <!-- Main Content Body -->
    <div style="padding: 24px;">
      
      <!-- Recruitment Evidence Callout -->
      <div style="background-color: #ECFDF5; border-left: 4px solid #10B981; padding: 14px 16px; border-radius: 4px; margin-bottom: 24px;">
        <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #065F46; margin-bottom: 4px;">Verified Recruitment Evidence</div>
        <div style="font-size: 13px; font-style: italic; color: #047857; line-height: 1.5;">&ldquo;{self.recruitment_evidence}&rdquo;</div>
      </div>

      <!-- Today's Research Focus Card -->
      <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #2563EB;">TODAY'S RESEARCH FOCUS (DAY {self.cycle_day})</span>
          <span style="font-size: 12px; color: #64748B;">{self.date}</span>
        </div>
        <h2 style="margin: 0 0 8px 0; font-size: 17px; font-weight: 700; color: #0F172A;">{self.today_research_focus}</h2>
        <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 14px; margin-top: 12px;">
          <div style="font-size: 15px; font-weight: 700; color: #1E293B; margin-bottom: 4px;">{self.paper_title}</div>
          <div style="font-size: 12px; color: #64748B; margin-bottom: 10px;">{self.paper_author} ({self.paper_year})</div>
          <a href="{self.paper_link}" style="display: inline-block; background-color: #1B365D; color: #FFFFFF; text-decoration: none; font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 4px;">Read Publication / DOI &rarr;</a>
        </div>
      </div>

      <!-- Deconstruction Sections -->
      <div style="margin-bottom: 24px;">
        <div style="margin-bottom: 16px;">
          <h3 style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; color: #64748B;">📌 Research Problem</h3>
          <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #1E293B;">{self.research_problem}</p>
        </div>

        <div style="margin-bottom: 16px;">
          <h3 style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; color: #64748B;">⚙️ Proposed Approach</h3>
          <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #1E293B;">{self.approach}</p>
        </div>

        <div style="margin-bottom: 16px;">
          <h3 style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; color: #64748B;">🎯 Key Contribution</h3>
          <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #1E293B;">{self.key_contribution}</p>
        </div>

        <div style="margin-bottom: 16px;">
          <h3 style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; color: #64748B;">🌐 Why This Matters for Edge Computing</h3>
          <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #1E293B;">{self.why_it_matters_for_edge}</p>
        </div>

        <div style="margin-bottom: 16px;">
          <h3 style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; color: #64748B;">📈 Research Trajectory</h3>
          <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #1E293B;">{self.research_trajectory}</p>
        </div>

        <div style="margin-bottom: 16px;">
          <h3 style="margin: 0 0 4px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; color: #64748B;">📖 What to Read Next</h3>
          <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #1E293B;">{self.what_to_read_next}</p>
        </div>
      </div>

      <!-- Action Items & Proposal Formulation -->
      <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 18px; margin-bottom: 24px;">
        <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #1D4ED8; margin-bottom: 10px;">PhD Proposal &amp; Outreach Strategy</div>
        
        <div style="margin-bottom: 10px;">
          <div style="font-size: 12px; font-weight: 600; color: #1E40AF;">🎓 Potential PhD Topics:</div>
          <div style="font-size: 13px; color: #1E3A8A; line-height: 1.4;">{self.potential_phd_alignment}</div>
        </div>

        <div style="margin-bottom: 10px;">
          <div style="font-size: 12px; font-weight: 600; color: #1E40AF;">✅ Today's Action Item:</div>
          <div style="font-size: 13px; color: #1E3A8A; line-height: 1.4;">{self.application_action_today}</div>
        </div>

        <div>
          <div style="font-size: 12px; font-weight: 600; color: #1E40AF;">⏭️ Next Step (Tomorrow):</div>
          <div style="font-size: 13px; color: #1E3A8A; line-height: 1.4;">{self.next_action}</div>
        </div>
      </div>

      <!-- Funding Scheme & Deadlines -->
      <div style="background-color: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; padding: 18px; margin-bottom: 24px;">
        <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #B45309; margin-bottom: 8px;">💰 Target Scholarship &amp; Deadline</div>
        <div style="font-size: 13px; color: #92400E; margin-bottom: 6px;"><strong>Funding Scheme:</strong> {self.scholarship_connection}</div>
        <div style="font-size: 13px; color: #92400E;"><strong>Deadline:</strong> {self.deadline_info}</div>
      </div>

    </div>

    <!-- Footer -->
    <div style="background-color: #F8FAFC; border-top: 1px solid #E2E8F0; padding: 20px 24px; font-size: 11px; color: #64748B; line-height: 1.5;">
      <p style="margin: 0 0 8px 0;"><strong>Notice:</strong> This briefing is automatically synthesized by the Hong Kong PhD Supervisor Intelligence module on behalf of the Edge Computing PhD Curriculum &amp; Tracker.</p>
      <p style="margin: 0 0 8px 0;">Visa and dependant accompaniment regulations are subject to statutory changes by national immigration authorities. Verify all requirements directly with the official immigration department and university international office before submitting applications.</p>
      <p style="margin: 0;">AlertMe &bull; Edge Computing PhD Intelligence System &bull; Open Source</p>
    </div>

  </div>
</body>
</html>"""

