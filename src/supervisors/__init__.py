"""
Global Country-Based PhD Funding and Supervisor Intelligence Engine.
Provides 1-day complete country campaign execution, university and funding discovery,
supervisor relevance matching, quad-format dossier generation, and Excel/email integration.
"""

from .config import (
    SUPPORTED_COUNTRIES, COUNTRY_CONFIGS, MINIMUM_PROFESSORS_PER_COUNTRY,
    normalize_country_key, RECRUITMENT_FRESHNESS_DAYS
)
from .models import (
    CountryCampaign, UniversityProfile, FundingOpportunity,
    ResearcherProfile, Publication, RecruitmentEvidence,
    CountryCampaignResult
)
from .storage import StorageManager
from .discovery import DiscoveryEngine
from .funding import FundingEngine
from .scoring import ScoringEngine
from .profiler import DossierProfiler
from .campaign import CountryCampaignManager
from .alerts import CountryAlertGenerator
from .excel_extension import add_country_supervisor_sheets

__version__ = "2.0.0"
__all__ = [
    "SUPPORTED_COUNTRIES",
    "COUNTRY_CONFIGS",
    "MINIMUM_PROFESSORS_PER_COUNTRY",
    "normalize_country_key",
    "CountryCampaign",
    "UniversityProfile",
    "FundingOpportunity",
    "ResearcherProfile",
    "Publication",
    "RecruitmentEvidence",
    "CountryCampaignResult",
    "StorageManager",
    "DiscoveryEngine",
    "FundingEngine",
    "ScoringEngine",
    "DossierProfiler",
    "CountryCampaignManager",
    "CountryAlertGenerator",
    "add_country_supervisor_sheets"
]
