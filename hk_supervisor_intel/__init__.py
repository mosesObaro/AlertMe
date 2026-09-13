"""
Hong Kong PhD Supervisor Intelligence Module.
A deadline-aware, evidence-based academic intelligence and scholarship tracking system
targeting 8 specific Hong Kong universities for PhD applications in Edge Computing.
"""

from .config import (
    HONG_KONG_SUPERVISOR_INTELLIGENCE_ENABLED,
    TARGET_HONG_KONG_UNIVERSITIES,
    UNIVERSITY_ALIASES
)
from .models import (
    UniversityProfile,
    ResearcherProfile,
    Publication,
    Scholarship,
    Opportunity,
    DailyAlert
)
from .storage import StorageManager
from .discovery import DiscoveryEngine
from .recruitment import RecruitmentEngine
from .scoring import ScoringEngine
from .campaign import CampaignManager
from .alerts import AlertGenerator
from .curriculum_matcher import CurriculumMatcher
from .ideas_matcher import IdeasMatcher
from .excel_extension import add_hong_kong_module_sheets

__version__ = "1.0.0"
__all__ = [
    "HONG_KONG_SUPERVISOR_INTELLIGENCE_ENABLED",
    "TARGET_HONG_KONG_UNIVERSITIES",
    "UNIVERSITY_ALIASES",
    "UniversityProfile",
    "ResearcherProfile",
    "Publication",
    "Scholarship",
    "Opportunity",
    "DailyAlert",
    "StorageManager",
    "DiscoveryEngine",
    "RecruitmentEngine",
    "ScoringEngine",
    "CampaignManager",
    "AlertGenerator",
    "CurriculumMatcher",
    "IdeasMatcher",
    "add_hong_kong_module_sheets"
]
