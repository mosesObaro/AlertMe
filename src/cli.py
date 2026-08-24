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


def generate_dashboard_cli(args):
    """Regenerates docs/data.json from current stored state."""
    pipeline = ResearchPipeline()
    history = pipeline.state_manager.load_alert_history()
    trends = pipeline.state_manager.load_trends()
    supervisors = pipeline.state_manager.load_supervisors()
    top_sups = pipeline.supervisor_tracker.get_top_supervisors_to_watch(supervisors)
    pipeline.dashboard_gen.generate_dashboard_data([], trends, top_sups)
    print("✅ Dashboard static data regenerated in docs/data.json.")


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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
