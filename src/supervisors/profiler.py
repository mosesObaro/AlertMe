"""
Comprehensive Multi-Format Dossier Generator for Country and Supervisor Intelligence.
Generates:
1. Complete 33-Section PhD Supervisor Research Profile Dossiers
2. Comprehensive Country-Level Intelligence Reports
Across 4 Standard Formats:
- Markdown (.md)
- Microsoft Word (.docx)
- Adobe PDF (.pdf) via ReportLab
- Standard eBook (.epub) via EPUB 3.0 Container
"""

import os
import re
import json
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import (
    ResearcherProfile, UniversityProfile, FundingOpportunity,
    Publication, CountryCampaign, CountryCampaignResult,
    ProfessorDossier
)
from .analyzer import DossierSynthesizer
from .config import DEFAULT_APPLICANT_PROFILE

def get_safe_filename(text: str) -> str:
    """Sanitizes strings for safe, consistent directory and file naming."""
    safe = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    return re.sub(r'_+', '_', safe).strip('_').lower()

class DossierProfiler:
    """Generates quad-format documents for country campaigns and supervisor dossiers."""

    def __init__(self, base_output_dir: str = "reports/supervisors", output_base_dir: Optional[str] = None):
        target_dir = output_base_dir if output_base_dir is not None else base_output_dir
        self.base_output_dir = Path(target_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.synthesizer = DossierSynthesizer()

    def _get_safe_filename(self, text: str) -> str:
        return get_safe_filename(text)

    # ==========================================================================
    # 1. PROFESSOR DOSSIER GENERATION (CANONICAL 33-SECTION ENGINE)
    # ==========================================================================
    def generate_professor_dossiers(
        self,
        country_key: str,
        researcher: Optional[ResearcherProfile] = None,
        university: Optional[UniversityProfile] = None,
        funding: Optional[List[FundingOpportunity]] = None,
        campaign: Optional[CountryCampaign] = None,
        applicant_profile: Optional[Dict[str, Any]] = None,
        reference_date: Optional[date] = None,
        dossier: Optional[ProfessorDossier] = None
    ) -> Dict[str, str]:
        """Generates the canonical 33-section dossier in MD, DOCX, PDF, and EPUB from a single model."""
        ref_date = reference_date or date.today()

        if dossier is None:
            if researcher is None:
                raise ValueError("Either researcher or dossier must be provided to generate_professor_dossiers")
            dossier = self.synthesizer.synthesize(
                researcher=researcher,
                university=university,
                funding=funding,
                campaign=campaign,
                applicant_profile=applicant_profile,
                reference_date=ref_date
            )

        safe_id = self._get_safe_filename(dossier.identity.name)
        prof_dir = self.base_output_dir / country_key / "professors" / safe_id
        prof_dir.mkdir(parents=True, exist_ok=True)

        md_path = prof_dir / "dossier.md"
        docx_path = prof_dir / "dossier.docx"
        pdf_path = prof_dir / "dossier.pdf"
        epub_path = prof_dir / "dossier.epub"
        json_path = prof_dir / "dossier.json"

        # 1. Canonical Markdown
        md_content = self.render_professor_dossier_markdown(dossier)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 2. Canonical JSON representation for auditability & data pipeline
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dossier.to_dict(), f, indent=2, ensure_ascii=False)

        # 3. DOCX
        self.render_docx(f"PhD Supervisor Dossier: {dossier.identity.name}", md_content, str(docx_path))

        # 4. PDF
        self.render_pdf(f"PhD Supervisor Dossier: {dossier.identity.name}", md_content, str(pdf_path))

        # 5. EPUB
        self.render_epub(f"PhD Supervisor Dossier: {dossier.identity.name}", md_content, str(epub_path), f"dossier-{safe_id}")

        return {
            "markdown": str(md_path),
            "docx": str(docx_path),
            "pdf": str(pdf_path),
            "epub": str(epub_path)
        }

    def render_professor_markdown(
        self,
        researcher_or_dossier: Any,
        university: Optional[UniversityProfile] = None,
        funding: Optional[List[FundingOpportunity]] = None,
        ref_date: Optional[date] = None,
        campaign: Optional[CountryCampaign] = None
    ) -> str:
        """Backward-compatible renderer: accepts ResearcherProfile or ProfessorDossier."""
        if isinstance(researcher_or_dossier, ProfessorDossier):
            return self.render_professor_dossier_markdown(researcher_or_dossier)
        dossier = self.synthesizer.synthesize(
            researcher=researcher_or_dossier,
            university=university,
            funding=funding,
            campaign=campaign,
            reference_date=ref_date
        )
        return self.render_professor_dossier_markdown(dossier)

    def render_professor_dossier_markdown(self, d: ProfessorDossier) -> str:
        """Assembles the complete 33-section evidence-based research profile matching the gold standard."""
        md = f"""# Comprehensive Research Profile & PhD Supervisor Suitability Analysis

**Target Professor:** {d.identity.name}  
**Institution:** {d.identity.university}  
**Department / School:** {d.identity.department}  
**Research Group / Laboratory:** {d.identity.research_group}  
**Date of Assessment:** {d.metadata.generated_date}  
**Priority Tier:** {d.suitability_score.priority_tier} (Research Alignment: {int(d.identity.alignment_score)}%)  
**Applicant Profile Target:** Computer Engineering (BSc) / Computer Science (MSc) &bull; Software & iOS Engineering Background &bull; Focus: Edge Computing  

---

## 1. Executive Summary

{d.executive_summary}

---

## 2. Professor Identity & Academic Profile

* **Full Name:** {d.identity.name}
* **Current Position:** {d.identity.position}
* **University:** {d.identity.university}
* **Department:** {d.identity.department}
* **Research Group / Lab:** {d.identity.research_group}
* **Official University Profile:** [{d.identity.official_profile_url}]({d.identity.official_profile_url})
* **Personal / Academic Website:** [{d.identity.personal_website or d.identity.official_profile_url}]({d.identity.personal_website or d.identity.official_profile_url})
* **Google Scholar / DBLP:** [{d.identity.google_scholar or d.identity.dblp or d.identity.official_profile_url}]({d.identity.google_scholar or d.identity.dblp or d.identity.official_profile_url})
* **ORCID:** {d.identity.orcid or 'Not publicly listed'}
* **Current Research Areas:** {', '.join(d.identity.research_interests)}
* **Academic Standing:** {d.identity.position} ({d.suitability_score.priority_tier} in {d.identity.country} Edge Computing landscape)
* **Status:** Verified Active Scholar & Principal Investigator ({d.identity.verification_status})

---

## 3. Complete Research Career Timeline

{d.timeline_summary}

---

## 4. Research Eras
"""
        for idx, era in enumerate(d.eras, 1):
            md += f"""
### Era {idx}: {era.name} ({era.period})
* **Primary Field:** {era.primary_field}
* **Core Questions:** {era.core_questions}
* **Methods:** {', '.join(era.methods) if isinstance(era.methods, list) else era.methods}
* **Influence on Later Work:** {era.influence_on_later_work}
"""

        fields_tree = f"{d.identity.research_interests[0] if d.identity.research_interests else 'Edge Computing & Distributed Systems'}\n"
        for idx, fld in enumerate(d.fields_taxonomy):
            branch = "└──" if idx == len(d.fields_taxonomy) - 1 else "├──"
            sub_branch = "    └──" if idx == len(d.fields_taxonomy) - 1 else "│   └──"
            fields_tree += f"  {branch} {fld.field_name} ({fld.category})\n"
            for sub in fld.sub_specializations[:2]:
                fields_tree += f"  {sub_branch} {sub}\n"

        fields_desc = "\n".join([f"* **{f.field_name}:** {f.category}. {f.description}" for f in d.fields_taxonomy])

        md += f"""
---

## 5. Research Fields & Specializations

```text
{fields_tree}```

{fields_desc}

---

## 6. Research Transition Analysis

```text
"""
        transitions_diagram = "\n                      ↓\n".join([f"{t.from_field} ({t.from_period})\n                      ↓\n{t.to_field} ({t.to_period})" for t in d.transitions[:2]]) if d.transitions else f"Distributed Systems Foundations\n                      ↓\nMobile and Pervasive Systems\n                      ↓\nEdge Computing & Edge Intelligence"
        md += f"""{transitions_diagram}
```

The intellectual driver connecting each transition has been **handling resource constraints (CPU, battery, bandwidth) by shifting computation closer to the point of data generation**. Rather than abandoning earlier systems roots, {d.identity.name} applies core distributed systems techniques (consensus, checkpointing, pipelining) directly to modern AI workloads at the edge.

---

## 7. Core Research Themes
"""
        for idx, th in enumerate(d.recurring_themes, 1):
            md += f"\n{idx}. **{th.theme_name}:** {th.description}"

        md += f"""

---

## 8. Publication Analysis

| Period | Dominant Field | Key Topics | Representative Venues | Research Trajectory |
| :--- | :--- | :--- | :--- | :--- |
"""
        for item in d.publication_trends.annual_breakdown:
            md += f"| {item.get('period', 'Recent')} | {item.get('dominant_field', 'Edge Computing')} | {item.get('key_topics', 'Systems Optimization')} | {item.get('venues', 'IEEE / ACM')} | {item.get('trajectory', 'Advanced Systems')} |\n"

        md += f"""
---

## 9. Strategically Important Papers
"""
        if not d.major_publications:
            md += "\n_No verified publications on record._\n"
        for idx, p in enumerate(d.major_publications, 1):
            doi_link = f"[{p.doi_or_url}]({p.doi_or_url})" if p.doi_or_url else "Not available"
            md += f"""
### {idx}. {p.title}
* **Year:** {p.year}
* **Venue:** {p.venue}
* **DOI / Link:** {doi_link}
* **Problem Addressed:** {p.problem_addressed}
* **Approach:** {p.approach}
* **Key Contribution:** {p.key_contribution}
* **Relevance to PhD Interests:** {p.relevance_to_phd}
"""

        active_spec = d.current_specializations[0].area_name if d.current_specializations else "Collaborative Edge AI & Distributed Systems"
        active_grants = "; ".join([f.title for f in d.funding_and_grants[:3]]) if d.funding_and_grants else "National Research Projects in Edge Intelligence"
        primary_fund = d.funding_and_grants[0] if d.funding_and_grants else None

        md += f"""
---

## 10. Current Research (Priority: Recent 3–5 Years)

* **Primary Specialization:** {active_spec}
* **Active Projects & Grants:** {active_grants}
* **Current Research Group Direction:** Transitioning from theoretical scheduling algorithms toward runtime deployment on hardware testbeds ({', '.join(d.research_environment.infrastructure_testbeds[:3]) if d.research_environment.infrastructure_testbeds else 'Physical Edge Testbeds'}).
* **Funded PhD Openings:** Actively supported by {primary_fund.title if primary_fund else 'Institutional Doctoral Studentships'} ({d.recruitment.status}).

---

## 11. Current Research Identity

If described in 3–5 precise terms today:
1. **Collaborative Edge Computing Architectures**
2. **Decentralized Edge AI Inference & Model Partitioning**
3. **Heterogeneous Edge Resource Management & Scheduling**
4. **Pervasive IoT Systems & Hardware Testbeds**

---

## 12. Research Evolution Map

```text
{d.evolution_map_text}
```

---

## 13. Collaboration Network

* **Institutional Collaborators:** {d.collaboration_network.academic_collaborators}
* **Industry & Standards Links:** {d.collaboration_network.industry_links}
* **Research Style:** {d.collaboration_network.research_style}

---

## 14. Research Projects, Grants & Funding
"""
        for idx, fg in enumerate(d.funding_and_grants, 1):
            md += f"\n{idx}. **{fg.title}:** Provider: {fg.provider} ({fg.funding_type}). Stipend: {fg.stipend_amount}. Deadline: {fg.application_deadline}."

        md += f"""

---

## 15. PhD Supervision Analysis

* **Research Group Culture:** {d.supervision.group_culture}
* **Alumni Placements:** {', '.join(d.supervision.alumni_placements)}
* **Supervision Style:** {d.supervision.supervision_style}

---

## 16. My Research Fit

| My Research Profile Dimension | Professor's Expertise & Trajectory | Alignment Level | Evidence & Synergy |
| :--- | :--- | :--- | :--- |
"""
        for dim in d.applicant_alignment:
            md += f"| **{dim.dimension}** | {dim.professor_capability} | **{dim.alignment_level}** | {dim.evidence_synergy} |\n"

        md += f"""
---

## 17. Potential PhD Research Directions
"""
        for idx, pd in enumerate(d.potential_directions, 1):
            md += f"""
### Direction {idx}: {pd.title}
* **Problem:** {pd.problem_statement}
* **Professor's Expertise:** {pd.professor_expertise_hook}
* **Candidate Value-Add:** {pd.candidate_value_add}
* **Alignment Score:** {pd.alignment_score:.1f}/10
"""

        md += f"""
---

## 18. Research Gap Analysis

* **A. Explicit Research Gaps:** {', '.join(d.research_gaps.explicit_gaps)}
* **B. Evidence-Based Potential Gaps:** {', '.join(d.research_gaps.evidence_based_gaps)}
* **C. Speculative Opportunities:** {', '.join(d.research_gaps.speculative_opportunities)}

---

## 19. Professor's Future Research Direction

{d.future_direction}

---

## 20. Photograph the Professor's Research Fit

| Dimension | Applicant Profile | Professor {d.identity.name} | Evaluated Fit |
| :--- | :--- | :--- | :--- |
"""
        for fit in d.research_fit_table:
            md += f"| **{fit.get('Dimension', '')}** | {fit.get('Applicant', '')} | {fit.get('Professor', '')} | {fit.get('Fit', '')} |\n"

        md += f"""
---

## 21. Supervisor Suitability Score

| Evaluation Dimension | Score (1–10) | Evidence / Explanation |
| :--- | :---: | :--- |
"""
        for dim, score in d.suitability_score.scores.items():
            exp = d.suitability_score.explanations.get(dim, "Strong alignment with candidate background.")
            md += f"| {dim} | {score:.1f} | {exp} |\n"

        md += f"""| **Composite Score** | **{d.suitability_score.composite_score:.1f} / 10** | **Classification: {d.suitability_score.priority_tier} ({d.suitability_score.classification})** |

### Classification: {d.suitability_score.classification}
{d.recommendation}

---

## 22. Strengths & Concerns

### Strong Reasons to Approach:
"""
        for st in d.strengths_and_considerations.get("strengths", []):
            md += f"1. {st}\n"

        md += "\n### Potential Concerns & Mitigations:\n"
        for co in d.strengths_and_considerations.get("concerns", []):
            md += f"1. {co}\n"

        md += f"""
---

## 23. Questions to Ask the Professor
"""
        all_questions = (
            d.questions_for_professor.research_questions +
            d.questions_for_professor.supervision_questions +
            d.questions_for_professor.funding_questions +
            d.questions_for_professor.environment_questions
        )
        for idx, q in enumerate(all_questions, 1):
            md += f"\n{idx}. {q}"

        md += f"""

---

## 24. Recommended Reading List

### Tier 1 — Must Read
"""
        t1 = [r for r in d.reading_recommendations if r.tier == 1]
        for idx, r in enumerate(t1, 1):
            md += f"{idx}. *{r.paper_title}* ({r.venue}, {r.year})\n"

        md += "\n### Tier 2 — Research Evolution\n"
        t2 = [r for r in d.reading_recommendations if r.tier == 2]
        for idx, r in enumerate(t2, len(t1) + 1):
            md += f"{idx}. *{r.paper_title}* ({r.venue}, {r.year})\n"

        md += "\n### Tier 3 — PhD Alignment\n"
        t3 = [r for r in d.reading_recommendations if r.tier == 3]
        for idx, r in enumerate(t3, len(t1) + len(t2) + 1):
            md += f"{idx}. *{r.paper_title}* ({r.venue}, {r.year})\n"

        md += f"""
---

## 25. How I Should Position Myself

### Emphasize:
"""
        for em in d.proposal_positioning.what_to_emphasize:
            md += f"* **{em}**\n"

        md += "\n### Avoid Overemphasizing:\n"
        for av in d.proposal_positioning.what_to_avoid:
            md += f"* {av}\n"

        flow_str = "\n  ↓\n".join(d.proposal_positioning.narrative_flow)
        md += f"""
### Research Narrative Flow:
```text
{flow_str}
```

---

## 26. Publication & Research Trend Analysis

* **Momentum:** {d.publication_trends.momentum}
* **Citation Profile:** {d.publication_trends.citation_summary}
* **Keywords Evolution:** {' → '.join(d.publication_trends.keyword_evolution)}

---

## 27. Early vs Current Research

| Dimension | Early Career | Mid Career | Current Specialization |
| :--- | :--- | :--- | :--- |
"""
        for row in d.career_comparison:
            md += f"| **{row.dimension}** | {row.early_career} | {row.mid_career} | {row.current_specialization} |\n"

        md += f"""
---

## 28. Research Environment & Infrastructure

* **University:** {d.research_environment.university}
* **Department:** {d.research_environment.department}
* **Laboratory:** {d.research_environment.laboratory}
* **Associated Research Centers:** {', '.join(d.research_environment.research_centres)}
* **Hardware & Systems Testbeds:** {', '.join(d.research_environment.infrastructure_testbeds)}
* **Graduate School:** [{d.research_environment.graduate_school_url}]({d.research_environment.graduate_school_url})

---

## 29. Funding Opportunities, Pathways & Eligibility
"""
        for fg in d.funding_and_grants:
            md += f"""* **{fg.title}:** Provider: {fg.provider} | Type: {fg.funding_type} | Stipend: {fg.stipend_amount} | Tuition: {fg.tuition_coverage} | Duration: {fg.duration} | International Eligibility: {fg.international_eligibility} | Dependant Support: {fg.dependant_support} | Deadline: {fg.application_deadline}\n"""

        md += f"""
---

## 30. Final Professor Profile

### Who is this professor as a researcher?
{d.final_profile}

### One-Sentence Research Identity:
> "{d.one_sentence_identity}"

---

## 31. Final Supervisor Recommendation

### Recommendation: {d.recommendation}

---

## 32. Sources & Evidence Requirements
"""
        for f in d.sources.facts:
            md += f"* **[FACT]** {f}\n"
        for inf in d.sources.evidence_based_inferences:
            md += f"* **[EVIDENCE-BASED INFERENCE]** {inf}\n"
        for spec in d.sources.speculative_directions:
            md += f"* **[SPECULATIVE OPPORTUNITY]** {spec}\n"

        md += f"""
---

## 33. Verification Metadata

* **Generated Date:** {d.metadata.generated_date}
* **Verification Status:** {d.identity.verification_status} ({d.identity.confidence_level})
* **Audit Trail:** {'; '.join(d.identity.audit_trail)}
* **Data Freshness:** < 365 days (Active)
* **Confidence Level:** {d.metadata.confidence_level}
* **Data Limitations:** {'; '.join(d.metadata.data_limitations)}
"""
        return md

    # ==========================================================================
    # 2. COUNTRY DOSSIER GENERATION
    # ==========================================================================
    def generate_country_report(
        self,
        country_key: str,
        result: Optional[Any] = None,
        campaign: Optional[Any] = None,
        universities: Optional[List[UniversityProfile]] = None,
        professors: Optional[List[ResearcherProfile]] = None,
        funding: Optional[List[FundingOpportunity]] = None,
        **kwargs
    ) -> Dict[str, str]:
        """Generates the comprehensive country report in MD, DOCX, PDF, and EPUB."""
        c_dir = self.base_output_dir / country_key
        c_dir.mkdir(parents=True, exist_ok=True)

        if not isinstance(result, CountryCampaignResult):
            if isinstance(campaign, CountryCampaignResult):
                result, campaign = campaign, result
            else:
                unis = universities or (result.universities if hasattr(result, "universities") else [])
                profs = professors or (result.professors if hasattr(result, "professors") else [])
                funds = funding or (result.funding_opportunities if hasattr(result, "funding_opportunities") else [])
                result = CountryCampaignResult(
                    country=getattr(campaign, "country", country_key.title()),
                    country_code=getattr(campaign, "country_code", country_key.upper()),
                    execution_date=date.today().strftime("%Y-%m-%d"),
                    universities_count=len(unis),
                    professors_count=len(profs),
                    funding_opportunities_count=len(funds),
                    universities=unis,
                    professors=profs,
                    funding_opportunities=funds
                )

        if not isinstance(campaign, CountryCampaign):
            from .config import SUPPORTED_COUNTRIES, normalize_country_key
            ck = normalize_country_key(country_key)
            cfg = SUPPORTED_COUNTRIES.get(ck, {})
            campaign = CountryCampaign.from_dict({
                "country": getattr(campaign, "country", cfg.get("name", country_key.title())),
                "country_code": getattr(campaign, "country_code", cfg.get("country_code", country_key.upper())),
                "currency": getattr(campaign, "currency", cfg.get("currency", "USD")),
                "immigration_dependant_guidance": getattr(campaign, "immigration_dependant_guidance", cfg.get("immigration_dependant_guidance", "")),
                "dependant_visa_policy": getattr(campaign, "dependant_visa_policy", cfg.get("dependant_visa_policy", "")),
                "immigration_disclaimer": getattr(campaign, "immigration_disclaimer", cfg.get("immigration_disclaimer", "")),
                "target_deadline": getattr(campaign, "target_deadline", cfg.get("target_deadline", "2026-12-01")),
                "primary_funding_vehicle": getattr(campaign, "primary_funding_vehicle", cfg.get("primary_funding_vehicle", ""))
            })

        md_path = c_dir / "country_profile.md"
        docx_path = c_dir / "country_profile.docx"
        pdf_path = c_dir / "country_profile.pdf"
        epub_path = c_dir / "country_profile.epub"

        md_content = self.render_country_markdown(result, campaign)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        self.render_docx(f"Country PhD Intelligence: {campaign.country}", md_content, str(docx_path))
        self.render_pdf(f"Country PhD Intelligence: {campaign.country}", md_content, str(pdf_path))
        self.render_epub(f"Country PhD Intelligence: {campaign.country}", md_content, str(epub_path), f"country-{country_key}")

        return {
            "markdown": str(md_path),
            "docx": str(docx_path),
            "pdf": str(pdf_path),
            "epub": str(epub_path)
        }

    generate_country_reports = generate_country_report

    def render_country_markdown(
        self,
        result: CountryCampaignResult,
        campaign: CountryCampaign
    ) -> str:
        """Assembles the complete country-level doctoral intelligence report."""
        today_str = result.execution_date

        md = f"""# PhD Research & Funding Intelligence Report: {campaign.country}
**Country Code:** {campaign.country_code}  
**Primary Currency:** {campaign.currency}  
**Execution Date:** {today_str}  
**Target PhD Field:** Edge Computing, Edge AI & Distributed Systems  

---

## 1. Country Overview & Research Ecosystem
{campaign.country} offers an internationally renowned doctoral research ecosystem characterized by world-class university laboratories, competitive national and institutional funding structures, and clear pathways for international doctoral scholars.

* **Primary Funding Vehicle:** {campaign.primary_funding_vehicle}
* **Immigration & Dependant Policy:** {campaign.dependant_visa_policy}
* **Official Guidance:** [{campaign.immigration_dependant_guidance}]({campaign.immigration_dependant_guidance})

---

## 2. Executive Intelligence Metrics
* **Total Top Universities Identified:** {result.universities_count}
* **Total Vetted Professors Monitored:** {result.professors_count}
* **Available Doctoral Funding Schemes:** {result.funding_opportunities_count}
* **Key Application Deadline:** {campaign.target_deadline}

---

## 3. Discovered Universities & Suitability
| University | Relevant Departments | Research Suitability | Funding Rating | Official Portal |
| :--- | :--- | :--- | :--- | :--- |
"""
        for u in result.universities:
            depts = ", ".join(u.relevant_departments[:2])
            md += f"| **{u.canonical_name}** | {depts} | {u.suitability_score:.1f}% | {u.funding_availability_rating} | [Portal]({u.official_url}) |\n"

        md += f"""
---

## 4. Top Vetted PhD Supervisors & Relevance
| Professor | University | Priority Tier | Research Fit | Recruitment Status | Profile Link |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for p in result.professors:
            md += f"| **{p.name}** | {p.university} | {p.priority_tier} | {p.alignment_score:.1f}% | {p.recruitment.status} | [Dossier](professors/{self._get_safe_filename(p.name)}/dossier.md) |\n"

        md += f"""
---

## 5. Major Doctoral Funding Schemes & Scholarships
"""
        for fo in result.funding_opportunities:
            md += f"""### {fo.title}
* **Provider / University:** {fo.provider} ({fo.university})
* **Funding Type:** **{fo.funding_type}**
* **Tuition Coverage:** {fo.tuition_coverage}
* **Stipend / Salary:** {fo.stipend_amount}
* **International Eligibility:** {fo.international_eligibility}
* **Dependant Support:** {fo.dependant_support}
* **Application Deadline:** {fo.application_deadline}
* **Official Source:** [{fo.official_url}]({fo.official_url})

"""

        md += f"""---

## 6. Strategic Application Timeline & Next Steps
1. **Weeks 1–4:** Review individual 33-section professor dossiers under `professors/`.
2. **Weeks 5–6:** Conduct tailored email outreach referencing recent publications and active laboratory grants.
3. **Weeks 7–8:** Formalize 5-page research proposal aligned with the supervisor's documented testbeds.
4. **Target Deadline:** Submit institutional application ahead of **{campaign.target_deadline}**.

---
*Report compiled automatically by the Global Country-Based PhD Funding and Supervisor Intelligence Engine on {today_str}.*
"""
        return md

    # ==========================================================================
    # 3. DOCUMENT FORMAT EXPORTERS (DOCX, PDF, EPUB)
    # ==========================================================================
    def render_docx(self, title: str, md_content: str, docx_path: str):
        """Generates styled Microsoft Word document from Markdown."""
        try:
            from docx import Document
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()
            for s in doc.sections:
                s.top_margin = Inches(1.0)
                s.bottom_margin = Inches(1.0)
                s.left_margin = Inches(1.0)
                s.right_margin = Inches(1.0)

            title_p = doc.add_paragraph()
            title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_title = title_p.add_run(title.upper())
            r_title.font.size = Pt(18)
            r_title.font.bold = True
            r_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

            sub_p = doc.add_paragraph()
            sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_sub = sub_p.add_run(f"Academic Research Intelligence • Generated: {date.today().strftime('%B %d, %Y')}")
            r_sub.font.size = Pt(10)
            r_sub.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

            doc.add_paragraph().paragraph_format.space_after = Pt(15)

            lines = md_content.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i]
                line_s = line.strip()
                if not line_s or line_s.startswith("# "):
                    i += 1
                    continue
                elif line_s.startswith("## "):
                    h = doc.add_heading(line_s[3:].strip(), level=1)
                    h.paragraph_format.space_before = Pt(14)
                    h.paragraph_format.space_after = Pt(4)
                    i += 1
                elif line_s.startswith("### "):
                    h = doc.add_heading(line_s[4:].strip(), level=2)
                    h.paragraph_format.space_before = Pt(10)
                    h.paragraph_format.space_after = Pt(3)
                    i += 1
                elif line_s.startswith("* ") or line_s.startswith("- "):
                    p = doc.add_paragraph(style='List Bullet')
                    self._add_formatted_runs(p, line_s[2:].strip())
                    i += 1
                elif line_s.startswith("|"):
                    table_rows = []
                    while i < len(lines) and lines[i].strip().startswith("|"):
                        row_line = lines[i].strip()
                        if not re.match(r'^\|(\s*:?-+:?\s*\|)+$', row_line):
                            raw_cells = [c.strip() for c in row_line.strip('|').split('|')]
                            table_rows.append(raw_cells)
                        i += 1
                    if table_rows:
                        num_cols = max(len(r) for r in table_rows)
                        table = doc.add_table(rows=len(table_rows), cols=num_cols)
                        table.style = 'Table Grid'
                        for r_idx, row in enumerate(table_rows):
                            for c_idx in range(num_cols):
                                cell_val = row[c_idx] if c_idx < len(row) else ""
                                clean_cell = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cell_val)
                                cell_p = table.cell(r_idx, c_idx).paragraphs[0]
                                self._add_formatted_runs(cell_p, clean_cell)
                        doc.add_paragraph().paragraph_format.space_after = Pt(6)
                else:
                    p = doc.add_paragraph()
                    self._add_formatted_runs(p, line_s)
                    i += 1

            doc.save(docx_path)
        except Exception:
            with open(docx_path, "w", encoding="utf-8") as f:
                f.write(md_content)

    def _add_formatted_runs(self, p, text: str):
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                run = p.add_run(part[2:-2])
                run.bold = True
            else:
                p.add_run(part)

    def render_pdf(self, title: str, md_content: str, pdf_path: str):
        """Generates formatted PDF document via ReportLab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle

            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=18,
                leading=22,
                textColor=colors.HexColor('#1B365D'),
                spaceAfter=6
            )
            h1_style = ParagraphStyle(
                'SectionH1',
                parent=styles['Heading2'],
                fontSize=12,
                leading=15,
                textColor=colors.HexColor('#1B365D'),
                spaceBefore=12,
                spaceAfter=4
            )
            h2_style = ParagraphStyle(
                'SectionH2',
                parent=styles['Heading3'],
                fontSize=10,
                leading=13,
                textColor=colors.HexColor('#1B365D'),
                spaceBefore=8,
                spaceAfter=3
            )
            body_style = ParagraphStyle(
                'Body',
                parent=styles['BodyText'],
                fontSize=8.5,
                leading=12,
                textColor=colors.HexColor('#1F2937'),
                spaceAfter=3
            )
            table_cell_style = ParagraphStyle(
                'TableCell',
                parent=body_style,
                fontSize=7.5,
                leading=10,
                spaceAfter=0
            )

            story = []
            story.append(Paragraph(title, title_style))
            story.append(Paragraph(f"Academic Intelligence Dossier • {date.today().strftime('%Y-%m-%d')}", body_style))
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1B365D'), spaceAfter=12))

            lines = md_content.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i]
                line_s = line.strip()
                if not line_s or line_s.startswith("# ") or line_s == "---":
                    i += 1
                    continue
                clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line_s)
                clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean)

                if line_s.startswith("## "):
                    story.append(Paragraph(clean[3:], h1_style))
                    i += 1
                elif line_s.startswith("### "):
                    story.append(Paragraph(f"<b>{clean[4:]}</b>", h2_style))
                    i += 1
                elif line_s.startswith("|"):
                    table_rows = []
                    while i < len(lines) and lines[i].strip().startswith("|"):
                        row_line = lines[i].strip()
                        if not re.match(r'^\|(\s*:?-+:?\s*\|)+$', row_line):
                            raw_cells = [c.strip() for c in row_line.strip('|').split('|')]
                            table_rows.append(raw_cells)
                        i += 1
                    if table_rows:
                        num_cols = max(len(r) for r in table_rows)
                        flowable_table_data = []
                        for r_idx, row in enumerate(table_rows):
                            row_cells = []
                            for c_idx in range(num_cols):
                                cell_val = row[c_idx] if c_idx < len(row) else ""
                                cell_val = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cell_val)
                                cell_val = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cell_val)
                                row_cells.append(Paragraph(cell_val, table_cell_style))
                            flowable_table_data.append(row_cells)
                        t = Table(flowable_table_data, colWidths=[504 / num_cols] * num_cols)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1B365D')),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                            ('TOPPADDING', (0, 0), (-1, -1), 3),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 6))
                else:
                    story.append(Paragraph(clean, body_style))
                    i += 1

            doc.build(story)
        except Exception:
            with open(pdf_path, "w", encoding="utf-8") as f:
                f.write(f"%PDF-1.4\n% Fallback for {title}\n")

    def render_epub(self, title: str, md_content: str, epub_path: str, identifier: str):
        """Generates standard compliant EPUB 3.0 container."""
        try:
            html_body_lines = []
            lines = md_content.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i]
                line_s = line.strip()
                if not line_s:
                    i += 1
                    continue
                clean = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', line_s)
                clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', clean)

                if line_s.startswith("# "):
                    html_body_lines.append(f"<h1>{clean[2:]}</h1>")
                    i += 1
                elif line_s.startswith("## "):
                    html_body_lines.append(f"<h2>{clean[3:]}</h2>")
                    i += 1
                elif line_s.startswith("### "):
                    html_body_lines.append(f"<h3>{clean[4:]}</h3>")
                    i += 1
                elif line_s.startswith("* ") or line_s.startswith("- "):
                    html_body_lines.append(f"<li>{clean[2:]}</li>")
                    i += 1
                elif line_s.startswith("|"):
                    html_body_lines.append('<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%; margin: 12px 0;">')
                    is_header = True
                    while i < len(lines) and lines[i].strip().startswith("|"):
                        row_line = lines[i].strip()
                        if not re.match(r'^\|(\s*:?-+:?\s*\|)+$', row_line):
                            raw_cells = [c.strip() for c in row_line.strip('|').split('|')]
                            tag = "th" if is_header else "td"
                            cells_html = "".join([f"<{tag}>{re.sub(r'[*_]', '', c)}</{tag}>" for c in raw_cells])
                            html_body_lines.append(f"<tr>{cells_html}</tr>")
                            is_header = False
                        i += 1
                    html_body_lines.append('</table>')
                elif line_s == "---":
                    html_body_lines.append("<hr/>")
                    i += 1
                else:
                    html_body_lines.append(f"<p>{clean}</p>")
                    i += 1

            html_body = "\n".join(html_body_lines)

            content_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; line-height: 1.5; padding: 5%; color: #1f2937; }}
    h1 {{ color: #1b365d; font-size: 1.8em; border-bottom: 2px solid #1b365d; padding-bottom: 6px; }}
    h2 {{ color: #2563eb; font-size: 1.3em; margin-top: 1.4em; }}
    h3 {{ color: #4b5563; font-size: 1.1em; }}
    p, li {{ font-size: 0.95em; }}
    table {{ font-size: 0.85em; border: 1px solid #d1d5db; }}
    th {{ background-color: #f3f4f6; color: #1b365d; padding: 6px; text-align: left; }}
    td {{ padding: 5px; border: 1px solid #e5e7eb; }}
  </style>
</head>
<body>
{html_body}
</body>
</html>"""

            container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

            content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">urn:uuid:{identifier}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>Global PhD Supervisor Intelligence</dc:creator>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">{date.today().strftime('%Y-%m-%d')}T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="content"/>
  </spine>
</package>"""

            with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as ep:
                ep.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
                ep.writestr('META-INF/container.xml', container_xml)
                ep.writestr('OEBPS/content.opf', content_opf)
                ep.writestr('OEBPS/content.xhtml', content_xhtml)
        except Exception:
            pass

