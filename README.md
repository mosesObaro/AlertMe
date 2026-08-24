# Automated Edge Computing PhD Research Intelligence & Email Alert System

[![CI Tests](https://github.com/mosesObaro/AlertMe/actions/workflows/tests.yml/badge.svg)](https://github.com/mosesObaro/AlertMe/actions/workflows/tests.yml)
[![Daily Research Alert](https://github.com/mosesObaro/AlertMe/actions/workflows/daily-alert.yml/badge.svg)](https://github.com/mosesObaro/AlertMe/actions/workflows/daily-alert.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An autonomous, high-precision academic research intelligence and alert assistant built to accelerate preparation for a **PhD in Edge Computing, Edge Intelligence, and Distributed Systems**. 

Hosted on **100% free infrastructure** (GitHub Actions, GitHub Pages, and free-tier academic APIs & email providers), the system continuously discovers, filters, scores, analyzes, deduplicates, and delivers research papers, PhD openings, conference CFPs, and emerging research trends directly to your email.

> **Core Philosophy**: *Optimize for signal, not volume.* Receive 5–10 deeply analyzed, high-relevance research developments instead of dozens of noisy links.

---

## 1. System Architecture

```
                          ┌──────────────────────────────────────┐
                          │          GitHub Repository           │
                          │  • config/ (topics, profile, confs)  │
                          │  • data/ (state, seen_items.json)    │
                          │  • docs/ (GitHub Pages Web UI)       │
                          └──────────────────┬───────────────────┘
                                             │ Scheduled Cron / Dispatch
                                             ▼
                          ┌──────────────────────────────────────┐
                          │      GitHub Actions Runner (CI)      │
                          └──────────────────┬───────────────────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             ▼                               ▼                               ▼
  ┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐
  │ Academic & Preprints │        │   Feeds & Standards  │        │   Opportunities &    │
  │ • OpenAlex API       │        │ • arXiv CS Feeds     │        │     Conferences      │
  │ • Semantic Scholar   │        │ • ETSI / 3GPP / NIST │        │ • WikiCFP / Conf RSS │
  │ • Crossref API       │        │ • IEEE / ACM TOCs    │        │ • AcademicPositions  │
  │ • arXiv API          │        │ • University Lab RSS │        │ • GitHub Edge Repos  │
  └──────────┬───────────┘        └──────────┬───────────┘        └──────────┬───────────┘
             │                               │                               │
             └───────────────────────────────┼───────────────────────────────┘
                                             ▼
                          ┌──────────────────────────────────────┐
                          │       1. Ingestion & Normalize       │
                          │     (Title, DOI, arXiv, Authors)     │
                          └──────────────────┬───────────────────┘
                                             ▼
                          ┌──────────────────────────────────────┐
                          │       2. Deduplication Engine        │
                          │  (DOI, arXiv ID, URL, Fuzzy Title)   │
                          └──────────────────┬───────────────────┘
                                             ▼
                          ┌──────────────────────────────────────┐
                          │      3. Relevance & PhD Scoring      │
                          │   • Multi-factor 0–10 point engine   │
                          │   • Learning Stage Alignment         │
                          │   • Academic Credibility Tiers       │
                          └──────────────────┬───────────────────┘
                                             ▼
                          ┌──────────────────────────────────────┐
                          │    4. Paper Intelligence & Analysis  │
                          │   • Deterministic NLP (Zero cost)    │
                          │   • Optional LLM (Gemini/Groq)       │
                          │   • Research Gap & Trend Analyzer    │
                          │   • Supervisor Discovery Tracker     │
                          └──────────────────┬───────────────────┘
                                             ▼
                          ┌──────────────────────────────────────┐
                          │       5. State Persistence & Web     │
                          │   • Commit data/seen_items.json      │
                          │   • Update docs/data.json (Pages UI) │
                          └──────────────────┬───────────────────┘
                                             ▼
                          ┌──────────────────────────────────────┐
                          │      6. Multi-Channel Email Alert    │
                          │   • Resend / Brevo / SMTP / SendGrid │
                          │   • Daily Briefing & Weekly Digest   │
                          │   • Urgent High-Priority Alert       │
                          └──────────────────────────────────────┘
```

---

## 2. Key Capabilities & Features

1. **Multi-Factor Transparent Relevance Scoring (0–10 scale)**
   - Distinguishes high-signal edge intelligence from low-relevance generic tutorials and off-topic AI news.
   - Every alert includes a transparent *"Why you received this"* breakdown.
2. **Deterministic Paper Intelligence (Zero-Cost / No LLM Required)**
   - Heuristic NLP rule-based extraction isolates:
     - **Why it matters**
     - **Research problem**
     - **Methodology**
     - **Key contribution**
     - **Potential research gap** (clearly flagged as a candidate direction for deeper literature review).
   - Pluggable optional LLM mode (Google Gemini Flash / Groq / OpenAI) if desired.
3. **Personalization Based on Learning Stage**
   - Learns your active study phase from `config/profile.yaml` (e.g. *Computation Offloading*, *Distributed Inference*, *Federated Learning*) and dynamically prioritizes relevant papers.
4. **PhD Application Mode**
   - Automatically detects proximity to your target PhD application deadline and amplifies PhD studentships, scholarships, conference submission deadlines, and research lab vacancies.
5. **Supervisor & Researcher Discovery**
   - Tracks prolific authors appearing across top-tier publications in your target topics to identify potential PhD supervisors without claiming unverified vacancies.
6. **Emerging Research Trend Velocity**
   - Analyzes 30-day n-gram velocity and flags observed topic shifts (`↑↑`, `↑`, `→`, `↓`).
7. **Weekly "Recommended Focus for Next Week"**
   - Synthesizes: 1 Concept to Master, 1 Primary Paper, 1 Practical Experiment/Simulation, 1 Research Question, and 1 Venue/Opportunity.
8. **Multi-Stage Academic Deduplication**
   - Deduplicates across DOI, arXiv ID, canonical URL, and fuzzy title similarity (Jaccard + Levenshtein), merging richer metadata across publishers.
9. **Interactive Static Web Dashboard (GitHub Pages)**
   - Fast client-side dashboard with dark/light mode, instant search, topic pills, and knowledge base browser located in `docs/`.
10. **Zero-Cost Ephemeral State Persistence**
    - Automatically commits updated indices (`data/seen_items.json`, `data/alert_history.json`, `data/trends.json`) back to the GitHub repository at the end of each Actions run.

---

## 3. Credibility Hierarchy & Discovery Sources

### Tier 1 — Academic & Standards (Highest Priority)
* **Academic APIs**: arXiv API (cs.DC, cs.NI, cs.AI), OpenAlex Works API, Crossref API (IEEE, ACM, Springer, Elsevier), Semantic Scholar Graph API.
* **Standards Bodies**: ETSI MEC RSS, NIST Computer Security/IoT, Linux Foundation / LF Edge, Cloud Native Computing Foundation (CNCF).

### Tier 2 — Top Universities & Research Labs
* Carnegie Mellon University (Living Edge Lab)
* Princeton University (EDGE Lab)
* MIT CSAIL
* UC Berkeley (RISELab / Sky Computing Lab)
* TU Wien (Distributed Systems Group)
* University of Cambridge (Systems Research Group)
* UT Austin (WNCG)

### Tier 3 — Premier Conferences & CFPs
* ACM SEC (Symposium on Edge Computing)
* IEEE INFOCOM
* ACM MobiCom
* USENIX ATC & USENIX NSDI
* IEEE ICDCS
* ACM EdgeSys & IEEE SECON
* IEEE CLOUD & ACM SenSys
* WikiCFP & USENIX upcoming deadline feeds

### Tier 4 — Industry Research Labs
* Google Research
* Microsoft Research
* AWS Architecture & HPC
* Qualcomm Research
* Ericsson Research

---

## 4. Relevance Scoring System Explained

Every discovered item is scored on a **0.0 to 10.0 scale**:

$$\text{Final Score} = \min(10.0, \max(0.0, \text{Topic} + \text{Credibility} + \text{Recency} + \text{Stage} + \text{PhD} - \text{Penalty}))$$

| Factor | Points | Evaluation Details |
| :--- | :---: | :--- |
| **Topic Match** | **0.0 – 4.0** | Matches primary topics (*Edge AI*, *MEC*, *Offloading*) in title (2.8–3.4 pts) or abstract (2.2 pts). Research sub-topic bonuses (+0.4 to +0.8 pts). |
| **Source Credibility** | **0.0 – 2.5** | Tier 1 Academic/Standards (+2.5), Tier 2 Top Labs (+2.0), Tier 3 Conferences (+1.5), Tier 4 Industry (+1.0), Unknown (+0.5). |
| **Recency** | **0.0 – 1.5** | $\le 3$ days (+1.5), $\le 7$ days (+1.2), $\le 14$ days (+0.8), $\le 30$ days (+0.5), $>30$ days (+0.2). |
| **Learning Stage** | **0.0 – 1.0** | Explicit boost if content matches your active topic in `profile.yaml -> learning_stage.current_topics`. |
| **PhD / Opportunity** | **0.0 – 1.0** | Boost for PhD studentships (+1.0), CFPs (+0.8), Surveys (+0.7), Benchmarks (+0.5). |
| **Negative Penalty** | **0.0 to -5.0** | Penalizes off-topic tutorials, generic AI news without edge context, crypto, and affiliate content. |

### Priority Thresholds
* 🔴 **Critical ($\ge 9.0$)**: Immediate / urgent email dispatch (or deadline $\le 14$ days).
* 🟠 **High ($\ge 7.5$)**: Included in the **Daily Briefing** (Target: 5–10 items).
* 🟡 **Moderate ($\ge 6.8$)**: Included in the **Weekly Digest** (Target: 10–20 items).
* ⚪ **Low ($< 6.5$)**: Filtered out and ignored.

---

## 5. Free Deployment & Setup Guide

### Step 1: Fork or Clone the Repository
```bash
git clone https://github.com/mosesObaro/AlertMe.git
cd AlertMe
```

### Step 2: Configure Your Profile
Run the interactive configuration wizard:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.cli setup
```
Or directly edit `config/profile.yaml` and `config/topics.yaml`:

```yaml
# config/profile.yaml
phd_target:
  field: "Edge Computing"
  target_application_period: "2027-01-01"

learning_stage:
  current_level: 3
  current_topics:
    - "Edge AI"
    - "Computation Offloading"
    - "Distributed Inference"

email_preferences:
  provider: "resend" # Options: resend, brevo, smtp, sendgrid, console
  sender_email: "research-alert@resend.dev"
  recipient_email: "${EMAIL_RECIPIENT}"
```

### Step 3: Configure Free Email Provider
Choose any free email service:
* **Resend (Recommended)**: 3,000 free emails/month. Sign up at [resend.com](https://resend.com), create an API key, and use sender `onboarding@resend.dev` or your verified domain.
* **Brevo (formerly Sendinblue)**: 300 free emails/day. Sign up at [brevo.com](https://brevo.com).
* **Gmail / Custom SMTP**: Generate an App Password in your Google Account security settings.

### Step 4: Configure GitHub Secrets
In your GitHub Repository, navigate to **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions** and add:

| Secret Name | Description | Required For |
| :--- | :--- | :--- |
| `EMAIL_RECIPIENT` | The email address where alerts will be delivered | All Providers |
| `EMAIL_PROVIDER` | `resend`, `brevo`, `smtp`, or `sendgrid` | All Providers |
| `RESEND_API_KEY` | API Key from Resend dashboard | If using Resend |
| `BREVO_API_KEY` | API Key from Brevo dashboard | If using Brevo |
| `SMTP_HOST` | SMTP server host (e.g. `smtp.gmail.com`) | If using SMTP |
| `SMTP_PORT` | SMTP port (e.g. `587` or `465`) | If using SMTP |
| `SMTP_USER` | SMTP username / email address | If using SMTP |
| `SMTP_PASSWORD` | SMTP password / App Password | If using SMTP |
| `GEMINI_API_KEY` | Optional Google AI Studio key for LLM analysis | If AI summarization enabled |

### Step 5: Enable GitHub Actions & GitHub Pages
1. Go to **Actions** in your GitHub repository and ensure workflows are enabled.
2. Go to **Settings** $\rightarrow$ **Pages**, set **Source** to `Deploy from a branch`, choose branch `main` and folder `/docs`.

---

## 6. CLI Commands & Local Development

The unified CLI command center provides local testing and debugging tools:

### 1. Run in Dry-Run Mode (No emails sent, state intact)
```bash
python -m src.cli run --mode daily --dry-run
python -m src.cli run --mode weekly --dry-run
```

### 2. Test All Data Sources & API Health
```bash
python -m src.cli test-sources
```

### 3. Debug Why an Item Received (or Didn't Receive) an Alert
```bash
python -m src.cli debug-score \
  --title "Adaptive Computation Offloading for Edge AI in 6G Networks" \
  --abstract "We formulate an energy-efficient computation offloading algorithm for MEC..." \
  --source "IEEE Transactions on Mobile Computing"
```

Output:
```text
=======================================================
 RELEVANCE SCORING DEBUGGER
=======================================================
Title:       Adaptive Computation Offloading for Edge AI in 6G Networks
Source:      IEEE Transactions on Mobile Computing (tier1_academic_standards)
Date:        Recent
-------------------------------------------------------
Topic Relevance Score:      3.80 / 4.0
Source Credibility Score:   2.50 / 2.5
Recency Boost:              1.50 / 1.5
Learning Stage Boost:       1.00 / 1.0
PhD Preparation Boost:      0.00 / 1.0
Negative Keyword Penalty:   0.00
-------------------------------------------------------
FINAL RELEVANCE SCORE:       8.8 / 10.0
DECISION:                  ✅ INCLUDED IN DAILY DIGEST

TRANSPARENT REASONS:
  ✓ Primary topic match: Edge AI (Title), Computation Offloading (Title)
  ✓ Key research area match: Computation Offloading (+0.4)
  ✓ Tier 1 Academic/Standards source: IEEE Transactions (+2.5)
  ✓ Freshly published (+1.5)
  ✓ Matches your current learning stage topic: Edge AI (+1.0)
=======================================================
```

### 4. Run Pytest Suite
```bash
pytest tests/ -v --cov=src
```

---

## 7. Customization Guide

### How to Add New Research Topics
Edit `config/topics.yaml`:
```yaml
primary_topics:
  - "Split Learning at Edge"
  - "TinyML Inference"

research_topics:
  - "Lyapunov Optimization"
  - "Model Pruning"
```

### How to Add Monitored Conferences
Edit `config/conferences.yaml`:
```yaml
conferences:
  - name: "ACM EuroSys"
    acronym: "EuroSys"
    organizer: "ACM"
    tier: 1
    topics: ["Distributed Systems", "Cloud/Edge"]
    website: "https://eurosys.org"
    typical_deadline_month: 10
```

### How to Add Research Labs
Edit `config/research_groups.yaml`:
```yaml
research_groups:
  - name: "Intelligent Edge Systems Lab"
    lead: "Prof. Jane Doe"
    university: "University of Waterloo"
    website: "https://uwaterloo.ca/edge-lab"
    topics: ["Edge AI", "5G MEC"]
```

---

## 8. Scheduled Workflows Summary

| Workflow | Schedule | Trigger | Action |
| :--- | :--- | :--- | :--- |
| `daily-alert.yml` | Daily at 06:00 UTC | Cron + Manual | Discovers, scores, deduplicates, sends Daily Briefing, persists state to repo. |
| `weekly-digest.yml` | Sundays at 08:00 UTC | Cron + Manual | Analyzes 30-day trends, supervisors, generates weekly study guide, sends digest. |
| `source-health.yml` | 1st & 15th of month | Cron + Manual | Tests all API/feed endpoints and updates health status in `data/source_health.json`. |
| `tests.yml` | Push & Pull Request | Automated | Runs full unit & integration test suite with coverage report. |

---

## 9. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
