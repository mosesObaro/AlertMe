"""
Command-Line Interface (CLI) for the Hong Kong PhD Supervisor Intelligence module.
Provides commands for supervisor discovery, recruitment verification, scholarship tracking,
daily briefing generation, and comprehensive reporting.
"""

import sys
import os
import argparse
from datetime import date
from .storage import StorageManager
from .campaign import CampaignManager
from .alerts import AlertGenerator
from .discovery import DiscoveryEngine
from .recruitment import RecruitmentEngine
from .scoring import ScoringEngine
from .config import TARGET_HONG_KONG_UNIVERSITIES

def cmd_discover_supervisors(args):
    """Lists vetted Edge Computing supervisors across the 8 target universities."""
    storage = StorageManager()
    researchers = list(storage.researchers.values())
    
    tier_filter = getattr(args, "tier", None)
    uni_filter = getattr(args, "university", None)
    
    if uni_filter:
        norm_uni = DiscoveryEngine.normalize_university_name(uni_filter)
        if norm_uni:
            researchers = [r for r in researchers if r.university == norm_uni]
        else:
            print(f"Error: '{uni_filter}' does not match any of the 8 target Hong Kong universities.")
            return

    if tier_filter:
        researchers = [r for r in researchers if r.priority_tier.lower() == tier_filter.lower()]

    tier_order = {"Tier 1": 1, "Tier 2": 2, "Tier 3": 3}
    researchers.sort(key=lambda r: (tier_order.get(r.priority_tier, 4), -r.alignment_score))

    print(f"\n{'='*85}")
    print(f"HONG KONG PhD SUPERVISOR DIRECTORY ({len(researchers)} Researchers Found)")
    print(f"{'='*85}")
    print(f"{'Name':<24} | {'University':<34} | {'Tier':<7} | {'Align%':<6} | {'Recruitment':<16}")
    print(f"{'-'*24}-+-{'-'*34}-+-{'-'*7}-+-{'-'*6}-+-{'-'*16}")

    for r in researchers:
        print(f"{r.name:<24} | {r.university:<34} | {r.priority_tier:<7} | {r.alignment_score:<5.1f}% | {r.recruitment.status:<16}")

    print(f"{'='*85}\n")

def cmd_verify_recruitment(args):
    """Verifies recruitment evidence, sources, dates, and checks for 12-month freshness."""
    storage = StorageManager()
    researchers = list(storage.researchers.values())
    today = date.today()

    print(f"\n{'='*95}")
    print("PhD RECRUITMENT STATUS & FRESHNESS VERIFICATION AUDIT")
    print(f"{'='*95}")
    print(f"{'Professor':<22} | {'Status':<20} | {'Source Date':<11} | {'Freshness':<12} | {'Source Type'}")
    print(f"{'-'*22}-+-{'-'*20}-+-{'-'*11}-+-{'-'*12}-+-{'-'*20}")

    confirmed_count = 0
    stale_count = 0

    for r in researchers:
        is_stale = storage.is_recruitment_stale(r.recruitment, today)
        freshness_label = "STALE (>12m)" if is_stale else "ACTIVE (<12m)"
        if is_stale:
            stale_count += 1
        if r.recruitment.status in ["CONFIRMED_ACTIVE", "STRONG_EVIDENCE"]:
            confirmed_count += 1

        print(f"{r.name:<22} | {r.recruitment.status:<20} | {r.recruitment.source_date:<11} | {freshness_label:<12} | {r.recruitment.source_type}")

    print(f"{'='*95}")
    print(f"Summary: {len(researchers)} researchers audited | {confirmed_count} active/strong recruitment | {stale_count} stale entries\n")

def cmd_update_scholarships(args):
    """Displays official Hong Kong PhD scholarships, stipends, and application deadlines."""
    storage = StorageManager()
    campaign = CampaignManager()
    time_info = campaign.get_time_remaining()

    print(f"\n{'='*95}")
    print(f"HONG KONG DOCTORAL SCHOLARSHIP SCHEMES ({time_info['days_remaining']} Days to Key Deadline: Dec 1)")
    print(f"{'='*95}")
    print(f"{'University':<28} | {'Scholarship Scheme':<30} | {'Annual Funding':<20} | {'Deadline'}")
    print(f"{'-'*28}-+-{'-'*30}-+-{'-'*20}-+-{'-'*15}")

    for s in storage.scholarships.values():
        print(f"{s.university:<28} | {s.scholarship_name[:30]:<30} | {s.funding_amount[:20]:<20} | {s.application_deadline[:10]}")

    print(f"{'='*95}\n")

def cmd_generate_alert(args):
    """Generates today's structured daily research intelligence briefing."""
    storage = StorageManager()
    campaign = CampaignManager()
    alert_gen = AlertGenerator(storage, campaign)
    
    alert = alert_gen.generate_daily_alert()
    if not alert:
        print("Error: Could not select a supervisor or generate alert.")
        return

    markdown_text = alert.to_markdown()
    print("\n" + markdown_text)

    # Save to alerts/daily/
    alerts_dir = os.path.join(os.getcwd(), "alerts", "daily")
    os.makedirs(alerts_dir, exist_ok=True)
    alert_file = os.path.join(alerts_dir, f"alert_{alert.alert_id}.md")
    with open(alert_file, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    print(f"[Saved daily briefing to: {alert_file}]\n")

def cmd_generate_report(args):
    """Generates a comprehensive Hong Kong PhD application intelligence report."""
    storage = StorageManager()
    campaign = CampaignManager()
    time_info = campaign.get_time_remaining()
    milestone_info = campaign.get_current_milestone()
    coverage = campaign.get_university_coverage_summary(
        list(storage.researchers.values()),
        list(storage.scholarships.values())
    )

    print(f"\n{'='*90}")
    print("HONG KONG PhD APPLICATION INTELLIGENCE REPORT — 8 TARGET UNIVERSITIES")
    print(f"{'='*90}")
    print(f"Campaign Phase: {milestone_info['milestone_info']['name']}")
    print(f"Timeline Status: {time_info['days_remaining']} days remaining ({time_info['weeks_remaining']} weeks)")
    print(f"Key Deadline: {time_info['target_deadline']}")
    print(f"Weekly Deliverable: {milestone_info['milestone_info']['deliverable']}")
    print(f"{'='*90}")
    print(f"\n[UNIVERSITY COVERAGE SUMMARY across 8 Target Institutions]")
    print(f"{'University':<42} | {'Researchers':<11} | {'Strong Fits':<11} | {'Scholarships':<12}")
    print(f"{'-'*42}-+-{'-'*11}-+-{'-'*11}-+-{'-'*12}")

    for c in coverage:
        print(f"{c['university']:<42} | {c['researchers_count']:<11} | {c['strong_matches_count']:<11} | {c['scholarships_count']:<12}")

    print(f"{'='*90}")
    print("\n[TOP-TIER HIGH-PRIORITY POTENTIAL SUPERVISORS]")
    tier1 = [r for r in storage.researchers.values() if r.priority_tier == "Tier 1"]
    for idx, r in enumerate(tier1, 1):
        print(f"{idx:2d}. {r.name} ({r.university})")
        print(f"    Department: {r.department}")
        print(f"    Research Focus: {', '.join(r.research_interests[:3])}")
        print(f"    Alignment Score: {r.alignment_score}% | Recruitment: {r.recruitment.status}")
        print(f"    Recruitment Evidence: {r.recruitment.evidence_text[:80]}...")
        print(f"    Mapped Curriculum: Weeks {', '.join(str(w) for w in r.relevant_curriculum_weeks[:4])}\n")

    print(f"{'='*90}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Hong Kong PhD Supervisor Intelligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # discover-hk-supervisors
    p_disc = subparsers.add_parser("discover-hk-supervisors", help="Discover vetted supervisors")
    p_disc.add_argument("--university", type=str, help="Filter by university (name or alias)")
    p_disc.add_argument("--tier", type=str, choices=["Tier 1", "Tier 2", "Tier 3"], help="Filter by priority tier")

    # verify-hk-recruitment
    subparsers.add_parser("verify-hk-recruitment", help="Verify recruitment evidence and freshness")

    # update-hk-scholarships
    subparsers.add_parser("update-hk-scholarships", help="Display scholarships and deadlines")

    # generate-hk-supervisor-alert
    subparsers.add_parser("generate-hk-supervisor-alert", help="Generate today's 7-day progressive daily briefing")

    # generate-hk-report
    subparsers.add_parser("generate-hk-report", help="Generate comprehensive 8-university intelligence report")

    # update-hk-supervisors
    subparsers.add_parser("update-hk-supervisors", help="Refresh supervisor database and state")

    args = parser.parse_args()

    if args.command == "discover-hk-supervisors":
        cmd_discover_supervisors(args)
    elif args.command == "verify-hk-recruitment":
        cmd_verify_recruitment(args)
    elif args.command == "update-hk-scholarships":
        cmd_update_scholarships(args)
    elif args.command == "generate-hk-supervisor-alert":
        cmd_generate_alert(args)
    elif args.command == "generate-hk-report":
        cmd_generate_report(args)
    elif args.command == "update-hk-supervisors":
        storage = StorageManager()
        storage.load_all()
        storage.save_state()
        print("Supervisor database state refreshed successfully.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
