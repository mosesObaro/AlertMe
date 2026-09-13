"""
Excel Extension Bridge for Hong Kong PhD Supervisor Intelligence.
Appends 3 new dedicated sheets (HK Supervisor Intelligence, HK Scholarships & Deadlines,
HK Application Tracker) and extends the master Dashboard without disturbing any existing sheets.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from typing import Optional, List
from datetime import date
from .storage import StorageManager
from .campaign import CampaignManager
from .models import ResearcherProfile, Scholarship

def add_hong_kong_module_sheets(
    wb: openpyxl.Workbook,
    storage: Optional[StorageManager] = None,
    reference_date: Optional[date] = None
):
    """
    Extends an existing workbook with the 3 Hong Kong PhD intelligence sheets
    and enriches the master Dashboard. Preserves all existing 11 sheets.
    """
    if storage is None:
        storage = StorageManager()
        
    campaign = CampaignManager()
    ref_date = reference_date or date.today()
    time_info = campaign.get_time_remaining(ref_date)

    # Styles
    NAVY_DARK = "1B365D"
    NAVY_MID = "2C4D75"
    NAVY_LIGHT = "E8EEF5"
    BORDER_LIGHT = "D0D7DE"
    BORDER_DARK = "8C9BAE"
    FILL_ZEBRA = "F7F9FC"
    FILL_WHITE = "FFFFFF"
    FILL_HEADER_ACCENT = "D9E2EC"
    FILL_HIGHLIGHT = "FFF8E7"

    font_title = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="E8EEF5")
    font_tbl_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=10, bold=True, color="1B365D")
    font_regular = Font(name="Calibri", size=10, color="24292F")
    font_small = Font(name="Calibri", size=9, color="57606A")
    font_hyperlink = Font(name="Calibri", size=10, color="0969DA", underline="single")
    font_kpi_num = Font(name="Calibri", size=16, bold=True, color="1B365D")
    font_kpi_label = Font(name="Calibri", size=9, bold=True, color="5A6B7C")

    fill_navy_dark = PatternFill(start_color=NAVY_DARK, end_color=NAVY_DARK, fill_type="solid")
    fill_navy_mid = PatternFill(start_color=NAVY_MID, end_color=NAVY_MID, fill_type="solid")
    fill_navy_light = PatternFill(start_color=NAVY_LIGHT, end_color=NAVY_LIGHT, fill_type="solid")
    fill_zebra = PatternFill(start_color=FILL_ZEBRA, end_color=FILL_ZEBRA, fill_type="solid")
    fill_white = PatternFill(start_color=FILL_WHITE, end_color=FILL_WHITE, fill_type="solid")
    fill_header_accent = PatternFill(start_color=FILL_HEADER_ACCENT, end_color=FILL_HEADER_ACCENT, fill_type="solid")
    fill_highlight = PatternFill(start_color=FILL_HIGHLIGHT, end_color=FILL_HIGHLIGHT, fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color=BORDER_LIGHT),
        right=Side(style='thin', color=BORDER_LIGHT),
        top=Side(style='thin', color=BORDER_LIGHT),
        bottom=Side(style='thin', color=BORDER_LIGHT)
    )
    header_border = Border(
        left=Side(style='thin', color=BORDER_DARK),
        right=Side(style='thin', color=BORDER_DARK),
        top=Side(style='medium', color=NAVY_DARK),
        bottom=Side(style='medium', color=NAVY_DARK)
    )

    align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left = Alignment(horizontal='left', vertical='center', wrap_text=True)
    align_right = Alignment(horizontal='right', vertical='center')

    # =========================================================================
    # SHEET 12: HK SUPERVISOR INTELLIGENCE
    # =========================================================================
    sheet_name_supervisors = "HK Supervisor Intelligence"
    if sheet_name_supervisors in wb.sheetnames:
        del wb[sheet_name_supervisors]
    ws_sup = wb.create_sheet(title=sheet_name_supervisors)
    ws_sup.views.sheetView[0].showGridLines = True

    ws_sup.merge_cells("A1:Q2")
    ws_sup["A1"] = "HONG KONG PhD SUPERVISOR INTELLIGENCE (8 TARGET UNIVERSITIES)"
    ws_sup["A1"].font = font_title
    ws_sup["A1"].fill = fill_navy_dark
    ws_sup["A1"].alignment = align_center

    sup_headers = [
        "University", "Professor", "Department", "Position", "Research Group",
        "Primary Research Focus", "Priority Tier", "Alignment Score (%)", "Recruitment Status",
        "Recruitment Evidence", "Seminal / Key Publication", "Recent Breakthrough Paper",
        "Active Projects / Grants", "Simulators & Testbeds", "Mapped Curriculum Weeks",
        "Official Profile URL", "Application Action / Status"
    ]

    for col_idx, h in enumerate(sup_headers, 1):
        cell = ws_sup.cell(row=3, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_center
        cell.border = header_border
    ws_sup.row_dimensions[3].height = 28

    researchers_list = list(storage.researchers.values())
    tier_order = {"Tier 1": 1, "Tier 2": 2, "Tier 3": 3}
    researchers_list.sort(key=lambda r: (tier_order.get(r.priority_tier, 4), -r.alignment_score))

    for idx, r in enumerate(researchers_list, 4):
        ws_sup.cell(row=idx, column=1, value=r.university).alignment = align_left
        ws_sup.cell(row=idx, column=2, value=r.name).alignment = align_left
        ws_sup.cell(row=idx, column=2).font = font_bold
        ws_sup.cell(row=idx, column=3, value=r.department).alignment = align_left
        ws_sup.cell(row=idx, column=4, value=r.position).alignment = align_left
        ws_sup.cell(row=idx, column=5, value=r.research_group).alignment = align_left
        ws_sup.cell(row=idx, column=6, value=", ".join(r.research_interests[:3])).alignment = align_left
        
        tier_cell = ws_sup.cell(row=idx, column=7, value=r.priority_tier)
        tier_cell.alignment = align_center
        tier_cell.font = font_bold
        
        score_cell = ws_sup.cell(row=idx, column=8, value=r.alignment_score)
        score_cell.alignment = align_right
        score_cell.font = font_bold
        score_cell.number_format = "0.0\"%\""
        
        status_cell = ws_sup.cell(row=idx, column=9, value=r.recruitment.status)
        status_cell.alignment = align_center
        status_cell.font = font_bold
        
        ws_sup.cell(row=idx, column=10, value=f"{r.recruitment.evidence_text} ({r.recruitment.source_date})").alignment = align_left
        
        seminal_title = next((p.title for p in r.publications if getattr(p, "is_seminal", False)), r.publications[0].title if r.publications else "N/A")
        recent_title = next((p.title for p in r.publications if getattr(p, "is_recent", False)), r.publications[-1].title if r.publications else "N/A")
        
        ws_sup.cell(row=idx, column=11, value=seminal_title).alignment = align_left
        ws_sup.cell(row=idx, column=12, value=recent_title).alignment = align_left
        ws_sup.cell(row=idx, column=13, value="; ".join(r.current_projects[:2])).alignment = align_left
        ws_sup.cell(row=idx, column=14, value=", ".join(r.simulation_tools + r.systems_testbeds[:1])).alignment = align_left
        
        weeks_str = f"Weeks {', '.join(str(w) for w in r.relevant_curriculum_weeks[:4])}"
        ws_sup.cell(row=idx, column=15, value=weeks_str).alignment = align_center
        
        url_cell = ws_sup.cell(row=idx, column=16, value=r.official_profile_url)
        url_cell.hyperlink = r.official_profile_url
        url_cell.font = font_hyperlink
        url_cell.alignment = align_left
        
        ws_sup.cell(row=idx, column=17, value="Identified — Ready for Outreach").alignment = align_center

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 18):
            cell = ws_sup.cell(row=idx, column=c)
            if c != 2 and c != 7 and c != 8 and c != 9 and c != 16:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    sup_widths = {
        1: 28, 2: 24, 3: 26, 4: 28, 5: 28, 6: 30, 7: 14, 8: 16, 9: 22,
        10: 45, 11: 35, 12: 35, 13: 38, 14: 28, 15: 18, 16: 32, 17: 25
    }
    for col, width in sup_widths.items():
        ws_sup.column_dimensions[get_column_letter(col)].width = width
    ws_sup.freeze_panes = "C4"

    # =========================================================================
    # SHEET 13: HK SCHOLARSHIPS & DEADLINES
    # =========================================================================
    sheet_name_scholarships = "HK Scholarships & Deadlines"
    if sheet_name_scholarships in wb.sheetnames:
        del wb[sheet_name_scholarships]
    ws_sch = wb.create_sheet(title=sheet_name_scholarships)
    ws_sch.views.sheetView[0].showGridLines = True

    ws_sch.merge_cells("A1:M2")
    ws_sch["A1"] = "HONG KONG PhD SCHOLARSHIPS & DOCTORAL FUNDING SCHEMES"
    ws_sch["A1"].font = font_title
    ws_sch["A1"].fill = fill_navy_dark
    ws_sch["A1"].alignment = align_center

    sch_headers = [
        "University", "Scholarship Scheme Name", "Target PhD Program", "Application Deadline",
        "Days Remaining", "Annual Funding (HKD)", "Monthly Living Allowance", "Tuition Coverage",
        "Duration", "Dependent Support", "Supervisor Requirement", "Official Portal URL", "Verification Source"
    ]

    for col_idx, h in enumerate(sch_headers, 1):
        cell = ws_sch.cell(row=3, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_center
        cell.border = header_border
    ws_sch.row_dimensions[3].height = 28

    scholarships_list = list(storage.scholarships.values())

    for idx, s in enumerate(scholarships_list, 4):
        ws_sch.cell(row=idx, column=1, value=s.university).alignment = align_left
        ws_sch.cell(row=idx, column=2, value=s.scholarship_name).alignment = align_left
        ws_sch.cell(row=idx, column=2).font = font_bold
        ws_sch.cell(row=idx, column=3, value=s.phd_program).alignment = align_left
        ws_sch.cell(row=idx, column=4, value=s.application_deadline).alignment = align_center
        
        days_rem_cell = ws_sch.cell(row=idx, column=5, value=f"{time_info['days_remaining']} days")
        days_rem_cell.alignment = align_center
        days_rem_cell.font = font_bold
        
        ws_sch.cell(row=idx, column=6, value=s.funding_amount).alignment = align_center
        ws_sch.cell(row=idx, column=7, value=s.living_allowance).alignment = align_center
        ws_sch.cell(row=idx, column=8, value=s.tuition_coverage).alignment = align_left
        ws_sch.cell(row=idx, column=9, value=s.duration).alignment = align_center
        ws_sch.cell(row=idx, column=10, value=s.dependent_support).alignment = align_left
        ws_sch.cell(row=idx, column=11, value=s.supervisor_requirement).alignment = align_left
        
        url_cell = ws_sch.cell(row=idx, column=12, value=s.official_url)
        url_cell.hyperlink = s.official_url
        url_cell.font = font_hyperlink
        url_cell.alignment = align_left
        
        ws_sch.cell(row=idx, column=13, value=s.source).alignment = align_left

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 14):
            cell = ws_sch.cell(row=idx, column=c)
            if c != 2 and c != 5 and c != 12:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    sch_widths = {
        1: 28, 2: 34, 3: 32, 4: 25, 5: 16, 6: 25, 7: 25,
        8: 30, 9: 18, 10: 32, 11: 35, 12: 35, 13: 28
    }
    for col, width in sch_widths.items():
        ws_sch.column_dimensions[get_column_letter(col)].width = width
    ws_sch.freeze_panes = "C4"

    # =========================================================================
    # SHEET 14: HK APPLICATION TRACKER (10-WEEK CAMPAIGN OVERLAY)
    # =========================================================================
    sheet_name_campaign = "HK Application Tracker"
    if sheet_name_campaign in wb.sheetnames:
        del wb[sheet_name_campaign]
    ws_camp = wb.create_sheet(title=sheet_name_campaign)
    ws_camp.views.sheetView[0].showGridLines = True

    ws_camp.merge_cells("A1:K2")
    ws_camp["A1"] = "10-WEEK HONG KONG PhD APPLICATION CAMPAIGN ROADMAP"
    ws_camp["A1"].font = font_title
    ws_camp["A1"].fill = fill_navy_dark
    ws_camp["A1"].alignment = align_center

    camp_headers = [
        "Campaign Week", "Phase", "Target Date Window", "Milestone Goal", "Tangible Deliverable",
        "Target Universities", "Key Tasks / Action Items", "Priority Action", "Completion Criteria",
        "Status", "Notes & Reflection"
    ]

    for col_idx, h in enumerate(camp_headers, 1):
        cell = ws_camp.cell(row=3, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_center
        cell.border = header_border
    ws_camp.row_dimensions[3].height = 28

    from .config import CAMPAIGN_MILESTONES
    for w in range(1, 11):
        idx = w + 3
        m = CAMPAIGN_MILESTONES.get(w, {})
        
        ws_camp.cell(row=idx, column=1, value=f"Week {w}").alignment = align_center
        ws_camp.cell(row=idx, column=1).font = font_bold
        ws_camp.cell(row=idx, column=2, value=m.get("phase", "General")).alignment = align_center
        ws_camp.cell(row=idx, column=3, value=f"T minus {11 - w} Weeks").alignment = align_center
        ws_camp.cell(row=idx, column=4, value=m.get("name", "")).alignment = align_left
        ws_camp.cell(row=idx, column=5, value=m.get("deliverable", "")).alignment = align_left
        ws_camp.cell(row=idx, column=5).fill = fill_highlight
        ws_camp.cell(row=idx, column=6, value="All 8 Universities" if w <= 2 else "Top 3-4 Target Institutions").alignment = align_left
        ws_camp.cell(row=idx, column=7, value=m.get("description", "")).alignment = align_left
        ws_camp.cell(row=idx, column=8, value="Focus on Supervisor Discovery" if w == 1 else ("Outreach Preparation" if w in [5,6] else "Application Submission")).alignment = align_left
        ws_camp.cell(row=idx, column=9, value="Deliverable produced and reviewed").alignment = align_left
        
        status = "In Progress" if w == time_info["current_campaign_week"] else ("Completed" if w < time_info["current_campaign_week"] else "Not Started")
        status_cell = ws_camp.cell(row=idx, column=10, value=status)
        status_cell.alignment = align_center
        status_cell.font = font_bold
        
        ws_camp.cell(row=idx, column=11, value="").alignment = align_left

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 12):
            cell = ws_camp.cell(row=idx, column=c)
            if c != 1 and c != 10:
                cell.font = font_regular
            if c != 5:
                cell.fill = row_fill
            cell.border = thin_border

    camp_widths = {
        1: 15, 2: 18, 3: 18, 4: 32, 5: 35, 6: 25, 7: 42, 8: 28, 9: 28, 10: 16, 11: 30
    }
    for col, width in camp_widths.items():
        ws_camp.column_dimensions[get_column_letter(col)].width = width
    ws_camp.freeze_panes = "D4"

    # =========================================================================
    # ENRICH EXISTING DASHBOARD SHEET (Add HK PhD Summary Card at the bottom)
    # =========================================================================
    if "Dashboard" in wb.sheetnames:
        ws_dash = wb["Dashboard"]
        # Add new Section Header at row 30 (below navigation directory)
        header_cell = ws_dash["A30"]
        header_cell.value = "HONG KONG PhD CAMPAIGN (10-WEEK APPLICATION OVERLAY)"
        header_cell.font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
        header_cell.fill = fill_navy_mid
        header_cell.alignment = Alignment(horizontal='left', vertical='center')
        ws_dash.merge_cells("A30:M30")

        # KPI Summary Cards row 31-33
        dash_cards = [
            ("TARGET UNIVERSITIES", "8 Universities", "A31", "A31:B31", "A32", "A32:B33"),
            ("POTENTIAL SUPERVISORS", f"{len(storage.researchers)} Discovered", "C31", "C31:D31", "C32", "C32:D33"),
            ("TIER 1 MATCHES", f"{sum(1 for r in storage.researchers.values() if r.priority_tier == 'Tier 1')} Supervisors", "E31", "E31:F31", "E32", "E32:F33"),
            ("ACTIVE RECRUITING", f"{sum(1 for r in storage.researchers.values() if r.recruitment.status in ['CONFIRMED_ACTIVE', 'STRONG_EVIDENCE'])} Verified", "G31", "G31:H31", "G32", "G32:H33"),
            ("WEEKS REMAINING", f"{time_info['weeks_remaining']} Weeks", "I31", "I31:J31", "I32", "I32:J33"),
            ("NEAREST DEADLINE", f"{time_info['days_remaining']} Days (Dec 1)", "K31", "K31:M31", "K32", "K32:M33")
        ]

        for label, val, top_cell_ref, top_range, val_cell_ref, val_range in dash_cards:
            top_cell = ws_dash[top_cell_ref]
            top_cell.value = label
            top_cell.font = font_kpi_label
            top_cell.fill = fill_navy_light
            top_cell.alignment = align_center
            ws_dash.merge_cells(top_range)

            val_cell = ws_dash[val_cell_ref]
            val_cell.value = val
            val_cell.font = font_kpi_num
            val_cell.fill = fill_white
            val_cell.alignment = align_center
            ws_dash.merge_cells(val_range)

        for r in range(31, 34):
            for c in range(1, 14):
                ws_dash.cell(row=r, column=c).border = thin_border

    print("Hong Kong PhD Supervisor Intelligence sheets successfully added to workbook.")
