# Edge Computing Events Module

The **Edge Computing Events Module** is an automated discovery, tracking, and evaluation system for academic conferences, industrial summits, workshops, symposia, webinars, and doctoral training programs/bootcamps related to **Edge Computing, Edge AI, Distributed Systems, Fog Computing, Cloud-Edge Continuum, and MEC**.

---

## 1. Architectural Pipeline Lifecycle

The module strictly adheres to AlertMe's core design pattern:

```text
Collect ──► Normalize ──► Deduplicate ──► Verify ──► Score ──► State & Notify
```

1. **Collect (`src/events/collector.py`)**: Fetches events from curated registries (`config/events.yaml`) and active RSS/Atom event feeds (e.g. WikiCFP, IEEE, ACM, Linux Foundation).
2. **Normalize (`src/events/normalizer.py`)**: Standardizes dates to ISO 8601, classifies event types and delivery formats (in-person, online, hybrid), parses registration fees, extracts discount/subsidy opportunities, and captures CFP deadlines.
3. **Deduplicate (`src/events/deduplicator.py`)**: Eliminates redundant event listings using canonical URL matching, acronym resolution (e.g., matching "SEC 2026" with "ACM/IEEE Symposium on Edge Computing 2026"), and sequence matching with year sensitivity. Merges richer subsidy and registration details into the canonical record.
4. **Verify (`src/events/verifier.py`)**: Checks event dates and CFP deadlines against current time, marking passed events as `CONCLUDED`, active submission windows as `CFP_OPEN`, and upcoming registration as `REGISTRATION_OPEN`.
5. **Score (`src/events/scorer.py`)**: Calculates a transparent 0–10 multi-factor relevance score prioritizing PhD-relevant research, IEEE/ACM/USENIX credibility, student subsidies, and active submission timelines.
6. **State & Alert (`src/events/state_manager.py` & `src/events/pipeline.py`)**: Persists active items atomically in `data/events.json`, tracks seen event IDs in `data/seen_events.json`, records history in `data/events_history.json`, and generates Markdown/email briefings.

---

## 2. Event Types & Supported Formats

| Event Type | Identifier | Examples |
| :--- | :--- | :--- |
| **Academic Conference** | `academic_conference` | ACM SEC, IEEE INFOCOM, ACM MobiCom, USENIX ATC, IEEE ICDCS |
| **Industrial Conference** | `industry_conference` | KubeCon + CloudNativeCon, Edge Computing World, OpenInfra Summit |
| **Workshop & Symposium** | `workshop`, `symposium` | ACM EdgeSys, USENIX HotEdge, IEEE EdgeSP |
| **Webinar** | `webinar` | LF Edge Technical Webinar Series, IEEE ComSoc 6G Edge Series |
| **Training & Bootcamp** | `summer_school`, `training_program`, `bootcamp` | TinyML Summer School, IEEE ComSoc School, LF Edge Bootcamp |

Delivery Formats supported:
- `in_person`: Physical on-site attendance
- `online`: 100% Virtual / live stream / on-demand
- `hybrid`: Dual in-person with remote track

---

## 3. Data Model Schema (`EdgeEvent`)

Each event is modeled as an `EdgeEvent` dataclass ([`src/events/models.py`](models.py)) with the following core attributes:

- `event_name` (`str`): Full event name.
- `organizer` (`str`): Professional body, university lab, or industry association.
- `event_type` (`str`): One of the event types above.
- `description` (`str`): Cleaned description of tracks, scope, and technical themes.
- `topics` (`List[str]`): List of matched edge computing keywords and tracks.
- `start_date` / `end_date` (`str`, ISO YYYY-MM-DD): Event execution dates.
- `location` (`str`): City, State, Country or "Online".
- `format` (`str`): `in_person`, `online`, or `hybrid`.
- `official_website` (`str`): Canonical website URL.
- `registration_url` (`str`): Direct attendee registration URL.
- `registration_fee` (`str`): Fee string (e.g., "$350 (Student) / $750 (Regular)").
- `fee_status` (`str`): `free`, `paid`, `hybrid_free`, or `unknown`.
- `discounts_subsidies` (`List[DiscountOpportunity]`): Structured list of student rates, travel grants, scholarships, early bird discounts, and fee waivers.
- `discount_eligibility` (`str`): Summarized student eligibility requirements.
- `has_student_discount` (`bool`): True if subsidized student ticket is offered.
- `has_travel_grant` (`bool`): True if travel stipend (e.g. STG) is available.
- `has_scholarship` (`bool`): True if attendance fellowship/scholarship exists.
- `has_early_bird` (`bool`): True if early registration window is active.
- `has_fee_waiver` (`bool`): True if 100% free virtual or hardship waiver exists.
- `cfp_deadline` (`Optional[str]`): Paper or poster submission cutoff date.
- `important_dates` (`Dict[str, str]`): Key dates (notification, camera-ready, early bird).
- `target_audience` (`List[str]`): Targeted roles (PhD researchers, engineers, faculty).
- `status` (`str`): `upcoming`, `cfp_open`, `registration_open`, `ongoing`, `concluded`.
- `relevance_score` (`float`): 0–10 score with `EventScoreBreakdown`.

---

## 4. Transparent 0–10 Multi-Factor Scoring

Events are scored objectively out of 10.0 using six dimensions:

$$\text{Final Score} = \min(10.0, \text{Topic} + \text{Credibility} + \text{Affordability} + \text{Actionability} + \text{PhD Boost} + \text{Penalty})$$

1. **Topic Relevance (0 to 4.0 points)**:
   - Primary focus in event title: **+2.5** (e.g. *Edge Computing*, *Edge AI*, *MEC*, *Fog Computing*).
   - Match in description: **+1.8**.
   - Multi-topic edge synergy across tracks: **+0.7 to +1.2**.
   - Secondary systems keywords (Distributed Systems, IoT, TinyML, Serverless): **+0.4 to +0.8**.
2. **Source Credibility (0 to 2.5 points)**:
   - Tier 1 Professional Bodies (IEEE, ACM, USENIX): **+2.5**.
   - Tier 2 Open Source Foundations & Universities (Linux Foundation, CNCF, Harvard, Cambridge): **+2.0**.
   - Tier 3 Industry Consortia (Topio, TinyML Foundation, Eclipse): **+1.5**.
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
   - Concluded / expired event: **-4.0**.
   - Non-technical spam, crypto, generic web dev bootcamps: **-3.0**.

---

## 5. CLI Commands

The module integrates directly into AlertMe's root CLI:

```bash
# Discover active events meeting default threshold (6.5)
python cli.py events

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
python cli.py events --export-markdown reports/upcoming_edge_events.md

# Test connectivity and metrics of all configured event feeds
python cli.py test-event-sources

# Debug transparent 0-10 score for any candidate event
python cli.py debug-event-score \
  --name "ACM/IEEE Symposium on Edge Computing (SEC 2026)" \
  --organizer "ACM / IEEE" \
  --description "Doctoral symposium and student travel grants available." \
  --fee "$350 Student" \
  --cfp "2026-11-15" \
  --date "2026-11-10"
```

---

## 6. How to Add New Event Sources

### Option A: Add a Curated Event (No Code Required)

Open `config/events.yaml` and append a new entry under `curated_events`:

```yaml
curated_events:
  - event_name: "IEEE SECON 2027"
    organizer: "IEEE Communications Society"
    event_type: "academic_conference"
    description: "International Conference on Sensing, Communication, and Networking with edge sensing and TinyML tracks."
    topics:
      - "Edge Computing"
      - "IoT"
      - "TinyML"
    start_date: "2027-06-20"
    end_date: "2027-06-23"
    location: "Rome, Italy"
    format: "in_person"
    official_website: "https://secon2027.ieee-secon.org/"
    registration_fee: "€380 (Student) / €750 (Regular)"
    fee_status: "paid"
    has_student_discount: true
    has_travel_grant: true
    discounts_subsidies:
      - discount_type: "student_rate"
        name: "IEEE Student Member Rate"
        amount_or_rate: "€380"
        eligibility: "Enrolled students with valid IEEE ID."
      - discount_type: "travel_grant"
        name: "IEEE ComSoc Travel Grant"
        amount_or_rate: "Up to €1,000"
        eligibility: "Student authors presenting papers."
    cfp_deadline: "2027-01-15"
```

### Option B: Add an RSS/Atom Event Feed

In `config/events.yaml`, append under `event_feeds`:

```yaml
event_feeds:
  - name: "USENIX Upcoming Conferences Feed"
    url: "https://www.usenix.org/conferences/upcoming.xml"
    type: "rss"
    default_event_type: "academic_conference"
    tier: "tier1_academic_standards"
    enabled: true
```

The `EdgeEventCollector` will automatically poll the feed, extract titles, parse dates, match keywords, and verify deadlines.

### Option C: Adding a Custom API or Scraper Collector

To add programmatic scrapers (e.g. for a custom university portal or GraphQL API):
1. Subclass `BaseCollector` or extend `EdgeEventCollector` in `src/events/collector.py`.
2. Yield raw event dictionaries.
3. Pass them through `self.normalizer.normalize(raw_data)`.
4. The pipeline handles deduplication, verification, scoring, and alerting automatically.
