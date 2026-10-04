#!/usr/bin/env python3
"""Audit script for research links, references, and evidence bundles in AlertMe.

Scans docs/data/research_gap_data.json and reports/research_statements/*.md to report:
1. Link breakdown by cause (doi_hash, bad_prefix, doi_not_registered, landing_404, blocked, missing, valid)
2. References count per statement
3. Evidence bundle size vs corpus size
"""

import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DATA_JSON = REPO_ROOT / "docs" / "data" / "research_gap_data.json"
REPORTS_STATEMENTS_DIR = REPO_ROOT / "reports" / "research_statements"

DOI_HANDLE_API = "https://doi.org/api/handles/"


def normalize_doi_candidate(raw: str) -> Tuple[str, str]:
    """Extracts clean DOI or identifies malformed/doi_hash patterns."""
    if not raw:
        return "", "missing"

    s = str(raw).strip()

    # Check for internal non-DOI IDs like doi_<hash> or paper_<hash>
    if re.search(r"doi_[a-f0-9]{8,}", s, re.IGNORECASE) or re.search(r"paper_[a-f0-9]{8,}", s, re.IGNORECASE):
        return s, "doi_hash"

    # Check for double/bad prefixes
    if s.count("doi.org") > 1 or s.count("http") > 1 or s.startswith("doi:10.") or s.startswith("https://doi.org/doi:"):
        return s, "bad_prefix"

    # Clean standard DOI prefixes
    clean = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", s, flags=re.IGNORECASE).strip()
    clean = clean.rstrip(".,;)")

    # Validate against DOI regex
    if re.match(r"^10\.\d{4,9}/\S+$", clean):
        return clean, "doi_candidate"

    if s.startswith("http://") or s.startswith("https://"):
        return s, "url_candidate"

    return s, "missing"


def check_doi_registration(doi: str) -> str:
    """Queries DOI REST API (GET https://doi.org/api/handles/<doi>)."""
    try:
        quoted = urllib.parse.quote(doi, safe="/")
        resp = requests.get(f"{DOI_HANDLE_API}{quoted}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            code = data.get("responseCode")
            if code == 1:
                return "valid"
            elif code == 100:
                return "doi_not_registered"
            else:
                return "doi_not_registered"
        elif resp.status_code in (403, 429, 999):
            return "blocked"
        elif resp.status_code == 404:
            return "doi_not_registered"
    except Exception:
        pass
    return "blocked"


def check_url_status(url: str) -> str:
    """Checks non-DOI URL HTTP status."""
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True)
        if resp.status_code in (200, 301, 302, 307, 308):
            return "valid"
        elif resp.status_code in (403, 429, 999):
            return "blocked"
        elif resp.status_code == 404:
            return "landing_404"
    except Exception:
        pass
    return "blocked"


def audit_links_and_bundles():
    print("=" * 70)
    print(" ALERTME RESEARCH LINK & STATEMENT AUDIT REPORT")
    print("=" * 70)

    # 1. Audit docs/data/research_gap_data.json
    link_counts: Dict[str, int] = {
        "doi_hash": 0,
        "bad_prefix": 0,
        "doi_not_registered": 0,
        "landing_404": 0,
        "blocked": 0,
        "missing": 0,
        "valid": 0,
    }

    evidence_bundle_sizes: List[Tuple[str, int, int]] = []  # (name/id, bundle_size, corpus_size)
    statement_ref_counts: Dict[str, int] = {}

    if DOCS_DATA_JSON.exists():
        try:
            with open(DOCS_DATA_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)

            professors = data.get("professors", [])
            for prof in professors:
                p_name = prof.get("professor_name", "Unknown")
                papers = prof.get("papers", [])
                corpus_size = len(papers)

                for pap in papers:
                    doi_raw = pap.get("doi")
                    url_raw = pap.get("url") or pap.get("link")

                    val, category = normalize_doi_candidate(doi_raw or url_raw)
                    if category == "doi_candidate":
                        status = check_doi_registration(val)
                        link_counts[status] += 1
                    elif category == "url_candidate":
                        status = check_url_status(val)
                        link_counts[status] += 1
                    elif category in link_counts:
                        link_counts[category] += 1

                stmts = prof.get("research_statements", {})
                for prob_id, stmt_obj in stmts.items():
                    refs = stmt_obj.get("references", [])
                    statement_ref_counts[prob_id] = len(refs)

                    # Bundle size tracking if bundles present
                    bundle = stmt_obj.get("evidence_bundle", []) or prof.get("evidence_bundles", {}).get(prob_id, [])
                    bundle_size = len(bundle)
                    evidence_bundle_sizes.append((f"{p_name} ({prob_id})", bundle_size, corpus_size))

        except Exception as e:
            print(f"Error reading {DOCS_DATA_JSON}: {e}")
    else:
        print(f"Warning: {DOCS_DATA_JSON} does not exist.")

    # 2. Audit reports/research_statements/*.md files
    statement_files = list(REPORTS_STATEMENTS_DIR.glob("*.md")) if REPORTS_STATEMENTS_DIR.exists() else []
    for s_file in statement_files:
        content = s_file.read_text(encoding="utf-8")
        prob_id = s_file.stem
        # Count references in markdown
        ref_matches = re.findall(r"^\[\d+\]\s+", content, re.MULTILINE)
        statement_ref_counts[prob_id] = len(ref_matches)

        # Find DOIs / links in markdown content
        urls = re.findall(r"https?://\S+", content)
        for u in urls:
            val, category = normalize_doi_candidate(u)
            if category == "doi_hash":
                link_counts["doi_hash"] += 1
            elif category == "bad_prefix":
                link_counts["bad_prefix"] += 1

    print("\n--- 1. LINK BREAKDOWN BY CAUSE ---")
    for cause, count in link_counts.items():
        print(f"  * {cause:<20}: {count:>5}")

    print("\n--- 2. REFERENCES PER RESEARCH STATEMENT ---")
    if statement_ref_counts:
        for pid, ref_c in statement_ref_counts.items():
            print(f"  * Statement {pid:<25}: {ref_c:>3} references")
    else:
        print("  * No statements found.")

    print("\n--- 3. EVIDENCE BUNDLE SIZE VS CORPUS SIZE ---")
    if evidence_bundle_sizes:
        for label, b_size, c_size in evidence_bundle_sizes:
            print(f"  * {label:<35}: Bundle Size = {b_size:>3}, Corpus Size = {c_size:>3}")
    else:
        print("  * Bundle tracking: 0 pre-computed evidence bundles present.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    audit_links_and_bundles()
