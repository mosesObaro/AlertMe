"""Command Line Interface (CLI) for Edge PhD Research Intelligence Assistant."""

import argparse
import sys
import os
import yaml
from pathlib import Path
from src.pipeline import ResearchPipeline
from src.utils.config_loader import ConfigManager
from src.ranking.scorer import RelevanceScorer
from src.models import ResearchItem, CredibilityTier
from src.utils.logger import logger

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def run_pipeline(args):
    """Executes the research intelligence pipeline."""
    pipeline = ResearchPipeline()
    result = pipeline.run(mode=args.mode, dry_run=args.dry_run)
    print("\n" + "=" * 50)
    print(" PIPELINE EXECUTION SUMMARY")
    print("=" * 50)
    print(f"Mode:              {result['mode'].upper()}")
    print(f"Raw Discovered:    {result['raw_items_count']}")
    print(f"Unique Items:      {result['unique_items_count']}")
    print(f"Ranked & Eligible: {result['ranked_items_count']}")
    print(f"Email Dispatched:  {result['email_sent']}")
    if result.get("top_item"):
        print(f"Top Discovery:     {result['top_item']}")
    print("=" * 50 + "\n")


def test_sources(args):
    """Tests connectivity and item retrieval for all configured sources."""
    print("\nTesting all discovery sources...\n")
    pipeline = ResearchPipeline()
    print(f"{'Source Name':<40} | {'Tier':<20} | {'Status':<10} | {'Items'}")
    print("-" * 85)

    for collector in pipeline.collectors:
        items = collector.collect()
        status = collector.last_status
        tier_short = collector.tier.replace("tier", "T").replace("_", " ")
        print(f"{collector.name:<40} | {tier_short:<20} | {status:<10} | {len(items)}")

    print("\nSource testing complete. Metrics stored in data/source_health.json.\n")


def debug_score(args):
    """Debugs why an item scored high or low with full transparent breakdown."""
    scorer = RelevanceScorer()

    # Determine tier
    tier = CredibilityTier.TIER1_ACADEMIC_STANDARDS.value
    if args.tier:
        tier = getattr(CredibilityTier, args.tier, CredibilityTier.TIER1_ACADEMIC_STANDARDS.value)

    item = ResearchItem(
        title=args.title,
        url=args.url or "https://example.com/test-paper",
        source=args.source or "IEEE Transactions",
        source_tier=tier,
        abstract=args.abstract or "",
        publication_date=args.date or ""
    )

    breakdown = scorer.score_item(item)

    print("\n" + "=" * 55)
    print(" RELEVANCE SCORING DEBUGGER")
    print("=" * 55)
    print(f"Title:       {item.title}")
    print(f"Source:      {item.source} ({item.source_tier})")
    print(f"Date:        {item.publication_date or 'Recent'}")
    print("-" * 55)
    print(f"Topic Relevance Score:     {breakdown.topic_score:>5.2f} / 4.0")
    print(f"Source Credibility Score:  {breakdown.credibility_score:>5.2f} / 2.5")
    print(f"Recency Boost:             {breakdown.recency_score:>5.2f} / 1.5")
    print(f"Learning Stage Boost:      {breakdown.stage_boost:>5.2f} / 1.0")
    print(f"PhD Preparation Boost:     {breakdown.phd_boost:>5.2f} / 1.0")
    print(f"Negative Keyword Penalty:  {breakdown.negative_penalty:>5.2f}")
    print("-" * 55)
    print(f"FINAL RELEVANCE SCORE:     {breakdown.final_score:>5.1f} / 10.0")
    
    threshold = scorer.config.alert_thresholds.get("daily_digest_min_score", 7.5)
    decision = "✅ INCLUDED IN DAILY DIGEST" if breakdown.final_score >= threshold else "❌ FILTERED OUT (Below threshold)"
    print(f"DECISION:                  {decision}")
    print("\nTRANSPARENT REASONS:")
    for r in breakdown.reasons:
        print(f"  {r}")
    print("=" * 55 + "\n")


def interactive_setup(args):
    """Interactive wizard to configure profile, topics, email, and preferences."""
    print("\n=======================================================")
    print("  EDGE COMPUTING PhD ASSISTANT — INITIAL SETUP WIZARD  ")
    print("=======================================================\n")

    profile_path = CONFIG_DIR / "profile.yaml"
    topics_path = CONFIG_DIR / "topics.yaml"

    email = input("What email address should receive alerts? [user@example.com]: ").strip() or "user@example.com"
    interests = input("What are your primary research interests? (comma-separated) [Edge AI, MEC, Offloading]: ").strip()
    if not interests:
        interests_list = ["Edge Intelligence", "Computation Offloading", "Resource Allocation"]
    else:
        interests_list = [i.strip() for i in interests.split(",")]

    current_topics = input("What topics are you actively studying right now? [Edge AI, Distributed Inference]: ").strip()
    if not current_topics:
        current_topics_list = ["Edge AI", "Computation Offloading", "Distributed Inference"]
    else:
        current_topics_list = [t.strip() for t in current_topics.split(",")]

    target_app_date = input("What is your expected PhD application deadline? (YYYY-MM-DD) [2027-01-01]: ").strip() or "2027-01-01"
    provider = input("Email provider (resend, brevo, smtp, console) [resend]: ").strip() or "resend"

    # Update profile.yaml
    profile_data = {
        "phd_target": {
            "field": "Edge Computing",
            "related_fields": ["Edge Intelligence", "Edge AI", "Distributed Systems", "IoT", "5G/6G"],
            "target_application_period": target_app_date
        },
        "learning_stage": {
            "current_level": 3,
            "current_topics": current_topics_list,
            "stage_boost_multiplier": 1.25
        },
        "research_interests": interests_list,
        "location": {
            "country": "Nigeria",
            "preferred_study_regions": ["Global", "Europe", "North America", "Asia"]
        },
        "email_preferences": {
            "provider": provider,
            "sender_email": "research-alert@resend.dev",
            "recipient_email": email,
            "daily_digest": True,
            "weekly_digest": True,
            "urgent_alerts": True
        },
        "alert_thresholds": {
            "minimum_score": 6.5,
            "daily_digest_min_score": 7.5,
            "weekly_digest_min_score": 6.8,
            "urgent_alert_min_score": 9.0,
            "daily_limit": 10,
            "weekly_limit": 20
        },
        "ai_summarization": {
            "enabled": False,
            "provider": "gemini",
            "api_key_env": "LLM_API_KEY",
            "model": "gemini-1.5-flash"
        }
    }

    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(profile_data, f, sort_keys=False)

    print(f"\n✅ Configuration saved successfully to {profile_path}!")
    print("\nTo send live emails, ensure the following GitHub Secret is set:")
    if provider == "resend":
        print("  • RESEND_API_KEY (from https://resend.com)")
    elif provider == "brevo":
        print("  • BREVO_API_KEY (from https://brevo.com)")
    elif provider == "smtp":
        print("  • SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD")
    print("  • EMAIL_RECIPIENT (your email)")
    print("\nYou can test the setup immediately with:")
    print("  python -m src.cli run --mode daily --dry-run\n")


def list_phd_opportunities(args):
    """Lists discovered PhD opportunities with optional filters."""
    from src.storage.state_manager import StateManager
    from src.collectors.lab_recruitment import LabRecruitmentCollector
    from src.collectors.opportunities import OpportunityCollector

    state_mgr = StateManager()
    opps = state_mgr.load_opportunities()
    if not opps:
        # Collect dynamically if storage empty
        collector = LabRecruitmentCollector()
        items = collector.collect()
        opps = [i.opportunity_data for i in items if i.opportunity_data]

    # Filters
    filtered = opps
    if args.country:
        filtered = [o for o in filtered if args.country.lower() in (o.get("country") or "").lower()]
    if args.actively_recruiting:
        filtered = [o for o in filtered if o.get("recruitment_status") == "actively_recruiting"]
    if args.fully_funded:
        filtered = [o for o in filtered if o.get("funding_status") == "fully_funded"]
    if args.family_supported:
        filtered = [o for o in filtered if o.get("dependant_support") == "financially_supported"]

    print("\n" + "=" * 75)
    print(f" 🎓 PhD & LAB OPPORTUNITIES ({len(filtered)} matching)")
    print("=" * 75)
    for idx, opp in enumerate(filtered, 1):
        rec = opp.get("recruitment_status", "unverified").upper()
        fund = opp.get("funding_status", "unspecified").upper()
        dep = opp.get("dependant_support", "unspecified").upper()
        fit = opp.get("fit_score", 7.0)

        print(f"{idx}. {opp.get('title')}")
        print(f"   Institution: {opp.get('university')} ({opp.get('country')}) | Fit: {fit}/10")
        if opp.get("supervisor"):
            print(f"   Supervisor:  {opp.get('supervisor')}")
        print(f"   Status:      [{rec}] | Funding: [{fund}] | Dependants: [{dep}]")
        if opp.get("direct_quote"):
            print(f"   Quote:       \"{opp.get('direct_quote')}\"")
        if opp.get("deadline"):
            print(f"   Deadline:    {opp.get('deadline')}")
        print(f"   Link:        {opp.get('link')}")
        print("-" * 75)
    print()


def list_researchers(args):
    """Lists monitored researchers and candidate supervisors."""
    from src.storage.state_manager import StateManager
    from src.summarization.supervisors import SupervisorTracker

    state_mgr = StateManager()
    watchlist = state_mgr.load_researcher_watchlist()
    registry = watchlist.get("researchers", {}) if isinstance(watchlist, dict) else {}
    if not registry:
        registry = state_mgr.load_supervisors()

    researchers = list(registry.values()) if isinstance(registry, dict) else registry
    if args.recruiting:
        researchers = [r for r in researchers if r.get("recruitment_status") == "actively_recruiting"]
    if args.country:
        researchers = [r for r in researchers if args.country.lower() in (r.get("country") or "").lower()]

    print("\n" + "=" * 75)
    print(f" 👤 MONITORED RESEARCHERS & SUPERVISORS ({len(researchers)} matching)")
    print("=" * 75)
    for idx, r in enumerate(researchers, 1):
        status = r.get("recruitment_status", "tracked").upper()
        pubs = r.get("publication_count", 0)
        score = r.get("composite_score") or r.get("average_relevance", 7.0)
        print(f"{idx}. {r.get('name')} — {r.get('institution')} ({r.get('country', 'International')})")
        print(f"   Status: [{status}] | Relevant Papers: {pubs} | Fit Score: {score}/10")
        if r.get("recruitment_quote"):
            print(f"   Quote:  \"{r.get('recruitment_quote')}\"")
        topics = r.get("research_topics") or r.get("topics", [])
        if topics:
            print(f"   Topics: {', '.join(topics[:4])}")
        if r.get("scholar_url"):
            print(f"   Scholar: {r.get('scholar_url')}")
        if r.get("lab_page"):
            print(f"   Lab URL: {r.get('lab_page')}")
        print("-" * 75)
    print()


def list_scholarships(args):
    """Lists curated international scholarships supporting dependants."""
    from src.collectors.scholarships import ScholarshipCollector

    collector = ScholarshipCollector()
    schols = collector.get_scholarships_list()

    if args.country:
        schols = [s for s in schols if args.country.lower() in s.country.lower()]
    if args.financially_supported:
        schols = [s for s in schols if s.dependant_support_classification in ["financially_supported", "excellent"]]

    print("\n" + "=" * 75)
    print(f" 💰 FAMILY-FRIENDLY SCHOLARSHIPS ({len(schols)} available)")
    print("=" * 75)
    for idx, s in enumerate(schols, 1):
        dep_status = "ALLOWANCE INCLUDED" if s.dependant_support_classification in ["financially_supported", "excellent"] else "PERMITTED ON VISA"
        print(f"{idx}. {s.name} ({s.country})")
        print(f"   Funding: Fully Funded | Family Support: [{dep_status}]")
        print(f"   Allowance: {s.dependant_support_details}")
        print(f"   Legal:     {s.notes}")
        print(f"   Deadline:  {s.deadline}")
        print(f"   Official:  {s.official_url}")
        print("-" * 75)
    print()


def test_phd_sources(args):
    """Tests PhD opportunities, lab recruitment, and scholarship collectors."""
    from src.collectors.lab_recruitment import LabRecruitmentCollector
    from src.collectors.scholarships import ScholarshipCollector
    from src.collectors.opportunities import OpportunityCollector

    print("\nTesting PhD intelligence sources...\n")
    collectors = [
        LabRecruitmentCollector(name="University Lab PhD Opportunities"),
        ScholarshipCollector(name="Curated International Scholarships"),
        OpportunityCollector(name="Institutional PhD Opportunities")
    ]

    print(f"{'Source Name':<40} | {'Status':<10} | {'Items'}")
    print("-" * 65)
    for col in collectors:
        items = col.collect()
        status = col.last_status
        print(f"{col.name:<40} | {status:<10} | {len(items)}")
    print("\nPhD source connectivity verification complete.\n")


def debug_opportunity_score(args):
    """Debugs the scoring and classification for a PhD opportunity."""
    from src.ranking.opportunity_scorer import OpportunityScorer
    from src.models import PhDOpportunity

    scorer = OpportunityScorer()
    opp = PhDOpportunity(
        title=args.title,
        university=args.university or "Technical University",
        department=args.department or "Department of Computer Science",
        country=args.country or "Germany",
        eligibility=args.description or "",
        research_areas=["Edge Computing", "Distributed Systems"]
    )

    full_text = f"{args.title} {args.description or ''} {args.quote or ''}"
    if args.quote:
        status, snippet = scorer.classify_recruitment_status(args.quote)
        opp.recruitment_status = status
        opp.recruitment_evidence = snippet
    else:
        status, snippet = scorer.classify_recruitment_status(full_text)
        opp.recruitment_status = status
        opp.recruitment_evidence = snippet

    fund_status, _ = scorer.classify_funding_status(full_text)
    opp.funding_status = fund_status

    dep_status, dep_info = scorer.classify_dependant_support(opp.country, full_text)
    opp.dependant_support_classification = dep_status
    opp.dependant_support_info = dep_info

    opp = scorer.score_opportunity(opp)

    print("\n" + "=" * 65)
    print(" 🎓 PhD OPPORTUNITY SCORING & CLASSIFICATION DEBUGGER")
    print("=" * 65)
    print(f"Title:        {opp.title}")
    print(f"University:   {opp.university} ({opp.country})")
    print(f"Recruitment:  {opp.recruitment_status.upper()}")
    print(f"Funding:      {opp.funding_status.upper()}")
    print(f"Dependants:   {opp.dependant_support_classification.upper()}")
    if opp.recruitment_evidence:
        print(f"Evidence:     \"{opp.recruitment_evidence}\"")
    print("-" * 65)
    print(f"Research Fit Score (35%):     {opp.relevance_score:>5.2f} / 10.0")
    print(f"Recruitment Status (20%):     {opp.supervisor_fit_score:>5.2f} / 10.0")
    print(f"Funding Security (20%):       {opp.funding_score:>5.2f} / 10.0")
    print(f"Dependant Feasibility (15%):  {opp.dependant_support_score:>5.2f} / 10.0")
    print(f"Country Target Score (10%):   {opp.country_score:>5.2f} / 10.0")
    print("-" * 65)
    print(f"TOTAL COMPOSITE FIT SCORE:    {opp.composite_score:>5.1f} / 10.0")
    print("\nTRANSPARENT RATIONALE:")
    for r in opp.reasons:
        print(f"  {r}")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Edge Computing PhD Research Intelligence Assistant CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run the discovery and alert pipeline")
    run_parser.add_argument("--mode", choices=["daily", "weekly", "urgent"], default="daily", help="Pipeline execution mode")
    run_parser.add_argument("--dry-run", action="store_true", help="Execute without sending live emails or modifying permanent state")

    # Command: test-sources
    subparsers.add_parser("test-sources", help="Test connectivity and status of all configured feeds & APIs")

    # Command: debug-score
    debug_parser = subparsers.add_parser("debug-score", help="Debug scoring for an academic item (Why didn't I receive this?)")
    debug_parser.add_argument("--title", required=True, help="Title of the paper or event")
    debug_parser.add_argument("--abstract", default="", help="Abstract or summary")
    debug_parser.add_argument("--source", default="IEEE Transactions", help="Publication source")
    debug_parser.add_argument("--tier", choices=["TIER1_ACADEMIC_STANDARDS", "TIER2_UNIVERSITY_LAB", "TIER3_CONFERENCE", "TIER4_INDUSTRY"], default="TIER1_ACADEMIC_STANDARDS")
    debug_parser.add_argument("--url", default="", help="Item URL")
    debug_parser.add_argument("--date", default="", help="Publication date (YYYY-MM-DD)")

    # Command: setup
    subparsers.add_parser("setup", help="Interactive initial configuration wizard")

    # Command: generate-dashboard
    subparsers.add_parser("generate-dashboard", help="Regenerate GitHub Pages docs/data.json")

    # Command: phd-opportunities
    opp_parser = subparsers.add_parser("phd-opportunities", help="List discovered PhD opportunities")
    opp_parser.add_argument("--country", default="", help="Filter by country name")
    opp_parser.add_argument("--actively-recruiting", action="store_true", help="Filter by actively recruiting only")
    opp_parser.add_argument("--fully-funded", action="store_true", help="Filter by fully funded only")
    opp_parser.add_argument("--family-supported", action="store_true", help="Filter by financially supported dependants")

    # Command: researchers
    res_parser = subparsers.add_parser("researchers", help="List monitored researchers and potential supervisors")
    res_parser.add_argument("--country", default="", help="Filter by country")
    res_parser.add_argument("--recruiting", action="store_true", help="Filter by actively recruiting only")

    # Command: scholarships
    schol_parser = subparsers.add_parser("scholarships", help="List curated family-friendly scholarships")
    schol_parser.add_argument("--country", default="", help="Filter by country")
    schol_parser.add_argument("--financially-supported", action="store_true", help="Filter by dedicated allowance only")

    # Command: test-phd-sources
    subparsers.add_parser("test-phd-sources", help="Test PhD opportunities and scholarship discovery sources")

    # Command: debug-opportunity-score
    dopp_parser = subparsers.add_parser("debug-opportunity-score", help="Debug opportunity scoring and classification")
    dopp_parser.add_argument("--title", required=True, help="Title of PhD opportunity")
    dopp_parser.add_argument("--university", default="", help="University name")
    dopp_parser.add_argument("--department", default="", help="Department")
    dopp_parser.add_argument("--country", default="Germany", help="Target country")
    dopp_parser.add_argument("--description", default="", help="Posting description")
    dopp_parser.add_argument("--quote", default=None, help="Direct recruitment quote snippet")

    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(args)
    elif args.command == "test-sources":
        test_sources(args)
    elif args.command == "debug-score":
        debug_score(args)
    elif args.command == "setup":
        interactive_setup(args)
    elif args.command == "generate-dashboard":
        generate_dashboard_cli(args)
    elif args.command == "phd-opportunities":
        list_phd_opportunities(args)
    elif args.command == "researchers":
        list_researchers(args)
    elif args.command == "scholarships":
        list_scholarships(args)
    elif args.command == "test-phd-sources":
        test_phd_sources(args)
    elif args.command == "debug-opportunity-score":
        debug_opportunity_score(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
