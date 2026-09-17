"""
Hong Kong PhD Supervisor Dossier Engine.
Delegates directly to the generic canonical DossierSynthesizer and DossierProfiler engine.
Operates completely generically without hardcoded professor text or static narratives.
"""

import os
import re
from datetime import date
from typing import Dict, Any, List, Optional
from .models import ResearcherProfile, Scholarship, Publication
from src.supervisors.analyzer import DossierSynthesizer
from src.supervisors.profiler import DossierProfiler
from src.supervisors.models import FundingOpportunity, Publication as GenericPublication, ResearcherProfile as GenericResearcherProfile
from src.supervisors.config import DEFAULT_APPLICANT_PROFILE

# Fixed Applicant Profile as specified by requirements
APPLICANT_PROFILE = dict(DEFAULT_APPLICANT_PROFILE)

class SupervisorProfiler:
    """Generates the standardized 30+ section Comprehensive PhD Supervisor Dossier."""

    def __init__(self, output_dir: str = "reports/supervisors"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.generic_profiler = DossierProfiler(output_base_dir=self.output_dir)
        self.synthesizer = DossierSynthesizer(APPLICANT_PROFILE)

    def _get_safe_filename(self, professor_name: str) -> str:
        safe = re.sub(r'[^a-zA-Z0-9_-]', '_', professor_name)
        safe = re.sub(r'_+', '_', safe).strip('_')
        return f"{safe}_PhD_Supervisor_Profile"

    def generate_all_dossiers(
        self,
        researcher: ResearcherProfile,
        scholarship: Optional[Scholarship] = None,
        reference_date: Optional[date] = None
    ) -> Dict[str, str]:
        """Generates dossier across all 4 formats and returns dictionary of filepaths and web links."""
        ref_date = reference_date or date.today()
        base_name = self._get_safe_filename(researcher.name)

        md_path = os.path.join(self.output_dir, f"{base_name}.md")
        docx_path = os.path.join(self.output_dir, f"{base_name}.docx")
        pdf_path = os.path.join(self.output_dir, f"{base_name}.pdf")
        epub_path = os.path.join(self.output_dir, f"{base_name}.epub")

        # 1. Generate Markdown content from canonical model
        md_content = self.generate_markdown(researcher, scholarship, ref_date)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 2. Generate DOCX
        self.generate_docx(researcher, md_content, docx_path)

        # 3. Generate PDF
        self.generate_pdf(researcher, md_content, pdf_path)

        # 4. Generate EPUB
        self.generate_epub(researcher, md_content, epub_path)

        # Relative GitHub URLs for email linking
        github_repo_prefix = "https://github.com/mosesObaro/AlertMe/blob/main"
        raw_prefix = "https://raw.githubusercontent.com/mosesObaro/AlertMe/main"

        return {
            "markdown_path": md_path,
            "docx_path": docx_path,
            "pdf_path": pdf_path,
            "epub_path": epub_path,
            "markdown_url": f"{github_repo_prefix}/{md_path}",
            "docx_url": f"{raw_prefix}/{docx_path}",
            "pdf_url": f"{raw_prefix}/{pdf_path}",
            "epub_url": f"{raw_prefix}/{epub_path}"
        }

    def generate_markdown(
        self,
        r: ResearcherProfile,
        s: Optional[Scholarship] = None,
        ref_date: Optional[date] = None
    ) -> str:
        """Assembles the complete generic 30+ section academic analysis in Markdown."""
        funding_list = []
        if s:
            funding_list.append(FundingOpportunity(
                opportunity_id=s.scholarship_id,
                country="Hong Kong",
                university=s.university,
                title=getattr(s, "scholarship_name", "Hong Kong PhD Fellowship Scheme"),
                provider="Hong Kong Research Grants Council",
                funding_type="SCHOLARSHIP",
                stipend_amount=getattr(s, "funding_amount", "HK$331,200/year"),
                tuition_coverage=getattr(s, "tuition_coverage", "Full Tuition Waiver"),
                duration=getattr(s, "duration", "3-4 Years"),
                international_eligibility="ELIGIBLE",
                dependant_support=getattr(s, "dependent_support", getattr(s, "dependant_visa_support", "PERMITTED")),
                application_deadline=getattr(s, "application_deadline", "2026-12-01"),
                official_url=getattr(s, "official_url", ""),
                eligibility_notes=getattr(s, "eligibility", "Open to all nationalities applying for PhD study in Hong Kong."),
                last_verified=getattr(s, "last_verified", str(ref_date or date.today()))
            ))

        dossier = self.synthesizer.synthesize(
            researcher=r,
            funding=funding_list,
            reference_date=ref_date
        )
        return self.generic_profiler.render_professor_dossier_markdown(dossier)

    def generate_docx(self, researcher: ResearcherProfile, md_content: str, docx_path: str):
        """Generates formatted Microsoft Word document (.docx)."""
        self.generic_profiler.render_docx(
            f"PhD Supervisor Dossier: {researcher.name}", md_content, docx_path
        )

    def generate_pdf(self, researcher: ResearcherProfile, md_content: str, pdf_path: str):
        """Generates formatted Adobe PDF (.pdf) via ReportLab."""
        self.generic_profiler.render_pdf(
            f"PhD Supervisor Dossier: {researcher.name}", md_content, pdf_path
        )

    def generate_epub(self, researcher: ResearcherProfile, md_content: str, epub_path: str):
        """Generates standard compliant EPUB 3.0 container."""
        safe_id = self._get_safe_filename(researcher.name)
        self.generic_profiler.render_epub(
            f"PhD Supervisor Dossier: {researcher.name}", md_content, epub_path, f"dossier-{safe_id}"
        )
