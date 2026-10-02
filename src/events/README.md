# Events Intelligence Modules: Edge Computing & ML/Embedded/IoT

The **Events Intelligence System** provides automated discovery, tracking, verification, and evaluation for academic conferences, industrial summits, workshops, symposia, webinars, and doctoral training programs/bootcamps across two specialized research domains:

1. **Edge Computing**: Edge AI, Distributed Systems, Fog Computing, Cloud-Edge Continuum, MEC, and Mobile Systems.
2. **Machine Learning / Embedded Systems / IoT**: Machine Learning, Deep Learning, Embedded Systems, TinyML, Intelligent IoT, Cyber-Physical Systems (CPS), Computer Vision, and Sensor Networks.

---

## 1. Architectural Pipeline Lifecycle

Both modules strictly adhere to AlertMe's core pipeline design:

```text
Collect ──► Normalize ──► Deduplicate ──► Verify & Filter ──► Score ──► State & Notify
```

1. **Collect (`src/events/collector.py`)**:
   - `EdgeEventCollector`: Gathers events from `config/events.yaml` (curated items and RSS feeds like WikiCFP Edge, IEEE, ACM).
   - `MLEmbeddedIoTEventCollector`: Gathers events from `config/ml_iot_events.yaml` (curated items and RSS feeds for ML, Embedded Systems, and IoT).
   - Generic `ConfigurableEventCollector`: Base collector adaptable to any domain configuration.

2. **Normalize (`src/events/normalizer.py`)**:
   - Standardizes dates to ISO 8601 (`YYYY-MM-DD`).
   - Classifies event types and delivery formats (`in_person`, `online`, `hybrid`).
   - Parses registration fees and detects free vs. hybrid-free events.
   - Extracts discount/subsidy opportunities (student rates, travel grants, scholarships, fee waivers).
   - Captures CFP submission deadlines.

3. **Deduplicate (`src/events/deduplicator.py`)**:
   - Eliminates redundant event listings using canonical URL matching.
   - Acronym resolution across Edge, ML, Embedded, and IoT venues (e.g., `SEC`, `NeurIPS`, `ICLR`, `SenSys`, `IPSN`, `RTSS`, `EMSOFT`, `TinyML`, `MobiSys`, `IoTDI`, `IOTSWC`).
   - Sequence matching with year sensitivity.
   - Merges richer subsidy and registration details into the canonical record.

4. **Verify & Filter (`src/events/verifier.py`)**:
   - Predatory conference and deceptive listing filter (`is_predatory_or_suspicious`): Detects known predatory organizers (WASET, OMICS, etc.) and spam indicators ("guaranteed acceptance", "review in 24 hours"), marking them as `CANCELLED` and inactive.
   - Deadline and status verification: Marks concluded events as `CONCLUDED`, active submission windows as `CFP_OPEN`, and upcoming registration as `REGISTRATION_OPEN`.

5. **Score (`src/events/scorer.py`)**:
   - Transparent 0–10 multi-factor relevance scoring.
   - Domain-specific search specifications and keyword weighting.
   - Source credibility tiers (IEEE, ACM, USENIX, NeurIPS Foundation, ICLR, TinyML Foundation, Oxford, Arm, etc.).
   - Student subsidies and financial accessibility bonuses.
   - Severe negative penalties (-5.0) for cancelled/predatory events.

6. **State & Alert (`src/events/state_manager.py` & `src/events/pipeline.py`)**:
   - Domain-isolated state persistence:
     - Edge: `data/events.json`, `data/seen_events.json`, `data/events_history.json`
     - ML/IoT: `data/ml_iot_events.json`, `data/seen_ml_iot_events.json`, `data/ml_iot_events_history.json`
   - Atomically written JSON stores.
   - Interleaved daily/weekly email notifications with visual domain badges (`⚡ Edge Systems` vs `🤖 ML / Embedded / IoT`).

---

## 2. Event Types & Supported Formats

| Event Type | Identifier | Examples |
| :--- | :--- | :--- |
| **Academic Conference** | `academic_conference` | ACM SEC, NeurIPS, ICLR, ACM SenSys, ACM/IEEE IPSN, IEEE RTSS, EMSOFT |
| **Industrial Conference** | `industry_conference` | Embedded World, tinyML Summit, IOTSWC, KubeCon, Edge Computing World |
| **Workshop & Symposium** | `workshop`, `symposium` | ACM EdgeSys, HotMobile, ICCPS, USENIX HotEdge, IEEE EdgeSP |
| **Webinar** | `webinar` | tinyML Talks, IEEE IoT Webinar Series, LF Edge Technical Series |
| **Training & Bootcamp** | `summer_school`, `training_program`, `bootcamp` | OxML Summer School, CPS-IoT Week Summer School, Arm & Edge Impulse Bootcamp |

Delivery formats supported:
- `in_person`: Physical on-site attendance
- `online`: 100% Virtual / live stream / on-demand
- `hybrid`: Dual in-person with remote track

---

## 3. Data Model Schema (`EdgeEvent` / `MLEmbeddedIoTEvent`)

Both domains use the unified `EdgeEvent` dataclass ([`src/events/models.py`](models.py)), also aliased as `MLEmbeddedIoTEvent` and `EventItem`:

- `event_name` (`str`): Full event name.
- `organizer` (`str`): Professional body, university lab, or industry association.
- `domain` (`str`): `edge_computing` or `ml_embedded_iot`.
- `event_type` (`str`): Event category (`academic_conference`, `workshop`, `webinar`, etc.).
- `description` (`str`): Cleaned description of tracks, scope, and technical themes.
- `topics` (`List[str]`): List of matched keywords and tracks.
- `start_date` / `end_date` (`str`, ISO YYYY-MM-DD): Event execution dates.
- `location` (`str`): City, State, Country or "Online".
- `format` (`str`): `in_person`, `online`, or `hybrid`.
- `official_website` (`str`): Canonical website URL.
- `registration_url` (`str`): Direct attendee registration URL.
- `registration_fee` (`str`): Fee string (e.g., "$350 (Student) / $750 (Regular)").
- `fee_status` (`str`): `free`, `paid`, `hybrid_free`, or `unknown`.
- `discounts_subsidies` (`List[DiscountOpportunity]`): Structured list of student rates, travel grants, scholarships, early-bird rates, and fee waivers.
- `discount_eligibility` (`str`): Summarized student eligibility requirements.
- `has_student_discount` (`bool`): True if subsidized student ticket is offered.
- `has_travel_grant` (`bool`): True if travel stipend (STG) is available.
- `has_scholarship` (`bool`): True if attendance fellowship/scholarship exists.
- `has_early_bird` (`bool`): True if early registration window is active.
- `has_fee_waiver` (`bool`): True if 100% free virtual or hardship waiver exists.
- `cfp_deadline` (`Optional[str]`): Paper or poster submission cutoff date.
- `important_dates` (`Dict[str, str]`): Key dates (notification, camera-ready, early bird).
- `target_audience` (`List[str]`): Targeted roles (PhD researchers, engineers, faculty).
- `status` (`str`): `upcoming`, `cfp_open`, `registration_open`, `ongoing`, `concluded`, `cancelled`.
- `relevance_score` (`float`): 0–10 score with `EventScoreBreakdown`.

---

## 4. Transparent 0–10 Multi-Factor Scoring

Events are scored objectively out of 10.0 using six dimensions:

$$\text{Final Score} = \min(10.0, \text{Topic} + \text{Credibility} + \text{Affordability} + \text{Actionability} + \text{PhD Boost} + \text{Penalty})$$

1. **Topic Relevance (0 to 4.0 points)**:
   - Primary domain keyword in title: **+2.5** (e.g., *Machine Learning*, *Embedded Systems*, *IoT*, *TinyML*, *Edge AI*).
   - Match in description: **+1.8**.
   - Multi-topic synergy across tracks: **+0.7 to +1.2**.
   - Secondary systems keywords: **+0.4 to +0.8**.
2. **Source Credibility (0 to 2.5 points)**:
   - Tier 1: IEEE, ACM, USENIX, NeurIPS, ICLR, AAAI, ICML, CVPR: **+2.5**.
   - Tier 2: TinyML Foundation, Oxford, Cambridge, MIT, Stanford, Arm, Edge Impulse: **+2.0**.
   - Tier 3: Reputable industrial consortia and associations: **+1.5**.
3. **Affordability & Student Subsidies (0 to 1.5 points)**:
   - 100% Free event: **+1.0** (Free virtual track: **+0.8**).
   - Student Travel Grant (STG) / Travel stipend: **+0.8**.
   - Subsidized student registration rate: **+0.5**.
   - Diversity scholarship or fee waiver: **+0.5**.
4. **Actionability & Urgency (0 to 1.0 points)**:
   - Open CFP closing within 60 days: **+0.7** (urgent alert if $\le 14$ days).
   - Event happening within 120 days: **+0.3**.
   - Active early-bird window: **+0.3**.
5. **PhD Value & Research Track (0 to 1.0 points)**:
   - Doctoral symposium / student research competition: **+0.8**.
   - Doctoral summer school / technical training program: **+0.7**.
   - Peer-reviewed research conference or workshop: **+0.5**.
6. **Negative Penalties (0 to -5.0 points)**:
   - Predatory / suspicious / fake conference claims: **-5.0**.
   - Concluded / expired event: **-4.0**.
   - Non-technical spam, generic commercial bootcamps: **-3.0**.

---

## 5. CLI Commands

The module integrates directly into AlertMe's root CLI:

```bash
# Discover active events across all domains (Edge + ML/Embedded/IoT)
python cli.py events --domain all

# Filter specifically for Edge Computing events
python cli.py events --domain edge

# Filter specifically for ML / Embedded / IoT events
python cli.py events --domain ml_iot

# Filter by event type
python cli.py events --type academic_conference
python cli.py events --type workshop
python cli.py events --type webinar
python cli.py events --type summer_school

# Filter by financial subsidies and travel grants
python cli.py events --student-rates
python cli.py events --travel-grants

# Filter for events with open CFP submission deadlines
python cli.py events --open-cfps

# Filter by delivery format
python cli.py events --format online
python cli.py events --format in_person

# Export Markdown summary digest
python cli.py events --domain all --export-markdown reports/upcoming_events.md

# Test connectivity and metrics of all configured event feeds
python cli.py test-event-sources
```

---

## 6. How to Add New Event Sources

### Option A: Add a Curated ML / Embedded / IoT Event (No Code Required)

Open `config/ml_iot_events.yaml` and append a new entry under `curated_events`:

```yaml
curated_events:
  - event_name: "ACM SenSys 2027"
    organizer: "ACM SIGMOBILE"
    event_type: "academic_conference"
    description: "Conference on Embedded Networked Sensor Systems, low-power ML, and intelligent IoT."
    topics:
      - "Embedded Systems"
      - "IoT"
      - "TinyML"
      - "Sensor Networks"
    start_date: "2027-11-10"
    end_date: "2027-11-13"
    location: "Delft, Netherlands"
    format: "in_person"
    official_website: "https://sensys.acm.org/2027/"
    registration_fee: "$400 (Student) / $850 (Regular)"
    fee_status: "paid"
    has_student_discount: true
    has_travel_grant: true
    discounts_subsidies:
      - discount_type: "travel_grant"
        name: "ACM SIGMOBILE Student Travel Grant"
        amount_or_rate: "Up to $1,200"
        eligibility: "Student authors presenting research."
    cfp_deadline: "2027-05-15"
```

### Option B: Add an RSS/Atom Event Feed

In `config/ml_iot_events.yaml` (or `config/events.yaml` for Edge), append under `event_feeds`:

```yaml
event_feeds:
  - name: "WikiCFP Embedded Systems Feed"
    url: "http://www.wikicfp.com/cfp/rss?cat=embedded%20system"
    type: "rss"
    default_event_type: "academic_conference"
    tier: "tier1_academic_standards"
    enabled: true
```

The collector automatically polls the feed, extracts titles, parses dates, matches keywords, verifies deadlines, and filters out predatory sources.

---

## 7. Email Digest Integration

The event discovery pipeline runs automatically as part of the daily PhD Alert pipeline.
Both Edge Computing and ML/Embedded/IoT events are scored and balanced so that top-ranking opportunities from both domains are displayed in the daily alert email:

- `⚡ Edge Systems` badge: Highlights edge architectures, MEC, and cloud-edge continuum events.
- `🤖 ML / Embedded / IoT` badge: Highlights machine learning, TinyML, embedded systems, and intelligent IoT events.
- Subsidies such as **Student Rates Available**, **Student Travel Grant**, **Early Bird**, and **100% Free** are prominently badged in the digest cards.
