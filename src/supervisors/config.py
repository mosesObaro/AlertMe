"""
Centralized Configuration for Global Country-Based PhD Funding and Supervisor Intelligence Engine.
Defines supported country campaigns (UK, Japan, Germany, US, Canada, Sweden, Hong Kong),
institutional scope, research keywords, scoring weights, and freshness policies.
"""

from typing import Dict, List, Any

# Minimum professors required per country campaign execution
MINIMUM_PROFESSORS_PER_COUNTRY = 8

# Freshness window for recruitment verification (days)
RECRUITMENT_FRESHNESS_DAYS = 365

# Fixed Applicant Profile defaults as defined by requirements
DEFAULT_APPLICANT_PROFILE = {
    "degree_background": "Computer Engineering (BSc); Computer Science (MSc)",
    "current_professional": "Software Engineering / iOS Engineering",
    "proposed_phd_field": "Edge Computing",
    "research_interests": [
        "Edge Computing",
        "Edge AI / Edge Intelligence",
        "Distributed Systems",
        "Internet of Things (IoT)",
        "Cloud-Edge Continuum",
        "Federated Learning at Network Edge",
        "Systems & Networking"
    ],
    "proposed_phd_topic_status": "Not yet finalized (open to strategic alignment)"
}

# Standard Research Domains & Core Keywords for Matching
RESEARCH_KEYWORDS = {
    "core": [
        "edge computing", "edge intelligence", "edge ai", "mobile edge computing",
        "mec", "multi-access edge computing", "edge-cloud computing", "edge-cloud continuum",
        "cloud-edge systems", "edge systems"
    ],
    "distributed_systems": [
        "distributed systems", "distributed computing", "cloud computing", "cloud-edge systems",
        "distributed ai", "distributed machine learning", "federated learning", "consensus",
        "fault tolerance", "distributed storage", "crdt", "stream processing"
    ],
    "networking": [
        "computer networks", "wireless networks", "5g", "6g", "mobile networks",
        "network optimization", "network intelligence", "wireless edge networks",
        "sdn", "software-defined networking", "network slicing", "urllc", "v2x"
    ],
    "ai_iot": [
        "aiot", "internet of things", "iot", "intelligent iot", "edge machine learning",
        "tinyml", "ai systems", "resource-constrained ai", "model compression",
        "quantization", "embedded ai", "wearable cognitive assistance"
    ],
    "optimization_systems": [
        "resource allocation", "scheduling", "task offloading", "computation offloading",
        "edge orchestration", "network optimization", "distributed optimization",
        "serverless edge computing", "faas", "convex optimization", "reinforcement learning"
    ]
}

# Country Campaign Definitions
SUPPORTED_COUNTRIES: Dict[str, Dict[str, Any]] = {
    "uk": {
        "name": "United Kingdom",
        "country_code": "UK",
        "currency": "GBP",
        "immigration_dependant_guidance": "https://www.gov.uk/student-visa/family-members",
        "dependant_visa_policy": "International postgraduate research (PhD/Doctoral) students are explicitly permitted to bring family dependants (partner and children) on Student Dependant Visas.",
        "immigration_disclaimer": "Dependants eligible under current published UK Visas and Immigration guidance for research doctorates; verify requirements before applying.",
        "target_deadline": "2026-12-15",
        "primary_funding_vehicle": "UKRI / EPSRC Doctoral Studentships & University Doctoral Scholarships",
        "aliases": ["uk", "united kingdom", "great britain", "britain", "england", "scotland"]
    },
    "japan": {
        "name": "Japan",
        "country_code": "JP",
        "currency": "JPY",
        "immigration_dependant_guidance": "https://www.isa.go.jp/en/applications/procedures/zairyu_nintei10_19.html",
        "dependant_visa_policy": "International doctoral students holding a College Student (Ryugaku) visa may sponsor spouse and children under Dependent (Kazoku Taizai) status of residence.",
        "immigration_disclaimer": "Dependants eligible under current published Immigration Services Agency of Japan guidelines; verify requirements before applying.",
        "target_deadline": "2026-11-30",
        "primary_funding_vehicle": "MEXT Government Doctoral Scholarship, JSPS Research Fellowships & University Fellowships",
        "aliases": ["japan", "jp", "nihon", "nippon"]
    },
    "germany": {
        "name": "Germany",
        "country_code": "DE",
        "currency": "EUR",
        "immigration_dependant_guidance": "https://www.make-it-in-germany.com/en/visa-residence/family-reunification/spouses-joining-citizens-non-eu",
        "dependant_visa_policy": "Dependants (spouse and minor children) are eligible for family reunification visa (Familiennachzug) with proven adequate health insurance and living funds.",
        "immigration_disclaimer": "Dependants eligible under current published German residence act (§ 29-32 AufenthG); verify requirements before applying.",
        "target_deadline": "2026-12-01",
        "primary_funding_vehicle": "TV-L E13 Salaried Research Associate Positions (100%/75%), DAAD Grants & DFG RTGs",
        "aliases": ["germany", "de", "deutschland"]
    },
    "us": {
        "name": "United States",
        "country_code": "US",
        "currency": "USD",
        "immigration_dependant_guidance": "https://travel.state.gov/content/travel/en/us-visas/study/student-visa.html",
        "dependant_visa_policy": "Spouses and unmarried minor children of F-1/J-1 doctoral students are eligible for F-2 or J-2 derivative status. J-2 spouses may apply for work authorization (EAD).",
        "immigration_disclaimer": "Dependants eligible under current published US Department of State visa regulations; verify requirements before applying.",
        "target_deadline": "2026-12-15",
        "primary_funding_vehicle": "Full Graduate Research Assistantships (100% Tuition Waiver + $30k-$48k Stipend)",
        "aliases": ["us", "usa", "united states", "united states of america"]
    },
    "canada": {
        "name": "Canada",
        "country_code": "CA",
        "currency": "CAD",
        "immigration_dependant_guidance": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/help-your-spouse-work.html",
        "dependant_visa_policy": "Spouses/common-law partners of full-time doctoral (PhD) students are eligible for a Spousal Open Work Permit (SOWP); minor children can study at public schools without study permit.",
        "immigration_disclaimer": "Dependants eligible under current published IRCC guidelines for doctoral students; verify requirements before applying.",
        "target_deadline": "2026-12-15",
        "primary_funding_vehicle": "Vanier CGS ($50,000/yr), NSERC Fellowships & Departmental Guaranteed PhD Funding Packages ($25k-$35k/yr)",
        "aliases": ["canada", "ca"]
    },
    "sweden": {
        "name": "Sweden",
        "country_code": "SE",
        "currency": "SEK",
        "immigration_dependant_guidance": "https://www.migrationsverket.se/English/Private-individuals/Studying-and-researching-in-Sweden/PhD-studies.html",
        "dependant_visa_policy": "Doctoral positions in Sweden are classified as salaried employment (Doktorandanställning) with residence permits for doctoral studies; family members can obtain residence permits with right to work.",
        "immigration_disclaimer": "Dependants eligible under current Swedish Migration Agency regulations for doctoral researchers; verify requirements before applying.",
        "target_deadline": "2026-12-01",
        "primary_funding_vehicle": "Fully Salaried Doctoral Employment (~31,000-35,000 SEK/month, free tuition, social benefits) & WASP Fellowships",
        "aliases": ["sweden", "se", "sverige"]
    },
    "hong_kong": {
        "name": "Hong Kong",
        "country_code": "HK",
        "currency": "HKD",
        "immigration_dependant_guidance": "https://www.immd.gov.hk/eng/services/visas/dependant_visa_entry_permit.html",
        "dependant_visa_policy": "Full-time doctoral students in Hong Kong may sponsor legal spouse and unmarried dependent children under 18 for dependant visas with right to study and reside.",
        "immigration_disclaimer": "Dependants eligible under current published Hong Kong Immigration Department guidance; verify requirements before applying.",
        "target_deadline": "2026-12-01",
        "primary_funding_vehicle": "Hong Kong PhD Fellowship Scheme (HKPFS HK$331,200/yr + travel allowance) & University Postgraduate Studentships",
        "aliases": ["hong kong", "hk", "hongkong"]
    }
}

COUNTRY_CONFIGS = SUPPORTED_COUNTRIES

# Scoring Weights for University Suitability (100% total)
UNIVERSITY_SCORING_WEIGHTS = {
    "research_alignment": 0.35,      # Presence of Edge Computing / Distributed Systems labs
    "funding_availability": 0.25,   # Availability of guaranteed doctoral funding / assistantships
    "faculty_density": 0.20,        # Number of prominent active faculty in target areas
    "infrastructure_strength": 0.10,# Testbeds, HPC, research centers
    "international_access": 0.10    # International student funding eligibility
}

# Scoring Weights for Professor Relevance & Suitability (100% total)
PROFESSOR_SCORING_WEIGHTS = {
    "research_alignment": 0.35,     # Overlap with Edge Computing & Distributed Systems
    "current_activity": 0.20,       # Recent publications (2022-2026), active grants
    "phd_recruitment": 0.25,        # Evidence of active student recruitment / open positions
    "academic_stature": 0.10,       # IEEE/ACM Fellows, citation impact, top-tier venues
    "research_accessibility": 0.10  # Open access preprints, code repos, public lab website
}

def normalize_country_key(country_input: str) -> str:
    """Normalizes raw country names or codes to canonical dictionary key."""
    if not country_input:
        return ""
    clean = country_input.strip().lower()
    for key, cfg in SUPPORTED_COUNTRIES.items():
        if clean == key or clean == cfg["country_code"].lower() or clean in [a.lower() for a in cfg.get("aliases", [])]:
            return key
    return clean
