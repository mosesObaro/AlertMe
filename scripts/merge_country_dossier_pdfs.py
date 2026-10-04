#!/usr/bin/env python3
"""Merge professor and country dossier PDFs under reports/supervisors/<country>/ into reports/<country>.pdf."""

import os
import sys
from pathlib import Path
from pypdf import PdfWriter

REPO_ROOT = Path(__file__).resolve().parent.parent
SUPERVISORS_DIR = REPO_ROOT / "reports" / "supervisors"
REPORTS_DIR = REPO_ROOT / "reports"


def merge_country_pdfs():
    if not SUPERVISORS_DIR.exists():
        print(f"ERROR: Supervisors directory not found at {SUPERVISORS_DIR}", file=sys.stderr)
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Discover country directories (subdirectories under reports/supervisors/)
    country_dirs = [d for d in SUPERVISORS_DIR.iterdir() if d.is_dir()]
    if not country_dirs:
        print(f"ERROR: No country directories found in {SUPERVISORS_DIR}", file=sys.stderr)
        sys.exit(1)

    # Sort country dirs for deterministic iteration
    country_dirs.sort(key=lambda d: d.name)

    print(f"Found {len(country_dirs)} country directories: {[d.name for d in country_dirs]}")

    failure_occurred = False
    merged_count = 0

    for country_dir in country_dirs:
        country_name = country_dir.name
        # Collect all .pdf files recursively within country folder
        pdf_files = [p for p in country_dir.rglob("*.pdf") if p.is_file()]

        if not pdf_files:
            print(f"ERROR: Country '{country_name}' contains no PDF files in {country_dir}", file=sys.stderr)
            failure_occurred = True
            continue

        # Sort deterministically by relative path within the country folder
        pdf_files.sort(key=lambda p: str(p.relative_to(country_dir)).lower())

        output_pdf_path = REPORTS_DIR / f"{country_name}.pdf"
        print(f"\nMerging {len(pdf_files)} PDFs for country '{country_name}' into {output_pdf_path.relative_to(REPO_ROOT)}:")
        for pdf_file in pdf_files:
            print(f"  - {pdf_file.relative_to(country_dir)}")

        writer = PdfWriter()
        try:
            for pdf_file in pdf_files:
                writer.append(str(pdf_file))
            writer.write(str(output_pdf_path))
            writer.close()
            print(f"SUCCESS: Generated {output_pdf_path.name} ({os.path.getsize(output_pdf_path)} bytes)")
            merged_count += 1
        except Exception as e:
            print(f"ERROR: Failed merging PDFs for country '{country_name}': {e}", file=sys.stderr)
            failure_occurred = True

    if failure_occurred:
        print("\nERROR: PDF merging failed for one or more countries.", file=sys.stderr)
        sys.exit(1)

    print(f"\nSuccessfully generated {merged_count} country PDF report(s) in {REPORTS_DIR.relative_to(REPO_ROOT)}.")


if __name__ == "__main__":
    merge_country_pdfs()
