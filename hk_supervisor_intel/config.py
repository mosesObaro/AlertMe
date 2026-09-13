"""
Centralized Configuration for Hong Kong PhD Supervisor Intelligence Module.
Defines the strict 8-university boundary, institutional aliases, scoring weights,
10-week campaign timeline, and module enablement flags.
"""

# Module Enablement Flag (Permits independent disabling of the HK module)
HONG_KONG_SUPERVISOR_INTELLIGENCE_ENABLED = True

# 1. HARD UNIVERSITY SCOPE (Strict Canonical Target List)
TARGET_HONG_KONG_UNIVERSITIES = [
    "City University of Hong Kong",
    "Hong Kong Baptist University",
    "Lingnan University",
    "The Chinese University of Hong Kong",
    "The Education University of Hong Kong",
    "The Hong Kong Polytechnic University",
    "The Hong Kong University of Science and Technology",
    "The University of Hong Kong",
]

# Robust Institutional Aliases Mapping to Canonical University Names
UNIVERSITY_ALIASES = {
    # CityU
    "cityu": "City University of Hong Kong",
    "city university of hong kong": "City University of Hong Kong",
    "city university": "City University of Hong Kong",
    "cityu hk": "City University of Hong Kong",
    
    # HKBU
    "hkbu": "Hong Kong Baptist University",
    "hong kong baptist university": "Hong Kong Baptist University",
    "baptist university": "Hong Kong Baptist University",
    "baptist u": "Hong Kong Baptist University",
    
    # Lingnan
    "lu": "Lingnan University",
    "lingnan": "Lingnan University",
    "lingnan university": "Lingnan University",
    "lingnan u": "Lingnan University",
    
    # CUHK
    "cuhk": "The Chinese University of Hong Kong",
    "chinese university of hong kong": "The Chinese University of Hong Kong",
    "the chinese university of hong kong": "The Chinese University of Hong Kong",
    "chinese u of hong kong": "The Chinese University of Hong Kong",
    
    # EdUHK
    "eduhk": "The Education University of Hong Kong",
    "the education university of hong kong": "The Education University of Hong Kong",
    "education university of hong kong": "The Education University of Hong Kong",
    "ied": "The Education University of Hong Kong",
    
    # PolyU
    "polyu": "The Hong Kong Polytechnic University",
    "the hong kong polytechnic university": "The Hong Kong Polytechnic University",
    "hong kong polytechnic university": "The Hong Kong Polytechnic University",
    "hk polyu": "The Hong Kong Polytechnic University",
    "polytechnic university": "The Hong Kong Polytechnic University",
    
    # HKUST
    "hkust": "The Hong Kong University of Science and Technology",
    "the hong kong university of science and technology": "The Hong Kong University of Science and Technology",
    "hong kong university of science and technology": "The Hong Kong University of Science and Technology",
    "ust": "The Hong Kong University of Science and Technology",
    "hkust-gz": "The Hong Kong University of Science and Technology",
    
    # HKU
    "hku": "The University of Hong Kong",
    "the university of hong kong": "The University of Hong Kong",
    "university of hong kong": "The University of Hong Kong",
    "u of hong kong": "The University of Hong Kong",
}

# 2. TARGET RESEARCH KEYWORDS & DOMAINS
RESEARCH_KEYWORDS = {
    "core": [
        "edge computing", "edge intelligence", "edge ai", "mobile edge computing",
        "mec", "multi-access edge computing", "edge-cloud computing", "edge-cloud continuum",
        "cloud-edge systems", "edge systems"
    ],
    "distributed_systems": [
        "distributed systems", "distributed computing", "cloud computing", "cloud-edge systems",
        "distributed ai", "distributed machine learning", "federated learning", "consensus",
        "fault tolerance", "distributed storage", "crdt"
    ],
    "networking": [
        "computer networks", "wireless networks", "5g", "6g", "mobile networks",
        "network optimization", "network intelligence", "wireless edge networks",
        "sdn", "software-defined networking", "network slicing", "urllc", "v2x"
    ],
    "ai_iot": [
        "aiot", "internet of things", "iot", "intelligent iot", "edge machine learning",
        "tinyml", "ai systems", "resource-constrained ai", "model compression",
        "quantization", "embedded ai"
    ],
    "optimization_systems": [
        "resource allocation", "scheduling", "task offloading", "computation offloading",
        "edge orchestration", "network optimization", "distributed optimization",
        "serverless edge computing", "faas", "convex optimization", "reinforcement learning"
    ]
}

# 3. RESEARCHER ELIGIBILITY & ALIGNMENT WEIGHTS (100% Total)
RESEARCHER_SCORING_WEIGHTS = {
    "research_alignment": 0.35,      # Overlap with Edge Computing & Distributed Systems
    "current_activity": 0.20,        # Recent papers, active grants, lab vitality
    "phd_recruitment": 0.30,         # Evidence of open PhD positions & active recruiting
    "academic_strength": 0.10,       # IEEE/ACM Fellows, impactful citations, high-tier venues
    "research_accessibility": 0.05   # Availability of public code, preprints, websites
}

# 4. COMPOSITE OPPORTUNITY SCORING WEIGHTS (100% Total)
OPPORTUNITY_SCORING_WEIGHTS = {
    "research_alignment": 0.30,
    "supervisor_recruitment": 0.20,
    "scholarship_quality": 0.20,
    "application_feasibility": 0.15,
    "deadline_urgency": 0.10,
    "research_familiarity_gap": 0.05
}

# 5. RESEARCHER FAMILIARITY WEIGHTS (100% Total)
FAMILIARITY_WEIGHTS = {
    "profile_understanding": 0.20,
    "publication_exposure": 0.20,
    "research_trajectory": 0.20,
    "recent_research": 0.15,
    "methodology": 0.10,
    "current_projects": 0.10,
    "recruitment_awareness": 0.05
}

# 6. RECRUITMENT STATUS ENUMS & FRESHNESS
RECRUITMENT_STATUSES = [
    "CONFIRMED_ACTIVE",
    "STRONG_EVIDENCE",
    "POSSIBLE",
    "UNKNOWN",
    "NOT_CURRENTLY_RECRUITING",
    "RECRUITMENT_STALE"
]

RECRUITMENT_FRESHNESS_DAYS = 365  # 12-month freshness window

# 7. 10-WEEK CAMPAIGN PHASES & MILESTONES
CAMPAIGN_WEEKS_TOTAL = 10

CAMPAIGN_MILESTONES = {
    1: {
        "name": "Week 1: University & Supervisor Discovery",
        "description": "Assess all 8 target universities, identify 20-30 candidate researchers, map scholarships & deadlines.",
        "deliverable": "Comprehensive Hong Kong 8-University Supervisor & Scholarship Directory",
        "phase": "Discovery"
    },
    2: {
        "name": "Week 2: Candidate Qualification & Shortlisting",
        "description": "Filter candidates down to 10-15 top potential supervisors with matched scholarships and PhD programs.",
        "deliverable": "Tier-1 Shortlist of 10-15 Qualified Supervisors + Scholarship Mapping",
        "phase": "Qualification"
    },
    3: {
        "name": "Weeks 3-4: Deep Research & Publication Analysis",
        "description": "Analyze publication history, research trajectories, current grants, and methodologies for top 5-10 candidates.",
        "deliverable": "Deep Technical Deconstruction Dossiers for Top 5-10 Supervisors",
        "phase": "Deep Research"
    },
    4: {
        "name": "Weeks 3-4: Methodology & Research Gap Deconstruction",
        "description": "Identify unaddressed research gaps, simulators used, and active project extensions.",
        "deliverable": "Research Gap & Methodology Analysis Matrix",
        "phase": "Deep Research"
    },
    5: {
        "name": "Weeks 5-6: Research Alignment & Question Formulation",
        "description": "Formulate 2-3 specific Research Questions (RQs) aligned with each priority supervisor.",
        "deliverable": "Supervisor-Aligned Research Questions & Initial Outreach Email Drafts",
        "phase": "Alignment"
    },
    6: {
        "name": "Weeks 5-6: Personalized Supervisor Outreach",
        "description": "Send tailored outreach emails demonstrating genuine familiarity with their recent publications.",
        "deliverable": "Supervisor Outreach Sent & Responses Logged",
        "phase": "Alignment"
    },
    7: {
        "name": "Weeks 7-8: Research Proposal & Application Materials",
        "description": "Draft 5-page PhD research proposal, tailored CV, statement of purpose, and arrange reference letters.",
        "deliverable": "Polished PhD Research Proposal + Tailored Academic CV + SOP Draft",
        "phase": "Application Preparation"
    },
    8: {
        "name": "Weeks 7-8: Portal Setup & Transcript Verification",
        "description": "Create accounts on RGC HKPFS portal and individual university graduate admissions portals.",
        "deliverable": "All University Portal Profiles Initialized & Required Documents Uploaded",
        "phase": "Application Preparation"
    },
    9: {
        "name": "Week 9: Final Compliance Review & Quality Audit",
        "description": "Audit eligibility, supervisor pre-approval status, scholarship requirements, and deadline verifications.",
        "deliverable": "Pre-Submission Quality Audit & Final Proposal Proofing Complete",
        "phase": "Final Review"
    },
    10: {
        "name": "Week 10: Formal Application Submission",
        "description": "Submit RGC HKPFS application ahead of Dec 1 noon deadline and finalize institutional submissions.",
        "deliverable": "HKPFS Reference Number Obtained & University Applications Submitted",
        "phase": "Submission"
    }
}

# Standard Reference Deadlines for Hong Kong PhD Admissions
KEY_DEADLINES = {
    "HKPFS_RGC_DEADLINE": "2026-12-01 12:00:00 HKT",  # RGC HKPFS Initial Application Deadline
    "HKU_MAIN_ROUND": "2026-12-01 23:59:59 HKT",
    "HKUST_MAIN_ROUND": "2026-12-01 23:59:59 HKT",
    "CUHK_MAIN_ROUND": "2026-12-01 23:59:59 HKT",
    "POLYU_MAIN_ROUND": "2026-12-01 23:59:59 HKT",
    "CITYU_MAIN_ROUND": "2026-12-01 23:59:59 HKT",
    "HKBU_MAIN_ROUND": "2026-12-01 23:59:59 HKT",
    "LINGNAN_MAIN_ROUND": "2026-12-01 23:59:59 HKT",
    "EDUHK_MAIN_ROUND": "2026-12-01 23:59:59 HKT"
}
