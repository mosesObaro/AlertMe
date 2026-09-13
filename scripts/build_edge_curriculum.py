"""
Build Comprehensive Edge Computing Learning Program & Weekly Progress Tracker (.xlsx)
Strictly Free Open-Access Edition: 100% Free OpenCourseWare, MIT/Stanford Materials, YouTube Lecture Series,
Free Audit MOOCs, arXiv Preprints, Open Standards, and Open-Source Repositories.
Zero Paywalls. Zero Subscription Requirements.
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule

def create_edge_computing_workbook(output_filename="Edge_Computing_PhD_Curriculum_Tracker.xlsx", enable_hk_module=True):
    wb = openpyxl.Workbook()
    default_sheet = wb.active
    
    # -------------------------------------------------------------
    # STYLES & COLOR PALETTE (Classic Professional Navy / Slate / Emerald)
    # -------------------------------------------------------------
    NAVY_DARK = "1B365D"       # Main headers
    NAVY_MID = "2C4D75"        # Subheaders / Section headers
    NAVY_LIGHT = "E8EEF5"      # Light table header / highlight
    NAVY_ACCENT = "0F2537"     # Title text
    
    SLATE_GRAY = "5A6B7C"      # Subtle text / borders
    BORDER_LIGHT = "D0D7DE"    # Light grid borders
    BORDER_DARK = "8C9BAE"     # Header borders
    
    FILL_ZEBRA = "F7F9FC"       # Alternating row fill
    FILL_WHITE = "FFFFFF"
    FILL_HIGHLIGHT = "FFF8E7"   # Warm accent for callouts / deliverables
    FILL_HEADER_ACCENT = "D9E2EC"
    
    # Status Fills
    FILL_GREEN = "D4EDDA"      # Completed / High / Yes
    FONT_GREEN = "155724"
    FILL_YELLOW = "FFF3CD"     # In Progress / Medium / Partially
    FONT_YELLOW = "856404"
    FILL_BLUE = "D1ECF1"       # In Progress / Investigating
    FONT_BLUE = "0C5460"
    FILL_RED = "F8D7DA"        # Not Started / Low / No / Gap
    FONT_RED = "721C24"
    FILL_GRAY = "E2E3E5"       # Skipped / Reference
    FONT_GRAY = "383D41"
    
    # Fonts
    font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    font_subtitle = Font(name="Calibri", size=11, italic=True, color="E8EEF5")
    font_sec_header = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    font_tbl_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=10, bold=True, color="1B365D")
    font_regular = Font(name="Calibri", size=10, color="24292F")
    font_small = Font(name="Calibri", size=9, color="57606A")
    font_italic = Font(name="Calibri", size=9, italic=True, color="57606A")
    font_kpi_num = Font(name="Calibri", size=18, bold=True, color="1B365D")
    font_kpi_label = Font(name="Calibri", size=9, bold=True, color="5A6B7C")
    font_hyperlink = Font(name="Calibri", size=10, color="0969DA", underline="single")
    
    # Fills
    fill_navy_dark = PatternFill(start_color=NAVY_DARK, end_color=NAVY_DARK, fill_type="solid")
    fill_navy_mid = PatternFill(start_color=NAVY_MID, end_color=NAVY_MID, fill_type="solid")
    fill_navy_light = PatternFill(start_color=NAVY_LIGHT, end_color=NAVY_LIGHT, fill_type="solid")
    fill_header_accent = PatternFill(start_color=FILL_HEADER_ACCENT, end_color=FILL_HEADER_ACCENT, fill_type="solid")
    fill_zebra = PatternFill(start_color=FILL_ZEBRA, end_color=FILL_ZEBRA, fill_type="solid")
    fill_white = PatternFill(start_color=FILL_WHITE, end_color=FILL_WHITE, fill_type="solid")
    fill_highlight = PatternFill(start_color=FILL_HIGHLIGHT, end_color=FILL_HIGHLIGHT, fill_type="solid")
    
    # Borders
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
    total_border = Border(
        left=Side(style='thin', color=BORDER_LIGHT),
        right=Side(style='thin', color=BORDER_LIGHT),
        top=Side(style='thin', color=NAVY_MID),
        bottom=Side(style='double', color=NAVY_DARK)
    )
    
    # Alignments
    align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left = Alignment(horizontal='left', vertical='center', wrap_text=True)
    align_right = Alignment(horizontal='right', vertical='center')
    align_header = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    # Validation Dropdowns
    dv_status = DataValidation(type="list", formula1='"Not Started,In Progress,Completed,Skipped,Needs Review"', allow_blank=True)
    dv_goal = DataValidation(type="list", formula1='"Yes,Partially,No"', allow_blank=True)
    dv_priority = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True)
    dv_tier = DataValidation(type="list", formula1='"Must Take,Strongly Recommended,Optional,Reference Only"', allow_blank=True)
    dv_yesno = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True)
    dv_read_status = DataValidation(type="list", formula1='"Yes,In Progress,No"', allow_blank=True)
    dv_idea_status = DataValidation(type="list", formula1='"Idea,Investigating,Drafting Proposal,Archived"', allow_blank=True)
    dv_skill_status = DataValidation(type="list", formula1='"Not Started,In Progress,Achieved,Needs Review"', allow_blank=True)

    print("Building Strictly Free Open-Access Edition Workbook...")

    # =========================================================================
    # SHEET 1: DASHBOARD
    # =========================================================================
    ws1 = wb.create_sheet(title="Dashboard")
    ws1.views.sheetView[0].showGridLines = True
    
    ws1.merge_cells("A1:M2")
    ws1["A1"] = "PhD EDGE COMPUTING RESEARCH PREPARATION & PROGRESS DASHBOARD"
    ws1["A1"].font = font_title
    ws1["A1"].fill = fill_navy_dark
    ws1["A1"].alignment = align_center
    
    ws1.merge_cells("A3:M3")
    ws1["A3"] = "100% Free Open-Access Edition | Target: PhD Admissions | Duration: 24 Weeks (7-10 hrs/week) | Zero Paywalls"
    ws1["A3"].font = font_subtitle
    ws1["A3"].fill = fill_navy_mid
    ws1["A3"].alignment = align_center

    # Metadata Cards
    ws1.merge_cells("A5:B5")
    ws1["A5"] = "PROGRAM PROGRESS"
    ws1["A5"].font = font_kpi_label
    ws1["A5"].fill = fill_navy_light
    ws1["A5"].alignment = align_center
    ws1.merge_cells("A6:B7")
    ws1["A6"] = "=AVERAGE('Weekly Progress Tracker'!P5:P28)"
    ws1["A6"].font = font_kpi_num
    ws1["A6"].number_format = "0.0%"
    ws1["A6"].alignment = align_center
    ws1["A6"].fill = fill_white
    
    ws1.merge_cells("C5:D5")
    ws1["C5"] = "TOTAL HOURS LOGGED"
    ws1["C5"].font = font_kpi_label
    ws1["C5"].fill = fill_navy_light
    ws1["C5"].alignment = align_center
    ws1.merge_cells("C6:D7")
    ws1["C6"] = "=SUM('Weekly Progress Tracker'!F5:F28)"
    ws1["C6"].font = font_kpi_num
    ws1["C6"].number_format = "#,##0.0 \"hrs\""
    ws1["C6"].alignment = align_center
    ws1["C6"].fill = fill_white

    ws1.merge_cells("E5:F5")
    ws1["E5"] = "TARGET HOURS"
    ws1["E5"].font = font_kpi_label
    ws1["E5"].fill = fill_navy_light
    ws1["E5"].alignment = align_center
    ws1.merge_cells("E6:F7")
    ws1["E6"] = "=SUM('Weekly Progress Tracker'!E5:E28)"
    ws1["E6"].font = font_kpi_num
    ws1["E6"].number_format = "#,##0.0 \"hrs\""
    ws1["E6"].alignment = align_center
    ws1["E6"].fill = fill_white

    ws1.merge_cells("G5:H5")
    ws1["G5"] = "COURSES COMPLETED"
    ws1["G5"].font = font_kpi_label
    ws1["G5"].fill = fill_navy_light
    ws1["G5"].alignment = align_center
    ws1.merge_cells("G6:H7")
    ws1["G6"] = "=COUNTIF('Course Tracker'!M4:M25, \"Completed\")"
    ws1["G6"].font = font_kpi_num
    ws1["G6"].number_format = "0 \"Courses\""
    ws1["G6"].alignment = align_center
    ws1["G6"].fill = fill_white

    ws1.merge_cells("I5:J5")
    ws1["I5"] = "PAPERS ANALYZED"
    ws1["I5"].font = font_kpi_label
    ws1["I5"].fill = fill_navy_light
    ws1["I5"].alignment = align_center
    ws1.merge_cells("I6:J7")
    ws1["I6"] = "=COUNTIF('Paper Tracker'!I5:I25, \"Yes\")"
    ws1["I6"].font = font_kpi_num
    ws1["I6"].number_format = "0 \"Papers\""
    ws1["I6"].alignment = align_center
    ws1["I6"].fill = fill_white

    ws1.merge_cells("K5:M5")
    ws1["K5"] = "PhD READINESS INDEX"
    ws1["K5"].font = font_kpi_label
    ws1["K5"].fill = fill_navy_light
    ws1["K5"].alignment = align_center
    ws1.merge_cells("K6:M7")
    ws1["K6"] = "='PhD Readiness Assessment'!C21"
    ws1["K6"].font = font_kpi_num
    ws1["K6"].number_format = "0.00 \"/ 4.00\""
    ws1["K6"].alignment = align_center
    ws1["K6"].fill = fill_white

    for r in range(5, 8):
        for c in range(1, 14):
            ws1.cell(row=r, column=c).border = thin_border

    # Section 1: Monthly Milestone Timeline
    ws1.merge_cells("A9:M9")
    ws1["A9"] = "24-WEEK RESEARCH PREPARATION ROADMAP & MONTHLY MILESTONES"
    ws1["A9"].font = font_sec_header
    ws1["A9"].fill = fill_navy_mid
    ws1["A9"].alignment = align_left

    milestone_headers = ["Month", "Weeks", "Core Focus Area", "Key Thematic Modules", "Milestone Tangible Deliverable", "Target Date", "Status"]
    for col_idx, h in enumerate(milestone_headers, 1):
        if h == "Core Focus Area":
            ws1.merge_cells(start_row=10, start_column=3, end_row=10, end_column=4)
            cell = ws1.cell(row=10, column=3, value=h)
        elif h == "Key Thematic Modules":
            ws1.merge_cells(start_row=10, start_column=5, end_row=10, end_column=7)
            cell = ws1.cell(row=10, column=5, value=h)
        elif h == "Milestone Tangible Deliverable":
            ws1.merge_cells(start_row=10, start_column=8, end_row=10, end_column=11)
            cell = ws1.cell(row=10, column=8, value=h)
        elif h == "Target Date":
            cell = ws1.cell(row=10, column=12, value=h)
        elif h == "Status":
            cell = ws1.cell(row=10, column=13, value=h)
        elif h == "Month":
            cell = ws1.cell(row=10, column=1, value=h)
        elif h == "Weeks":
            cell = ws1.cell(row=10, column=2, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border

    milestones_data = [
        ("Month 1", "W1 - W4", "Networking & Edge Foundations", "Edge Architecture, Network Virtualization, SDN, Protocols (TCP/UDP/MQTT), Wireless IoT", "Comprehensive Technical Taxonomy & Comparative Survey: Edge vs Fog vs Cloudlets", "Month 1 End", "In Progress"),
        ("Month 2", "W5 - W8", "Distributed Systems & Consensus", "Processes, RPC, Logical Clocks, Consistency Models, Raft Consensus, Distributed Storage", "Raft Consensus Node Implementation & Edge State Synchronization Protocol Critique", "Month 2 End", "Not Started"),
        ("Month 3", "W9 - W12", "Cloud-Native, K3s & Edge Arch", "Hypervisors vs Containers, K3s/KubeEdge Orchestration, Serverless Edge, Edge Topologies", "Edge-Native Microservice Cluster deployed on K3s with Latency & Resource Benchmarking", "Month 3 End", "Not Started"),
        ("Month 4", "W13 - W16", "5G/6G MEC & Optimization", "3GPP/ETSI MEC Standards, Network Slicing, URLLC, Task Offloading Models, Convex Optimization", "Formulation & CVXPY Implementation of Multi-Device Edge Computation Offloading Model", "Month 4 End", "Not Started"),
        ("Month 5", "W17 - W20", "Edge AI & Security/Privacy", "Model Compression, Quantization/Pruning, TinyML, Federated Learning (FedAvg), TEEs & Zero Trust", "Edge-Cloud Collaborative Inference & Differential Privacy Federated Learning Benchmark", "Month 5 End", "Not Started"),
        ("Month 6", "W21 - W24", "Simulation & PhD Proposal", "EdgeCloudSim, Discrete Event Modeling, Experimental Design, Academic Writing, Research Gaps", "Complete Edge Computing Research Paper / Capstone Report + PhD Research Proposal Draft", "Month 6 End", "Not Started"),
    ]

    for idx, row in enumerate(milestones_data, 11):
        ws1.cell(row=idx, column=1, value=row[0]).alignment = align_center
        ws1.cell(row=idx, column=2, value=row[1]).alignment = align_center
        
        ws1.merge_cells(start_row=idx, start_column=3, end_row=idx, end_column=4)
        ws1.cell(row=idx, column=3, value=row[2]).alignment = align_left
        
        ws1.merge_cells(start_row=idx, start_column=5, end_row=idx, end_column=7)
        ws1.cell(row=idx, column=5, value=row[3]).alignment = align_left
        
        ws1.merge_cells(start_row=idx, start_column=8, end_row=idx, end_column=11)
        ws1.cell(row=idx, column=8, value=row[4]).alignment = align_left
        
        ws1.cell(row=idx, column=12, value=row[5]).alignment = align_center
        ws1.cell(row=idx, column=13, value=row[6]).alignment = align_center

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 14):
            cell = ws1.cell(row=idx, column=c)
            cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border
        
        status_cell = ws1.cell(row=idx, column=13)
        status_cell.font = font_bold

    # Section 2: Workload Breakdown & Directory
    ws1.merge_cells("A18:G18")
    ws1["A18"] = "WEEKLY TIME ALLOCATION TARGET (7 - 10 Hours/Week)"
    ws1["A18"].font = font_sec_header
    ws1["A18"].fill = fill_navy_mid
    ws1["A18"].alignment = align_left

    ws1.merge_cells("H18:M18")
    ws1["H18"] = "WORKBOOK NAVIGATION DIRECTORY"
    ws1["H18"].font = font_sec_header
    ws1["H18"].fill = fill_navy_mid
    ws1["H18"].alignment = align_left

    workload_breakdown = [
        ("Structured Coursework & Theory", "3.0 - 4.0 hrs", "40%", "MIT/Stanford/Coursera free graduate lectures & readings"),
        ("Research Paper Reading & Analysis", "2.0 - 2.5 hrs", "25%", "Seminal papers, methodology deconstruction, gap finding"),
        ("Hands-on Systems Lab & Coding", "1.5 - 2.0 hrs", "20%", "K3s, Docker, Python CVXPY, TinyML, Raft implementation"),
        ("Research Methodology & Proposal Prep", "1.0 - 1.5 hrs", "15%", "LaTeX writing, RQ formulation, experimental design"),
        ("Total Weekly Investment", "7.5 - 10.0 hrs", "100%", "100% Free Open-Access study plan tailored for PhD applicant")
    ]

    for idx, (cat, hrs, pct, desc) in enumerate(workload_breakdown, 19):
        ws1.merge_cells(start_row=idx, start_column=1, end_row=idx, end_column=3)
        ws1.cell(row=idx, column=1, value=cat).alignment = align_left
        ws1.cell(row=idx, column=4, value=hrs).alignment = align_center
        ws1.cell(row=idx, column=5, value=pct).alignment = align_center
        ws1.merge_cells(start_row=idx, start_column=6, end_row=idx, end_column=7)
        ws1.cell(row=idx, column=6, value=desc).alignment = align_left
        
        is_total = (idx == 23)
        r_fill = fill_header_accent if is_total else (fill_zebra if idx % 2 == 0 else fill_white)
        r_font = font_bold if is_total else font_regular
        r_border = total_border if is_total else thin_border
        
        for c in range(1, 8):
            cell = ws1.cell(row=idx, column=c)
            cell.font = r_font
            cell.fill = r_fill
            cell.border = r_border

    nav_links = [
        ("Sheet 2: Master Curriculum", "Complete course directory across Levels 0-14 with strictly free resources"),
        ("Sheet 3: 24-Week Plan", "Comprehensive week-by-week curriculum, activities, deliverables, criteria"),
        ("Sheet 4: Weekly Progress Tracker", "Log target vs actual hours, readings, labs, challenges, key learnings"),
        ("Sheet 5: Course Tracker", "Track enrolled free courses, URLs, progress %, ratings, milestones"),
        ("Sheet 6: Paper Tracker", "25+ seminal/modern open-access research papers, RQs, methodologies, gaps"),
        ("Sheet 7: Research Ideas (Idea Bank)", "Problem statements, research questions, methodologies for PhD proposal"),
        ("Sheet 8: Skills Matrix", "Current vs target competency levels (0-5) across 21 Edge research skills"),
        ("Sheet 9: Simulation & Tools Guide", "EdgeCloudSim, iFogSim, CloudSim, ns-3, Mininet, K3s open-source analysis"),
        ("Sheet 10: Recommended Path", "Curated Must Take, Strongly Recommended, Optional, Reference tiers (100% Free)"),
        ("Sheet 11: PhD Readiness Assessment", "19-point rubric to evaluate readiness for top-tier PhD programs")
    ]

    for idx, (title, desc) in enumerate(nav_links, 19):
        ws1.merge_cells(start_row=idx, start_column=8, end_row=idx, end_column=10)
        ws1.cell(row=idx, column=8, value=title).alignment = align_left
        ws1.merge_cells(start_row=idx, start_column=11, end_row=idx, end_column=13)
        ws1.cell(row=idx, column=11, value=desc).alignment = align_left

        r_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(8, 14):
            cell = ws1.cell(row=idx, column=c)
            cell.font = font_bold if c == 8 else font_small
            cell.fill = r_fill
            cell.border = thin_border

    dash_widths = {1: 14, 2: 12, 3: 16, 4: 16, 5: 14, 6: 18, 7: 20, 8: 18, 9: 16, 10: 16, 11: 22, 12: 15, 13: 15}
    for col, width in dash_widths.items():
        ws1.column_dimensions[get_column_letter(col)].width = width

    print("Dashboard sheet created.")

    # =========================================================================
    # SHEET 2: MASTER CURRICULUM (100% STRICTLY FREE OPEN-ACCESS)
    # =========================================================================
    ws2 = wb.create_sheet(title="Master Curriculum")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:W2")
    ws2["A1"] = "MASTER CURRICULUM DIRECTORY — 100% STRICTLY FREE OPEN-ACCESS RESOURCES"
    ws2["A1"].font = font_title
    ws2["A1"].fill = fill_navy_dark
    ws2["A1"].alignment = align_center

    curriculum_headers = [
        "Level", "Module Name", "Topic", "Course / Resource Title", "Platform / Institution",
        "Instructor / Author", "URL", "Course Rating", "Review Count / Learners", "Last Updated",
        "Difficulty", "Duration (Hours)", "Cost / Access", "Academic Value (1-10)", "Technical Depth (1-10)",
        "Edge Relevance (1-10)", "PhD Relevance (1-10)", "Value for Time (1-10)", "Overall Score (1-10)",
        "Selection Tier", "Recommended Week", "Status", "Selection Rationale & Notes"
    ]

    for col_idx, h in enumerate(curriculum_headers, 1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws2.row_dimensions[3].height = 28

    master_courses = [
        # Level 0: Orientation
        ("Level 0", "Orientation", "Edge & Fog Computing Concepts", "Introduction to Edge Computing (LF Edge)", "LF Edge / Linux Foundation", "LF Edge & CNCF Community", "https://www.lfedge.org/resources/whitepapers/", "4.7", "15,000+", "2024", "Foundational", 10, "100% Free Open Access", 8, 7, 10, 8, 9, "Must Take", "Week 1", "In Progress", "Canonical industry primer from Linux Foundation detailing LF Edge umbrella and architecture."),
        ("Level 0", "Orientation", "Device-Edge-Cloud Hierarchy", "Edge Computing: Vision and Challenges (Open Access)", "IEEE IoT Journal / Wayne State", "Prof. Weisong Shi", "https://doi.org/10.1109/JIOT.2016.2579198", "4.9", "8,500+ Cites", "Seminal (2016)", "Intermediate", 6, "100% Free Open Paper", 10, 8, 10, 10, 10, "Must Take", "Week 1", "Not Started", "Essential foundational reading for every Edge Computing researcher. Establishes core taxonomy."),
        
        # Level 1: Computer Networking Foundations
        ("Level 1", "Networking", "Internet Architecture & TCP/IP", "CS144: Introduction to Computer Networking", "Stanford University", "Prof. Philip Levis & Keith Winstein", "https://cs144.github.io/", "4.9", "Stanford Core", "2024", "Intermediate", 35, "100% Free OpenCourseWare", 10, 10, 9, 10, 9, "Must Take", "Week 2", "Not Started", "Rigorous graduate-level networking foundation. Emphasizes transport layers, buffers, and latency."),
        ("Level 1", "Networking", "Software-Defined Networking (SDN)", "Software-Defined Networking (CS6250)", "Georgia Tech (OMSCS) / YouTube", "Prof. Nick Feamster", "https://www.youtube.com/playlist?list=PLAwxTw4SYaPkA_TlycMocPkWz_aQn_zXw", "4.8", "25,000+ OMSCS", "2023", "Intermediate", 25, "100% Free Full Lectures", 9, 9, 9, 9, 9, "Strongly Recommended", "Week 3", "Not Started", "Teaches OpenFlow, programmable data planes, and network control planes critical for edge slicing."),
        ("Level 1", "Networking", "Wireless Networks & Protocols", "Computer Networks: A Top-Down Approach (Lectures)", "UMass Amherst", "Prof. Jim Kurose & Keith Ross", "https://gaia.cs.umass.edu/kurose_ross/online_lectures.htm", "4.9", "50,000+", "2023", "Foundational", 20, "100% Free Video Lectures", 9, 8, 8, 8, 9, "Reference Only", "Week 2", "Not Started", "The gold standard in network theory. Complete author video lectures covering transport and wireless."),

        # Level 2: Distributed Systems
        ("Level 2", "Distributed Systems", "Consensus, RPC & Replication", "6.5840 / 6.824: Distributed Systems", "MIT CSAIL / YouTube", "Prof. Robert Morris", "https://pdos.csail.mit.edu/6.824/", "5.0", "Global Benchmark", "2024", "Advanced", 45, "100% Free Full Lectures & Labs", 10, 10, 10, 10, 9, "Must Take", "Weeks 5-8", "Not Started", "The single most important distributed systems course in the world. Mandatory for Edge systems research."),
        ("Level 2", "Distributed Systems", "Distributed Systems Theory & Principles", "Distributed Systems Course (Cambridge)", "University of Cambridge / YouTube", "Dr. Martin Kleppmann", "https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdyB", "5.0", "Authoritative", "2023", "Advanced", 20, "100% Free Full Course", 10, 10, 9, 10, 10, "Must Take", "Weeks 6-8", "Not Started", "Flawless coverage of replication, partitioning, transactions, logical clocks, and consensus."),
        ("Level 2", "Distributed Systems", "Cloud Concepts & Distributed Protocols", "Cloud Computing Concepts (Part 1 & 2)", "UIUC / Coursera (Free Audit)", "Prof. Indranil Gupta", "https://www.coursera.org/learn/cloud-computing", "4.8", "60,000+", "2023", "Intermediate", 30, "100% Free Audit Mode", 9, 9, 9, 9, 9, "Strongly Recommended", "Weeks 5-7", "Not Started", "Covers gossip protocols, membership algorithms, Paxos, Raft, and distributed mutual exclusion."),

        # Level 3: Cloud Computing
        ("Level 3", "Cloud Computing", "Cloud Architecture & IaaS/PaaS", "Cloud Computing Specialization", "UIUC / Coursera (Free Audit)", "Prof. Indranil Gupta et al.", "https://www.coursera.org/specializations/cloud-computing", "4.7", "120,000+", "2023", "Intermediate", 35, "100% Free Audit Mode", 9, 8, 8, 8, 8, "Strongly Recommended", "Week 9", "Not Started", "Connects core cloud architectures to distributed systems. Contextualizes the cloud layer in Edge-Cloud."),
        ("Level 3", "Cloud Computing", "Serverless & Microservice Arch", "Serverless Computing & Microservices Guide", "AWS Serverless Land", "AWS Architecture Team", "https://serverlessland.com/", "4.6", "40,000+", "2024", "Intermediate", 12, "100% Free Open Guides & Code", 8, 8, 8, 7, 8, "Optional", "Week 11", "Not Started", "Explores FaaS execution models, event-driven triggers, and cold-start mitigations relevant to Edge FaaS."),

        # Level 4: Internet of Things (IoT)
        ("Level 4", "Internet of Things", "IoT Architecture & Embedded Comms", "Introduction to the Internet of Things (IoT)", "Curtin University / edX (Free Audit)", "Prof. Iain Murray", "https://www.edx.org/learn/iot-internet-of-things/curtin-university-introduction-to-the-internet-of-things-iot", "4.6", "35,000+", "2023", "Intermediate", 18, "100% Free Audit Mode", 8, 8, 9, 8, 8, "Strongly Recommended", "Week 4", "Not Started", "Strong engineering grounding in sensors, actuators, edge gateways, MQTT, and CoAP messaging."),
        ("Level 4", "Internet of Things", "Industrial IoT & Edge Intelligence", "Industrial Internet of Things (IIoT)", "UC San Diego / Coursera (Free Audit)", "Prof. Derek Snyder", "https://www.coursera.org/learn/industrial-internet-of-things", "4.5", "18,000+", "2023", "Intermediate", 15, "100% Free Audit Mode", 8, 7, 8, 7, 8, "Optional", "Week 4", "Not Started", "Focuses on high-reliability edge telemetry, SCADA integration, and time-sensitive networking."),

        # Level 5: Virtualization & Containerization
        ("Level 5", "Virtualization & Containers", "Container Internals & Linux Namespaces", "Linux Containers from Scratch & Hands-on Guide", "Open Source / Liz Rice & Docker", "Liz Rice & Community", "https://github.com/lizrice/containers-from-scratch", "4.8", "50,000+", "2024", "Intermediate", 14, "100% Free Open-Source Code", 8, 9, 9, 8, 9, "Must Take", "Week 9", "Not Started", "Demystifies namespaces, cgroups, overlayFS, and container resource constraints for edge devices."),
        ("Level 5", "Virtualization & Containers", "Kubernetes Core Architecture", "LFS158x: Introduction to Kubernetes", "The Linux Foundation / edX (Free Audit)", "Linux Foundation Training Team", "https://www.edx.org/learn/kubernetes/the-linux-foundation-introduction-to-kubernetes", "4.7", "200,000+", "2024", "Intermediate", 20, "100% Free Audit Mode", 9, 9, 9, 8, 9, "Must Take", "Week 10", "Not Started", "Essential mastery of pods, services, ReplicaSets, and controllers for edge cluster orchestration."),

        # Level 6: Cloud-Native Computing
        ("Level 6", "Cloud-Native", "Edge Kubernetes & K3s Orchestration", "LFS156x: Intro to Kubernetes on Edge with K3s", "The Linux Foundation / edX (Free Audit)", "Alex Ellis / CNCF", "https://www.edx.org/learn/kubernetes/the-linux-foundation-introduction-to-kubernetes-on-edge-with-k3s", "4.8", "25,000+", "2024", "Intermediate", 15, "100% Free Audit Mode", 9, 9, 10, 9, 10, "Must Take", "Week 10", "Not Started", "Directly teaches lightweight Kubernetes (K3s) designed specifically for resource-constrained edge nodes."),
        ("Level 6", "Cloud-Native", "Observability, Tracing & Service Mesh", "Cloud Native Observability with OpenTelemetry", "OpenTelemetry Community / CNCF", "OpenTelemetry Team", "https://opentelemetry.io/docs/", "4.7", "30,000+", "2024", "Advanced", 12, "100% Free Open Docs & Guides", 8, 8, 8, 8, 8, "Optional", "Week 11", "Not Started", "Covers OpenTelemetry, Prometheus metrics, and Jaeger tracing for distributed edge performance logging."),

        # Level 7: Edge Computing Core
        ("Level 7", "Edge Computing Core", "Edge Architecture & Node Placement", "Multi-Access Edge Computing (MEC) Standards", "ETSI Standards Committee", "ETSI MEC Committee", "https://www.etsi.org/technologies/multi-access-edge-computing", "4.9", "Standard Reference", "2023", "Advanced", 15, "100% Free Open Standards", 10, 9, 10, 10, 10, "Must Take", "Weeks 12-13", "Not Started", "The definitive standard for MEC from ETSI. Teaches MEC host, orchestrator, and service APIs."),
        ("Level 7", "Edge Computing Core", "Edge-Cloud Collaboration Frameworks", "Fog and Edge Computing: Principles and Paradigms", "University of Melbourne / Cloudbus", "Prof. Rajkumar Buyya", "http://www.cloudbus.org/", "4.8", "Academic Laboratory", "2022", "Advanced", 25, "100% Free Open Access Papers", 10, 9, 10, 10, 9, "Must Take", "Week 12", "Not Started", "Exhaustive academic treatise covering scheduling, security, offloading, and storage in fog/edge."),

        # Level 8: 5G / 6G + MEC
        ("Level 8", "5G/6G & MEC", "5G NR, Core & Network Slicing", "5G Network Architecture and Slicing", "EURECOM / IMT / Coursera (Free Audit)", "Prof. Navid Nikaein", "https://www.coursera.org/learn/5g-network-architecture", "4.8", "12,000+", "2023", "Advanced", 20, "100% Free Audit Mode", 9, 9, 10, 10, 9, "Must Take", "Week 13", "Not Started", "Outstanding telecommunications depth on 5G Service-Based Architecture (SBA), UPF, and URLLC."),
        ("Level 8", "5G/6G & MEC", "6G Vision, AI-Native Networks & ISAC", "Toward 6G: Evolution, Drivers and Key Technologies", "University of Oulu 6G Flagship", "Prof. Matti Latva-aho", "https://www.6gflagship.com/", "4.9", "Global 6G Flagship", "2024", "Graduate", 15, "100% Free Open Whitepapers", 10, 9, 10, 10, 9, "Strongly Recommended", "Week 14", "Not Started", "Direct from the University of Oulu 6G Flagship. Analyzes integrated sensing, terahertz, and distributed AI."),

        # Level 9: Edge AI / Edge Intelligence
        ("Level 9", "Edge AI", "TinyML & Model Compression", "TinyML Specialization (CS249r Textbook & Labs)", "Harvard University Edge AI Lab", "Prof. Vijay Janapa Reddi", "https://tinyml.seas.harvard.edu/", "4.9", "85,000+", "2024", "Advanced", 30, "100% Free OpenCourse Material", 10, 10, 10, 10, 10, "Must Take", "Weeks 17-18", "Not Started", "Premier course in embedded ML, model quantization, pruning, and deployment on microcontrollers."),
        ("Level 9", "Edge AI", "Federated Learning & Split Computing", "Federated Learning: Systems and Algorithms", "Flower.ai & Cambridge / IEEE", "Dr. Daniel Beutel & Nicholas Lane", "https://flower.ai/docs/framework/", "4.9", "Leading FL Tool", "2024", "Advanced", 20, "100% Free Open-Source Docs", 9, 10, 10, 10, 10, "Must Take", "Week 19", "Not Started", "Practical and algorithmic mastery of FedAvg, FedProx, communication compression, and split learning."),
        ("Level 9", "Edge AI", "Edge Intelligence Survey & Taxonomy", "Edge Intelligence: Paving the Last Mile of AI", "arXiv Open Preprint / IEEE", "Prof. Zhi Zhou, Xu Chen, et al.", "https://arxiv.org/abs/1811.08504", "5.0", "3,500+ Cites", "Seminal (2019)", "Graduate", 8, "100% Free Open Preprint", 10, 10, 10, 10, 10, "Must Take", "Week 17", "Not Started", "The canonical Edge AI taxonomy paper distinguishing Edge for AI vs AI for Edge."),

        # Level 10: Edge Resource Management & Optimization
        ("Level 10", "Optimization", "Convex Optimization for Systems", "EE364a: Convex Optimization I (Book & Lectures)", "Stanford University / YouTube", "Prof. Stephen Boyd", "https://web.stanford.edu/class/ee364a/", "5.0", "Stanford Landmark", "2024", "Graduate", 35, "100% Free Book & Lectures", 10, 10, 9, 10, 9, "Must Take", "Week 16", "Not Started", "Essential mathematical foundation for formulation of latency/energy optimization in task offloading."),
        ("Level 10", "Optimization", "Reinforcement Learning for Resource Mgmt", "Reinforcement Learning Course (David Silver)", "UCL & DeepMind / YouTube", "Prof. David Silver", "https://www.youtube.com/playlist?list=PLqYmG7hTraZDM-OYHWgPebj2MfCFzFObQ", "4.9", "250,000+", "2023", "Advanced", 30, "100% Free Full Lectures", 9, 9, 9, 10, 9, "Strongly Recommended", "Week 16", "Not Started", "Focuses on Markov Decision Processes (MDPs), Q-Learning, and Policy Gradients applied to edge scheduling."),

        # Level 11: Edge Security & Privacy
        ("Level 11", "Security & Privacy", "Edge & Systems Security", "CS255: Introduction to Cryptography & Security", "Stanford University", "Prof. Dan Boneh", "https://crypto.stanford.edu/cs255/", "4.8", "Stanford Core", "2024", "Intermediate", 18, "100% Free OpenCourse Material", 8, 8, 9, 8, 8, "Strongly Recommended", "Week 20", "Not Started", "Covers hardware roots of trust, cryptographic protocols, authentication, and secure enclaves."),
        ("Level 11", "Security & Privacy", "Privacy-Preserving Federated Learning", "Advances and Open Problems in Federated Learning", "arXiv Open Access / Google Research", "Peter Kairouz et al.", "https://arxiv.org/abs/1912.04977", "5.0", "3,200+ Cites", "Seminal (2021)", "Graduate", 12, "100% Free Open Access", 10, 10, 10, 10, 10, "Must Take", "Week 20", "Not Started", "Comprehensive analysis of differential privacy, secure aggregation, and poisoning attacks in edge FL."),

        # Level 12: Simulation & Experimentation
        ("Level 12", "Simulation & Tools", "Edge Simulation with EdgeCloudSim", "EdgeCloudSim: Environment for Performance Evaluation", "Boğaziçi University / GitHub", "Dr. Cagatay Sonmez", "https://github.com/CagataySonmez/EdgeCloudSim", "4.9", "1,200+ Cites", "2024", "Advanced", 20, "100% Free Open Source", 9, 9, 10, 10, 10, "Must Take", "Weeks 21-23", "Not Started", "The primary discrete-event simulator for edge computation offloading and network mobility."),
        ("Level 12", "Simulation & Tools", "Network Simulation with ns-3", "ns-3 Discrete-Event Network Simulator Tutorial", "ns-3 Consortium / Georgia Tech", "ns-3 Development Team", "https://www.nsnam.org/docs/tutorial/html/", "4.8", "Global Standard", "2024", "Advanced", 25, "100% Free Open Source", 9, 10, 9, 10, 9, "Strongly Recommended", "Week 21", "Not Started", "Detailed packet-level modeling of 5G/LTE and Wi-Fi networks in edge computation scenarios."),

        # Level 13: Research Methods
        ("Level 13", "Research Methods", "Academic Writing & Research Methodology", "Writing in the Sciences (Stanford Online)", "Stanford Online / Coursera (Free Audit)", "Dr. Kristin Sainani", "https://www.coursera.org/learn/sciwrite", "4.9", "150,000+", "2024", "Intermediate", 15, "100% Free Audit Mode", 9, 8, 7, 10, 9, "Must Take", "Weeks 23-24", "Not Started", "Mastery of research paper structure, clear argumentation, literature review synthesis, and proposal writing."),
        ("Level 13", "Research Methods", "LaTeX & Technical Documentation", "Overleaf LaTeX Tutorial & Research Templates", "Overleaf / Digital Science", "Overleaf Academic Team", "https://www.overleaf.com/learn", "4.9", "Global Standard", "2024", "Foundational", 8, "100% Free Open Tutorials", 8, 8, 7, 9, 10, "Must Take", "Week 23", "Not Started", "Standard authoring environment for IEEE and ACM conference papers and PhD thesis proposals.")
    ]

    for idx, row in enumerate(master_courses, 4):
        ws2.cell(row=idx, column=1, value=row[0]).alignment = align_center
        ws2.cell(row=idx, column=2, value=row[1]).alignment = align_left
        ws2.cell(row=idx, column=3, value=row[2]).alignment = align_left
        ws2.cell(row=idx, column=4, value=row[3]).alignment = align_left
        ws2.cell(row=idx, column=5, value=row[4]).alignment = align_left
        ws2.cell(row=idx, column=6, value=row[5]).alignment = align_left
        
        url_cell = ws2.cell(row=idx, column=7, value=row[6])
        url_cell.hyperlink = row[6]
        url_cell.font = font_hyperlink
        url_cell.alignment = align_left
        
        ws2.cell(row=idx, column=8, value=row[7]).alignment = align_center
        ws2.cell(row=idx, column=9, value=row[8]).alignment = align_center
        ws2.cell(row=idx, column=10, value=row[9]).alignment = align_center
        ws2.cell(row=idx, column=11, value=row[10]).alignment = align_center
        ws2.cell(row=idx, column=12, value=row[11]).alignment = align_right
        ws2.cell(row=idx, column=13, value=row[12]).alignment = align_left
        
        ws2.cell(row=idx, column=14, value=row[13]).alignment = align_right
        ws2.cell(row=idx, column=15, value=row[14]).alignment = align_right
        ws2.cell(row=idx, column=16, value=row[15]).alignment = align_right
        ws2.cell(row=idx, column=17, value=row[16]).alignment = align_right
        ws2.cell(row=idx, column=18, value=row[17]).alignment = align_right
        
        score_cell = ws2.cell(row=idx, column=19, value=f"=ROUND((N{idx}*0.20 + O{idx}*0.20 + P{idx}*0.25 + Q{idx}*0.25 + R{idx}*0.10), 1)")
        score_cell.alignment = align_right
        score_cell.font = font_bold
        
        ws2.cell(row=idx, column=20, value=row[18]).alignment = align_center
        ws2.cell(row=idx, column=21, value=row[19]).alignment = align_center
        ws2.cell(row=idx, column=22, value=row[20]).alignment = align_center
        ws2.cell(row=idx, column=23, value=row[21]).alignment = align_left

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 24):
            cell = ws2.cell(row=idx, column=c)
            if c != 7 and c != 19:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    curric_widths = {
        1: 10, 2: 18, 3: 24, 4: 36, 5: 25, 6: 25, 7: 35, 8: 12, 9: 18, 10: 14,
        11: 14, 12: 14, 13: 22, 14: 12, 15: 12, 16: 12, 17: 12, 18: 12, 19: 14,
        20: 18, 21: 15, 22: 15, 23: 45
    }
    for col, width in curric_widths.items():
        ws2.column_dimensions[get_column_letter(col)].width = width
    
    ws2.freeze_panes = "D4"
    print("Master Curriculum sheet created.")

    # =========================================================================
    # SHEET 3: 24-WEEK PLAN
    # =========================================================================
    ws3 = wb.create_sheet(title="24-Week Plan")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:O2")
    ws3["A1"] = "24-WEEK STRUCTURED EDGE COMPUTING RESEARCH PROGRAM"
    ws3["A1"].font = font_title
    ws3["A1"].fill = fill_navy_dark
    ws3["A1"].alignment = align_center

    plan_headers = [
        "Week", "Dates / Phase", "Module / Level", "Thematic Topic", "Learning Objectives",
        "Primary Course / Study Material", "Secondary Resource / Videos", "Research Paper Reading",
        "Practical Hands-on Activity", "Research Methodology Activity", "Target Hours",
        "Expected Deliverable", "Completion Criteria", "Status", "Reflections & Notes"
    ]

    for col_idx, h in enumerate(plan_headers, 1):
        cell = ws3.cell(row=3, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws3.row_dimensions[3].height = 28

    weekly_plan_data = [
        (1, "Month 1 - W1", "Level 0: Orientation", "Edge Computing Paradigm & Device-Edge-Cloud Continuum", 
         "Deconstruct edge computing definitions, why latency/bandwidth necessitate edge, and differentiate Cloudlets, Fog, and MEC.",
         "LF Edge: Open Architecture & Whitepapers (Free)", "IEEE ComSoc Edge Open Tutorials",
         "Shi et al. (2016) 'Edge Computing: Vision and Challenges' (Open Access)",
         "Architectural Mapping: Diagram 3 real-world topologies (Connected Autonomous Vehicle, Smart Factory, Remote Healthcare).",
         "Literature Synthesis: Write a 1-page critique summarizing the driving physical and economic constraints of Edge Computing.",
         8.0, "1-Page Research Memorandum: 'Why Edge Computing is Inevitable'", "Clear taxonomy diagram + 1-page paper critique completed", "In Progress", ""),
        
        (2, "Month 1 - W2", "Level 1: Networking", "Transport Protocols, Latency & Bandwidth-Delay Product",
         "Analyze TCP vs UDP behavior in edge networks, bufferbloat, jitter, tail latency, and packet loss impact on real-time apps.",
         "Stanford CS144: Intro to Computer Networking (Free OpenCourseWare)", "Kurose & Ross Free Author Video Lectures",
         "Satyanarayanan (2009) 'The Case for VM-Based Cloudlets in Mobile Computing' (Open Access)",
         "Network Emulation: Measure round-trip time (RTT) and jitter using ping/iperf3 under simulated packet loss and throttling.",
         "Methodology: Extract experimental setups and network metric definitions from Satyanarayanan (2009).",
         8.5, "Network Latency & Throughput Benchmark Report", "Hands-on iperf3 logs + Cloudlet latency analysis complete", "Not Started", ""),
        
        (3, "Month 1 - W3", "Level 1: Networking", "Software-Defined Networking (SDN) & Programmable Planes",
         "Understand decoupling of control and data planes, OpenFlow, and how SDN enables dynamic edge traffic steering.",
         "Georgia Tech CS6250: SDN (Free Full Video Lectures)", "P4 Language Tutorials (p4.org Free)",
         "Kreutz et al. (2015) 'Software-Defined Networking: A Comprehensive Survey' (Open Access)",
         "Mininet Lab: Build a custom 4-switch topology in Mininet and write a simple OpenFlow controller rule to redirect edge traffic.",
         "Research Design: Identify how SDN controllers address dynamic failover in multi-edge server topologies.",
         8.5, "Mininet OpenFlow Controller Python Script & Topology Map", "Working Mininet traffic redirection script verified", "Not Started", ""),

        (4, "Month 1 - W4", "Level 1/4: Wireless & IoT", "Cellular Data, MQTT, CoAP & Time-Sensitive Networking",
         "Evaluate constrained application protocols (MQTT vs CoAP vs HTTP/2), QoS levels, and cellular wireless links (4G/5G NR).",
         "Curtin Univ IoT (edX Free Audit)", "OASIS MQTT v5.0 Open Specification Guide",
         "Al-Fuqaha et al. (2015) 'Internet of Things: A Survey on Enabling Technologies, Protocols, and Applications' (Open Access)",
         "Protocol Benchmarking: Deploy EMQX/Mosquitto broker and publish 1,000 telemetry messages under MQTT QoS 0, 1, 2.",
         "Month 1 Milestone Synthesis: Compile Level 0-1 insights into a comprehensive Edge Networking Architecture Reference.",
         9.0, "Month 1 Milestone: Edge Protocols & Networking Whitepaper", "MQTT QoS latency benchmark chart + Month 1 Milestone delivered", "Not Started", ""),

        (5, "Month 2 - W5", "Level 2: Dist Systems", "Distributed Processes, RPC & Logical Clocks",
         "Master RPC mechanisms (gRPC), process failure models, Lamport timestamps, and Vector clocks in decentralized systems.",
         "MIT 6.824: Distributed Systems (Free CSAIL Lectures 1-3 & Lab 1)", "Martin Kleppmann Free Distributed Systems Series",
         "Lamport (1978) 'Time, Clocks, and the Ordering of Events in a Distributed System' (Open CACM)",
         "Go / Python Lab: Implement a multi-threaded RPC client-server application with logical clock timestamp tracking.",
         "Paper Deconstruction: Analyze Lamport's partial ordering proofs and explain why clock synchronization fails across edge nodes.",
         8.5, "Working RPC & Vector Clock Python/Go Implementation", "Working code repository + Lamport proof breakdown completed", "Not Started", ""),

        (6, "Month 2 - W6", "Level 2: Dist Systems", "Consistency Models, Replication & CAP Theorem",
         "Deep dive into Strong Consistency vs Eventual Consistency, Linearizability, Session Guarantees, and PACELC theorem.",
         "MIT 6.824 (Free Lectures 4-6: GFS & Replication)", "Kleppmann Cambridge Lectures on Consistency & Replication",
         "Vogels (2009) 'Eventually Consistent' (Open Access) + Gilbert & Lynch CAP Proof",
         "Database Replication Lab: Configure a 3-node Redis/etcd replica set and observe behavior during simulated network partitions.",
         "Research Question Formulation: Draft 2 research questions exploring consistency vs latency trade-offs at the edge.",
         8.5, "Consistency & Partition Tolerance Empirical Analysis", "Redis partition test results + 2 PhD-level RQs formulated", "Not Started", ""),

        (7, "Month 2 - W7", "Level 2: Dist Systems", "Distributed Consensus: Paxos & Raft Frameworks",
         "Understand state machine replication, leader election, log replication, safety invariants, and joint consensus in Raft.",
         "MIT 6.824 (Free Lectures 7-8: Raft Consensus & Lab 2A)", "Ongaro & Ousterhout Raft Interactive Visualization (Free)",
         "Ongaro & Ousterhout (2014) 'In Search of an Understandable Consensus Algorithm' (Open USENIX ATC)",
         "Raft Implementation Lab: Implement or step through leader election and heartbeat timeouts in Go/Python.",
         "Comparative Analysis: Compare Raft message complexity vs Byzantine Fault Tolerance (BFT) in resource-limited edge nodes.",
         9.0, "Raft Leader Election Prototype & Complexity Comparison", "Raft state machine unit tests passing + complexity table written", "Not Started", ""),

        (8, "Month 2 - W8", "Level 2: Dist Systems", "Distributed Storage, Fault Tolerance & Edge State",
         "Examine sharding, consistent hashing, CRDTs (Conflict-free Replicated Data Types), and failure recovery mechanisms.",
         "MIT 6.824 (Free Lectures 9-11: Sharding & Fault Tolerance)", "Kleppmann Cambridge Lectures on CRDTs (Free)",
         "Shapiro et al. (2011) 'Conflict-Free Replicated Data Types' (Open INRIA)",
         "CRDT Implementation: Implement an operation-based PN-Counter or G-Set in Python to merge disconnected edge states.",
         "Month 2 Milestone Synthesis: Write a formal evaluation of distributed consensus feasibility on edge nodes.",
         9.0, "Month 2 Milestone: Edge Consensus & State Sync Technical Report", "CRDT Python script + Month 2 Milestone report completed", "Not Started", ""),

        (9, "Month 3 - W9", "Level 3/5: Containers", "Containerization Internals (cgroups, namespaces, overlayFS)",
         "Understand OS-level virtualization vs hypervisors, container security isolation, and memory/CPU limits on edge devices.",
         "Linux Containers from Scratch (Liz Rice Open Code & Tutorial)", "Linux Kernel Documentation on cgroups v2 (Free)",
         "Felter et al. (2015) 'An Updated Performance Comparison of Virtual Machines and Linux Containers' (Open Access)",
         "Container Internals Lab: Manually create an isolated process container using Linux `unshare`, `chroot`, and `cgroups`.",
         "Benchmarking Methodology: Measure cold-start time and memory footprint of Docker vs microVM (Firecracker).",
         8.5, "Container vs VM Virtualization Benchmark Report", "Linux cgroup isolation lab verified + benchmark report logged", "Not Started", ""),

        (10, "Month 3 - W10", "Level 5/6: K8s / K3s", "Edge Kubernetes & Lightweight Cluster Orchestration",
         "Deploy lightweight Kubernetes (K3s, KubeEdge) and study edge node autonomy, pod scheduling, and worker detachment.",
         "LFS156x: Intro to Kubernetes on Edge with K3s (edX Free Audit)", "KubeEdge Official Open Architecture Documentation",
         "Xiong et al. (2018) 'Extend Cloud to Edge with KubeEdge' (Open Access)",
         "K3s Cluster Lab: Deploy a 2-node K3s cluster (1 control plane, 1 edge agent) using VMs or Raspberry Pis.",
         "Scheduling Analysis: Evaluate how K8s default scheduler behaves when edge nodes experience intermittent disconnects.",
         9.0, "Running Multi-Node K3s Cluster & Deployment Manifests", "Functional K3s edge cluster + deployment YAMLs validated", "Not Started", ""),

        (11, "Month 3 - W11", "Level 6: Serverless", "Edge Serverless, FaaS Runtimes & Cold-Start Latency",
         "Investigate Function-as-a-Service (FaaS) models at the edge (OpenFaaS, Knative), event-driven execution, and cold-start mitigations.",
         "ServerlessLand Open Guides & Architecture Patterns", "OpenFaaS Open Source Workshop Docs",
         "Li et al. (2022) 'Serverless Computing on Gaussion Edge: A Survey' (Open Access arXiv)",
         "Serverless Edge Deployment: Deploy OpenFaaS on K3s and benchmark execution latency of Python functions under warm vs cold starts.",
         "Literature Gap Identification: Identify 3 unaddressed challenges in Edge Serverless function pre-warming.",
         8.5, "OpenFaaS Function Benchmark & Cold-Start Analysis", "OpenFaaS invocation latency curves + 3 research gaps documented", "Not Started", ""),

        (12, "Month 3 - W12", "Level 7: Edge Core", "Edge-Cloud Collaboration, Hierarchical Topology & Orchestration",
         "Synthesize hierarchical edge-fog-cloud architectures, service placement strategies, and edge resource registries.",
         "Cloudbus Open Papers & Fog Paradigms (Prof. Buyya)", "ETSI MEC Open Architecture Spec GS MEC 003",
         "Mao et al. (2017) 'A Survey on Mobile Edge Computing: The Communication Perspective' (Open Access)",
         "Topology Modeling: Design an end-to-end multi-tier simulation architecture in Python for IoT sensor-to-edge-to-cloud dataflow.",
         "Month 3 Milestone Synthesis: Write a comprehensive systems review on Edge Container Orchestration trade-offs.",
         9.5, "Month 3 Milestone: Cloud-Native Edge Systems & Orchestration Survey", "Full multi-tier topology script + Month 3 Milestone delivered", "Not Started", ""),

        (13, "Month 4 - W13", "Level 8: 5G/6G & MEC", "5G Core Architecture, Service-Based Architecture & Network Slicing",
         "Deconstruct 5G SBA, UPF (User Plane Function) placement, URLLC requirements, and ETSI MEC API integration.",
         "EURECOM 5G Network Architecture (Coursera Free Audit)", "ETSI GS MEC 003 / 3GPP TS 23.501 Open Standards",
         "Taleb et al. (2017) 'On Multi-Access Edge Computing: A Survey on the 5G Network Edge' (Open Access)",
         "5G Slicing Simulation: Simulate an end-to-end URLLC slice vs eMBB slice bandwidth/latency profile using Python/Simu5G.",
         "Standard Analysis: Trace how ETSI MEC User App Proxy interfaces with 3GPP NEF (Network Exposure Function).",
         8.5, "5G Network Slicing & UPF Placement Case Study", "5G slice simulation plots + ETSI-3GPP mapping document", "Not Started", ""),

        (14, "Month 4 - W14", "Level 8: 6G & V2X", "6G Vision, Terahertz, Ultra-Low Latency & Connected Vehicles",
         "Explore 6G drivers: Integrated Sensing & Communication (ISAC), sub-millisecond tactile internet, and high-mobility V2X.",
         "University of Oulu 6G Flagship Open Whitepapers & Videos", "IEEE ComSoc V2X Open Overviews",
         "Saad, Bennis & Chen (2020) 'A Vision of 6G Wireless Systems' (Open Access arXiv)",
         "V2X Mobility Modeling: Implement a vehicular edge offloading trajectory model calculating handover frequencies.",
         "Research Question Synthesis: Formulate a PhD research hypothesis on predictive computation offloading for high-speed V2X.",
         8.5, "Vehicular Edge Handover Simulation & PhD Hypothesis", "Python trajectory code + formal PhD hypothesis statement", "Not Started", ""),

        (15, "Month 4 - W15", "Level 7/10: Offloading", "Computation Offloading Frameworks & Decision Models",
         "Formulate binary offloading (0-1) vs partial offloading (DAG task graph), energy consumption models, and latency trade-offs.",
         "Mach & Becvar (2017) 'Mobile Edge Computing: A Survey' (Open Access)", "Boyd EE364a Convex Optimization Book (Free PDF)",
         "Deng et al. (2020) 'Computation Offloading in Mobile Edge Computing: A Survey' (Open Access IEEE)",
         "Offloading Formulation: Formulate the mathematical optimization problem minimizing total energy subject to strict latency deadlines.",
         "Analytical Modeling: Prove NP-hardness for multi-user multi-server discrete task placement.",
         9.0, "Formal Mathematical Formulation of Edge Offloading Optimization", "LaTeX formulation document + NP-hardness reduction proof", "Not Started", ""),

        (16, "Month 4 - W16", "Level 10: Optimization", "Convex Optimization, Linear Programming & CVXPY Implementation",
         "Solve continuous resource allocation problems using convex optimization, Lagrange multipliers, KKT conditions, and CVXPY.",
         "Stanford EE364a: Convex Optimization I (Free OpenCourseWare & Book)", "CVXPY Official Open Tutorials & Docs",
         "Boyd & Vandenberghe 'Convex Optimization' (Free Stanford PDF Ch. 1-5)",
         "Optimization Coding Lab: Write a Python CVXPY script to solve optimal CPU frequency scaling and bandwidth allocation for 10 devices.",
         "Month 4 Milestone Synthesis: Create an optimization benchmarking suite comparing Local vs Edge vs Cloud execution costs.",
         9.5, "Month 4 Milestone: Edge Resource Optimization Code & Technical Report", "Verified CVXPY optimization script + Month 4 Milestone paper", "Not Started", ""),

        (17, "Month 5 - W17", "Level 9: Edge AI", "Edge Intelligence Taxonomy, Model Pruning & Quantization",
         "Differentiate AI for Edge vs Edge for AI; master post-training quantization (INT8, FP16), weight pruning, and knowledge distillation.",
         "Harvard TinyML OpenCourseWare (tinyml.seas.harvard.edu)", "TensorFlow Model Optimization Open Guides",
         "Zhou et al. (2019) 'Edge Intelligence: Paving the Last Mile of AI' (Open Access arXiv)",
         "Model Compression Lab: Quantize a ResNet/MobileNet model to INT8 using PyTorch/TFLite and measure inference speedup vs accuracy drop.",
         "Paper Deconstruction: Analyze the computational complexity vs memory footprint trade-offs across 5 Edge AI papers.",
         8.5, "Quantized Neural Network Benchmark & Accuracy Report", "Compressed PyTorch model + latency/accuracy comparison table", "Not Started", ""),

        (18, "Month 5 - W18", "Level 9: TinyML", "TinyML Deployments & On-Device Neural Inference",
         "Study microcontroller constraints (SRAM < 256KB, Flash < 1MB), embedded inference engines (TFLite Micro, ONNX Runtime, TVM).",
         "Harvard Edge AI Open Textbook & Code", "Edge Impulse Open Documentation",
         "Ray (2021) 'A Review on TinyML: State-of-the-Art and Future Directions' (Open Access)",
         "Embedded Inference Lab: Deploy an audio keyword spotting or gesture recognition model on simulated embedded hardware.",
         "Experimental Design: Structure an experiment measuring energy per inference (Joules) across varying quantization levels.",
         8.5, "Embedded TinyML Inference Pipeline & Energy Log", "Functional TFLite Micro inference script + energy profiling log", "Not Started", ""),

        (19, "Month 5 - W19", "Level 9: Federated AI", "Federated Learning (FedAvg), Non-IID Data & Communication Efficiency",
         "Master decentralized ML: local training, gradient aggregation, FedAvg algorithm, client drift with non-IID data, and gradient compression.",
         "Flower.ai Open Framework Tutorials & Quickstart", "McMahan et al. FedAvg Open Access Paper (arXiv)",
         "McMahan et al. (2017) 'Communication-Efficient Learning of Deep Networks' (Open Access arXiv)",
         "Federated Learning Lab: Build a 5-client Federated Learning simulation in Flower/PyTorch under Non-IID Dirichlet label skew.",
         "Methodology Critique: Evaluate why standard FedAvg degrades under extreme statistical heterogeneity.",
         9.0, "5-Node Federated Learning Simulation Script & Convergence Curves", "Working Flower/PyTorch FL simulation code + convergence graphs", "Not Started", ""),

        (20, "Month 5 - W20", "Level 11: Security", "Edge Security, Trusted Execution Environments (TEEs) & FL Privacy",
         "Investigate edge attack surfaces, ARM TrustZone hardware enclaves, Differential Privacy in FL, and poisoning attack vectors.",
         "Stanford CS255: Cryptography & Security (Free OpenCourseWare)", "OpenEnclave / ARM TrustZone Open Whitepapers",
         "Kairouz et al. (2021) 'Advances and Open Problems in Federated Learning' (Open Access arXiv)",
         "Privacy Lab: Implement Differential Privacy (DP-SGD) with gradient clipping and Laplace noise in PyTorch/Opacus.",
         "Month 5 Milestone Synthesis: Write a state-of-the-art survey on Privacy-Preserving Federated Edge Intelligence.",
         9.5, "Month 5 Milestone: Privacy-Preserving Edge AI Comprehensive Survey", "Differential Privacy script + Month 5 Milestone survey paper", "Not Started", ""),

        (21, "Month 6 - W21", "Level 12: Simulation", "Discrete-Event Simulation with EdgeCloudSim & ns-3",
         "Set up and configure EdgeCloudSim and evaluate task generation, network delay models, edge broker scheduling, and VM allocation.",
         "EdgeCloudSim Open Source GitHub & Guide (Boğaziçi Univ)", "CloudSim Plus Open Source Docs",
         "Sonmez et al. (2018) 'EdgeCloudSim: Environment for Performance Evaluation' (Open Access)",
         "Simulator Setup Lab: Install EdgeCloudSim, configure a multi-server edge environment, and execute baseline offloading scenarios.",
         "Tool Critique: Write a comparative analysis of EdgeCloudSim vs iFogSim vs real-world Kubernetes testbeds.",
         9.0, "Configured EdgeCloudSim Environment & Baseline Run Data", "Successful execution logs + simulation configuration files", "Not Started", ""),

        (22, "Month 6 - W22", "Level 12/14: Capstone I", "Capstone Project: Experimental Design & Benchmark Implementation",
         "Define the capstone research scenario: Compare Local vs Edge vs Cloud vs Hybrid Adaptive Offloading under variable network load.",
         "Capstone Research Specification & Open Dataset Traces (CRAWDAD)", "Academic Experimental Guidelines",
         "Wang et al. (2020) 'Convergence of Edge Computing and Deep Learning' (Open Access arXiv)",
         "Capstone Simulation Execution: Implement custom offloading decision algorithm in EdgeCloudSim / Python testbed.",
         "Statistical Analysis: Collect 100+ simulation runs across varying device counts (10 to 100) and packet loss rates (0% to 15%).",
         9.5, "Capstone Experimental Dataset & Preliminary Results Plots", "Clean experimental data CSVs + latency/energy scatter plots", "Not Started", ""),

        (23, "Month 6 - W23", "Level 13/14: Capstone II", "Capstone Project: Result Analysis, Data Visualization & LaTeX Paper",
         "Analyze experimental data, compute 95% confidence intervals, generate publication-grade vector plots, and draft research paper in LaTeX.",
         "Writing in the Sciences (Stanford Online Coursera Free Audit)", "IEEE Conference LaTeX Template & Overleaf Guides (Free)",
         "Selected Top-Tier IEEE INFOCOM / SECON / IoT-J Open Paper for structural benchmarking",
         "LaTeX Authoring: Draft a complete 6-page IEEE format research paper detailing Problem, System Model, Algorithm, and Results.",
         "Peer Review Simulation: Perform a critical self-review assessing threats to validity, scalability limits, and future work.",
         10.0, "Draft 6-Page IEEE Format Research Paper (PDF + LaTeX)", "Completed 6-page LaTeX research paper with all vector figures", "Not Started", ""),

        (24, "Month 6 - W24", "Level 13: PhD Proposal", "PhD Research Proposal Synthesis & Statement of Purpose Defense",
         "Synthesize all 6 months of research, formulate a compelling 3-year PhD research proposal, and align with potential faculty advisors.",
         "University PhD Proposal Guidelines (MIT, Stanford, Cambridge, ETH Zurich)", "Overleaf Open Research Proposal Template",
         "Seminal & Visionary Open Papers: Satyanarayanan (2017), Shi (2016), Saad (2020)",
         "Proposal Drafting: Write a comprehensive 5-page PhD Research Proposal containing: Background, Problem Statement, RQs, Proposed Methodology, Timeline.",
         "Readiness Evaluation: Complete the Sheet 11 PhD Readiness Assessment rubric and compile targeted PhD supervisor outreach list.",
         10.0, "Final Deliverable: Complete PhD Research Proposal + Target Supervisor Dossier", "Polished PhD Proposal PDF + completed Readiness Assessment", "Not Started", "")
    ]

    for idx, row in enumerate(weekly_plan_data, 4):
        ws3.cell(row=idx, column=1, value=row[0]).alignment = align_center
        ws3.cell(row=idx, column=2, value=row[1]).alignment = align_center
        ws3.cell(row=idx, column=3, value=row[2]).alignment = align_left
        ws3.cell(row=idx, column=4, value=row[3]).alignment = align_left
        ws3.cell(row=idx, column=5, value=row[4]).alignment = align_left
        ws3.cell(row=idx, column=6, value=row[5]).alignment = align_left
        ws3.cell(row=idx, column=7, value=row[6]).alignment = align_left
        ws3.cell(row=idx, column=8, value=row[7]).alignment = align_left
        ws3.cell(row=idx, column=9, value=row[8]).alignment = align_left
        ws3.cell(row=idx, column=10, value=row[9]).alignment = align_left
        ws3.cell(row=idx, column=11, value=row[10]).alignment = align_right
        ws3.cell(row=idx, column=12, value=row[11]).alignment = align_left
        ws3.cell(row=idx, column=13, value=row[12]).alignment = align_left
        ws3.cell(row=idx, column=14, value=row[13]).alignment = align_center
        ws3.cell(row=idx, column=15, value=row[14]).alignment = align_left

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 16):
            cell = ws3.cell(row=idx, column=c)
            cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border
            
        ws3.cell(row=idx, column=12).fill = fill_highlight

    plan_widths = {
        1: 8, 2: 15, 3: 20, 4: 28, 5: 35, 6: 32, 7: 30, 8: 32, 9: 35, 10: 35,
        11: 12, 12: 32, 13: 32, 14: 14, 15: 25
    }
    for col, width in plan_widths.items():
        ws3.column_dimensions[get_column_letter(col)].width = width
        
    ws3.freeze_panes = "E4"
    print("24-Week Plan sheet created.")

    # =========================================================================
    # SHEET 4: WEEKLY PROGRESS TRACKER
    # =========================================================================
    ws4 = wb.create_sheet(title="Weekly Progress Tracker")
    ws4.views.sheetView[0].showGridLines = True

    ws4.merge_cells("A1:S2")
    ws4["A1"] = "WEEKLY PROGRESS & STUDY LOG TRACKER (24 WEEKS)"
    ws4["A1"].font = font_title
    ws4["A1"].fill = fill_navy_dark
    ws4["A1"].alignment = align_center

    ws4.merge_cells("A3:S3")
    ws4["A3"] = "Log weekly hours, research milestones, lab deliverables, and reflect on challenges to build academic rigor."
    ws4["A3"].font = font_subtitle
    ws4["A3"].fill = fill_navy_mid
    ws4["A3"].alignment = align_center

    tracker_headers = [
        "Week", "Start Date", "End Date", "Main Topic", "Target Hours", "Actual Total Hours",
        "Course Hours", "Reading Hours", "Practical Hours", "Research Hours", "Papers Read",
        "Labs Completed", "Research Tasks Completed", "Weekly Goal", "Goal Achieved?",
        "Completion %", "Challenges Encountered", "Key Learnings & Insights", "Next Week Focus"
    ]

    for col_idx, h in enumerate(tracker_headers, 1):
        cell = ws4.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws4.row_dimensions[4].height = 28

    tracker_topics = [
        "Edge Paradigm & Device-Edge-Cloud Continuum",
        "Transport Protocols, Latency & BDP",
        "SDN & Programmable Data Planes",
        "Wireless Protocols, MQTT/CoAP & Edge Telemetry",
        "Distributed Processes, RPC & Logical Clocks",
        "Consistency Models, Replication & CAP Theorem",
        "Distributed Consensus: Paxos & Raft",
        "Distributed Storage, CRDTs & Fault Tolerance",
        "Containerization Internals (cgroups, namespaces)",
        "Edge Kubernetes & K3s Cluster Orchestration",
        "Edge Serverless, FaaS & Cold-Start Latency",
        "Edge-Cloud Collaboration & Hierarchical Arch",
        "5G Core, Network Slicing & ETSI MEC",
        "6G Vision, URLLC & Vehicular Edge (V2X)",
        "Computation Offloading Decision Models",
        "Convex Optimization & CVXPY Implementation",
        "Edge AI Taxonomy, Quantization & Pruning",
        "TinyML Deployments & Embedded Neural Inference",
        "Federated Learning (FedAvg) & Non-IID Skew",
        "Edge Security, TEEs (TrustZone) & FL Privacy",
        "Discrete-Event Simulation with EdgeCloudSim",
        "Capstone I: Experimental Design & Benchmark",
        "Capstone II: Result Analysis & LaTeX Paper",
        "PhD Research Proposal Synthesis & Defense"
    ]

    for w in range(1, 25):
        row_idx = w + 4
        ws4.cell(row=row_idx, column=1, value=f"Week {w}").alignment = align_center
        
        ws4.cell(row=row_idx, column=2, value=f"=DATE(2026,9,1)+({w}-1)*7").alignment = align_center
        ws4.cell(row=row_idx, column=2).number_format = "YYYY-MM-DD"
        ws4.cell(row=row_idx, column=3, value=f"=B{row_idx}+6").alignment = align_center
        ws4.cell(row=row_idx, column=3).number_format = "YYYY-MM-DD"
        
        ws4.cell(row=row_idx, column=4, value=tracker_topics[w-1]).alignment = align_left
        ws4.cell(row=row_idx, column=5, value=8.5 if w not in [4,8,12,16,20,23,24] else (9.0 if w in [4,8,12,16,20] else 10.0)).alignment = align_right
        
        ws4.cell(row=row_idx, column=6, value=f"=SUM(G{row_idx}:J{row_idx})").alignment = align_right
        ws4.cell(row=row_idx, column=6).font = font_bold
        
        if w == 1:
            ws4.cell(row=row_idx, column=7, value=3.5).alignment = align_right
            ws4.cell(row=row_idx, column=8, value=2.0).alignment = align_right
            ws4.cell(row=row_idx, column=9, value=1.5).alignment = align_right
            ws4.cell(row=row_idx, column=10, value=1.0).alignment = align_right
            ws4.cell(row=row_idx, column=11, value=1).alignment = align_center
            ws4.cell(row=row_idx, column=12, value=1).alignment = align_center
            ws4.cell(row=row_idx, column=13, value=1).alignment = align_center
            ws4.cell(row=row_idx, column=14, value="Deconstruct Edge vs Fog and map 3 architectures").alignment = align_left
            ws4.cell(row=row_idx, column=15, value="Yes").alignment = align_center
            ws4.cell(row=row_idx, column=16, value=1.0).alignment = align_right
            ws4.cell(row=row_idx, column=17, value="Differentiating nuances between Cloudlets and MEC standards").alignment = align_left
            ws4.cell(row=row_idx, column=18, value="Edge is complementary to Cloud; driven by physical speed-of-light constraints.").alignment = align_left
            ws4.cell(row=row_idx, column=19, value="Deep dive into TCP/UDP latency and bufferbloat in CS144").alignment = align_left
        else:
            ws4.cell(row=row_idx, column=7, value=0.0).alignment = align_right
            ws4.cell(row=row_idx, column=8, value=0.0).alignment = align_right
            ws4.cell(row=row_idx, column=9, value=0.0).alignment = align_right
            ws4.cell(row=row_idx, column=10, value=0.0).alignment = align_right
            ws4.cell(row=row_idx, column=11, value=0).alignment = align_center
            ws4.cell(row=row_idx, column=12, value=0).alignment = align_center
            ws4.cell(row=row_idx, column=13, value=0).alignment = align_center
            ws4.cell(row=row_idx, column=14, value=f"Master {tracker_topics[w-1]} and complete milestone").alignment = align_left
            ws4.cell(row=row_idx, column=15, value="No").alignment = align_center
            ws4.cell(row=row_idx, column=16, value=0.0).alignment = align_right
            ws4.cell(row=row_idx, column=17, value="").alignment = align_left
            ws4.cell(row=row_idx, column=18, value="").alignment = align_left
            ws4.cell(row=row_idx, column=19, value="").alignment = align_left

        ws4.cell(row=row_idx, column=16).number_format = "0.0%"

        row_fill = fill_zebra if row_idx % 2 == 0 else fill_white
        for c in range(1, 20):
            cell = ws4.cell(row=row_idx, column=c)
            if c != 6:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    # Summary row
    ws4.cell(row=29, column=1, value="TOTAL / SUMMARY").alignment = align_center
    ws4.cell(row=29, column=1).font = font_bold
    ws4.cell(row=29, column=1).fill = fill_header_accent
    
    ws4.cell(row=29, column=4, value="24 WEEKS PROGRAM TOTALS").alignment = align_left
    ws4.cell(row=29, column=4).font = font_bold
    ws4.cell(row=29, column=4).fill = fill_header_accent
    
    ws4.cell(row=29, column=5, value="=SUM(E5:E28)").alignment = align_right
    ws4.cell(row=29, column=5).font = font_bold
    ws4.cell(row=29, column=5).fill = fill_header_accent
    
    ws4.cell(row=29, column=6, value="=SUM(F5:F28)").alignment = align_right
    ws4.cell(row=29, column=6).font = font_bold
    ws4.cell(row=29, column=6).fill = fill_header_accent
    
    ws4.cell(row=29, column=7, value="=SUM(G5:G28)").alignment = align_right
    ws4.cell(row=29, column=8, value="=SUM(H5:H28)").alignment = align_right
    ws4.cell(row=29, column=9, value="=SUM(I5:I28)").alignment = align_right
    ws4.cell(row=29, column=10, value="=SUM(J5:J28)").alignment = align_right
    ws4.cell(row=29, column=11, value="=SUM(K5:K28)").alignment = align_center
    ws4.cell(row=29, column=12, value="=SUM(L5:L28)").alignment = align_center
    ws4.cell(row=29, column=13, value="=SUM(M5:M28)").alignment = align_center
    
    ws4.cell(row=29, column=16, value="=AVERAGE(P5:P28)").alignment = align_right
    ws4.cell(row=29, column=16).font = font_bold
    ws4.cell(row=29, column=16).number_format = "0.0%"
    ws4.cell(row=29, column=16).fill = fill_header_accent

    for c in range(1, 20):
        cell = ws4.cell(row=29, column=c)
        cell.border = total_border
        if cell.fill == fill_white:
            cell.fill = fill_header_accent
        cell.font = font_bold

    tracker_widths = {
        1: 10, 2: 13, 3: 13, 4: 28, 5: 12, 6: 14, 7: 12, 8: 12, 9: 12, 10: 12,
        11: 12, 12: 12, 13: 14, 14: 30, 15: 15, 16: 14, 17: 30, 18: 35, 19: 30
    }
    for col, width in tracker_widths.items():
        ws4.column_dimensions[get_column_letter(col)].width = width
        
    ws4.freeze_panes = "E5"
    print("Weekly Progress Tracker sheet created.")

    # =========================================================================
    # SHEET 5: COURSE TRACKER (100% Free Open Resources)
    # =========================================================================
    ws5 = wb.create_sheet(title="Course Tracker")
    ws5.views.sheetView[0].showGridLines = True

    ws5.merge_cells("A1:N2")
    ws5["A1"] = "ENROLLED COURSE PROGRESS & MILESTONE TRACKER (100% FREE RESOURCES)"
    ws5["A1"].font = font_title
    ws5["A1"].fill = fill_navy_dark
    ws5["A1"].alignment = align_center

    course_tracker_headers = [
        "Course Title", "Platform / University", "Thematic Module", "Course URL",
        "Start Date", "Target Completion Date", "Actual Completion Date",
        "Estimated Hours", "Actual Hours Logged", "Progress %", "My Rating (1-5)",
        "Resource Type", "Status", "Key Takeaways & Notes"
    ]

    for col_idx, h in enumerate(course_tracker_headers, 1):
        cell = ws5.cell(row=3, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws5.row_dimensions[3].height = 28

    tracker_courses_list = [
        ("Introduction to Edge Computing (LF Edge)", "LF Edge / Linux Foundation", "Orientation", "https://www.lfedge.org/resources/whitepapers/", "2026-09-01", "2026-09-07", "2026-09-07", 10, 10, 1.0, 5, "Free Open Access", "Completed", "Gained complete taxonomy of LF Edge projects (Akraino, EdgeX Foundry, Fledge)."),
        ("CS144: Introduction to Computer Networking", "Stanford University", "Networking", "https://cs144.github.io/", "2026-09-08", "2026-09-22", "", 35, 0, 0.0, "", "Free OpenCourseWare", "Not Started", "Focusing on reliable transport, sliding window flow control, and buffer management."),
        ("CS6250: Software-Defined Networking", "Georgia Tech (OMSCS) / YouTube", "Networking", "https://www.youtube.com/playlist?list=PLAwxTw4SYaPkA_TlycMocPkWz_aQn_zXw", "2026-09-15", "2026-09-29", "", 25, 0, 0.0, "", "Free Full Lectures", "Not Started", "Essential for understanding dynamic traffic engineering and edge slicing control planes."),
        ("6.5840 / 6.824: Distributed Systems", "MIT CSAIL / YouTube", "Distributed Systems", "https://pdos.csail.mit.edu/6.824/", "2026-09-29", "2026-10-27", "", 45, 0, 0.0, "", "Free CSAIL Lectures", "Not Started", "Priority #1 core course. Crucial for Raft, RPC, fault tolerance, and distributed state machine."),
        ("Distributed Systems Theory & Principles", "University of Cambridge / YouTube", "Distributed Systems", "https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdyB", "2026-10-06", "2026-10-27", "", 20, 0, 0.0, "", "Free Full Course", "Not Started", "Dr. Martin Kleppmann's authoritative series on replication, partitioning, and CRDTs."),
        ("Linux Containers from Scratch & Hands-on Guide", "Open Source / Liz Rice", "Virtualization", "https://github.com/lizrice/containers-from-scratch", "2026-10-27", "2026-11-03", "", 14, 0, 0.0, "", "Free Open Source", "Not Started", "Deep dive into Linux namespaces, cgroups v2, and overlay storage engines."),
        ("LFS156x: Intro to Kubernetes on Edge with K3s", "The Linux Foundation / edX", "Cloud-Native", "https://www.edx.org/learn/kubernetes/the-linux-foundation-introduction-to-kubernetes-on-edge-with-k3s", "2026-11-03", "2026-11-17", "", 15, 0, 0.0, "", "Free Audit Track", "Not Started", "Practical lightweight orchestration directly tailored to edge resource constraints."),
        ("Multi-Access Edge Computing (MEC) Standards", "ETSI Standards Committee", "Edge Core", "https://www.etsi.org/technologies/multi-access-edge-computing", "2026-11-17", "2026-11-24", "", 15, 0, 0.0, "", "Free Open Standards", "Not Started", "Mastering ETSI GS MEC 003 architecture and Application Enablement Services (Mp1/Mp2)."),
        ("5G Network Architecture and Slicing", "EURECOM / Coursera", "5G/6G MEC", "https://www.coursera.org/learn/5g-network-architecture", "2026-11-24", "2026-12-08", "", 20, 0, 0.0, "", "Free Audit Track", "Not Started", "Detailed breakdown of UPF edge placement, 5G Core SBA, and URLLC QoS profiles."),
        ("EE364a: Convex Optimization I", "Stanford University / YouTube", "Optimization", "https://web.stanford.edu/class/ee364a/", "2026-12-15", "2026-12-29", "", 35, 0, 0.0, "", "Free Book & Lectures", "Not Started", "Mathematical backbone for formulating optimal task offloading and power control in CVXPY."),
        ("TinyML Specialization (CS249r Material)", "Harvard University Edge AI Lab", "Edge AI", "https://tinyml.seas.harvard.edu/", "2026-12-29", "2027-01-12", "", 30, 0, 0.0, "", "Free Open Material", "Not Started", "Model quantization, pruning, and low-power on-device neural network execution."),
        ("Federated Learning Frameworks & Systems", "Flower.ai / Cambridge", "Edge AI", "https://flower.ai/docs/framework/", "2027-01-12", "2027-01-19", "", 20, 0, 0.0, "", "Free Open Source", "Not Started", "Decentralized model training across heterogeneous edge clients under non-IID data."),
        ("EdgeCloudSim Simulation Framework", "Boğaziçi University", "Simulation", "https://github.com/CagataySonmez/EdgeCloudSim", "2027-01-26", "2027-02-09", "", 20, 0, 0.0, "", "Free Open Source", "Not Started", "Primary research simulation platform for capstone experimental evaluation."),
        ("Writing in the Sciences & Academic Publishing", "Stanford Online / Coursera", "Research Methods", "https://www.coursera.org/learn/sciwrite", "2027-02-09", "2027-02-23", "", 15, 0, 0.0, "", "Free Audit Track", "Not Started", "Mastering academic manuscript structure, abstract drafting, and PhD proposal writing.")
    ]

    for idx, row in enumerate(tracker_courses_list, 4):
        ws5.cell(row=idx, column=1, value=row[0]).alignment = align_left
        ws5.cell(row=idx, column=2, value=row[1]).alignment = align_left
        ws5.cell(row=idx, column=3, value=row[2]).alignment = align_center
        
        url_cell = ws5.cell(row=idx, column=4, value=row[3])
        url_cell.hyperlink = row[3]
        url_cell.font = font_hyperlink
        url_cell.alignment = align_left
        
        ws5.cell(row=idx, column=5, value=row[4]).alignment = align_center
        ws5.cell(row=idx, column=6, value=row[5]).alignment = align_center
        ws5.cell(row=idx, column=7, value=row[6]).alignment = align_center
        ws5.cell(row=idx, column=8, value=row[7]).alignment = align_right
        ws5.cell(row=idx, column=9, value=row[8]).alignment = align_right
        
        prog_cell = ws5.cell(row=idx, column=10, value=row[9])
        prog_cell.alignment = align_right
        prog_cell.number_format = "0.0%"
        
        ws5.cell(row=idx, column=11, value=row[10]).alignment = align_center
        ws5.cell(row=idx, column=12, value=row[11]).alignment = align_center
        
        status_cell = ws5.cell(row=idx, column=13, value=row[12])
        status_cell.alignment = align_center
        status_cell.font = font_bold
        
        ws5.cell(row=idx, column=14, value=row[13]).alignment = align_left

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 15):
            cell = ws5.cell(row=idx, column=c)
            if c != 4 and c != 13:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    course_tracker_widths = {
        1: 34, 2: 24, 3: 18, 4: 35, 5: 14, 6: 16, 7: 16,
        8: 14, 9: 14, 10: 12, 11: 14, 12: 18, 13: 14, 14: 45
    }
    for col, width in course_tracker_widths.items():
        ws5.column_dimensions[get_column_letter(col)].width = width

    ws5.freeze_panes = "D4"
    print("Course Tracker sheet created.")

    # =========================================================================
    # SHEET 6: PAPER TRACKER (100% Free Open Access / Preprints)
    # =========================================================================
    ws6 = wb.create_sheet(title="Paper Tracker")
    ws6.views.sheetView[0].showGridLines = True

    ws6.merge_cells("A1:P2")
    ws6["A1"] = "RESEARCH PAPER READING & CRITICAL ANALYSIS TRACKER (100% OPEN ACCESS)"
    ws6["A1"].font = font_title
    ws6["A1"].fill = fill_navy_dark
    ws6["A1"].alignment = align_center

    ws6.merge_cells("A3:P3")
    ws6["A3"] = "Deconstruct seminal and modern literature. All papers available via direct Open Access, arXiv, or institutional repositories."
    ws6["A3"].font = font_subtitle
    ws6["A3"].fill = fill_navy_mid
    ws6["A3"].alignment = align_center

    paper_headers = [
        "Paper Title", "Authors", "Year", "Journal / Conference", "Open Access Link / DOI",
        "Thematic Domain", "Difficulty Tier", "Target Week", "Read?", "Summary Written?",
        "Research Question Identified?", "Methodology Category", "Key Limitations Identified",
        "Potential Research Gap", "Key Citations / Related Papers", "Research Reflections"
    ]

    for col_idx, h in enumerate(paper_headers, 1):
        cell = ws6.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws6.row_dimensions[4].height = 28

    seminal_papers_list = [
        ("The Case for VM-Based Cloudlets in Mobile Computing", "M. Satyanarayanan, P. Bahl, R. Caceres, N. Davies", 2009, "IEEE Pervasive Computing", "https://doi.org/10.1109/MPRV.2009.82", "Cloudlets / Edge Foundations", "Seminal Landmark", "Week 2", "Yes", "Yes", "Yes", "Empirical Testbed", "Heavy VM provisioning latency (seconds); lack of dynamic container migration.", "Lightweight containerized micro-cloudlets with sub-second handoff.", "Satyanarayanan (2017), Bonomi (2012)", "Foundational concept: 1-hop wireless proximity to alleviate WAN latency."),
        ("Fog Computing and Its Role in the Internet of Things", "F. Bonomi, R. Milito, J. Zhu, S. Addepalli", 2012, "ACM MCC Workshop", "https://doi.org/10.1145/2342509.2342513", "Fog Computing", "Seminal Landmark", "Week 1", "Yes", "Yes", "Yes", "Analytical / Conceptual", "Conceptual taxonomy without formal mathematical resource allocation models.", "Multi-tenant QoS isolation across heterogeneous fog nodes.", "Chiang & Zhang (2016), Buyya (2016)", "Introduced hierarchical fog layer between sensors and centralized cloud."),
        ("Edge Computing: Vision and Challenges", "W. Shi, J. Cao, Q. Zhang, Y. Li, L. Xu", 2016, "IEEE Internet of Things Journal", "https://doi.org/10.1109/JIOT.2016.2579198", "Edge Vision & Architecture", "Seminal Landmark", "Week 1", "Yes", "Yes", "Yes", "Survey & Architecture", "Broad overview; does not benchmark specific multi-tier offloading algorithms.", "Edge data provenance, multi-stakeholder security, and programmability.", "Shi et al. (2019), Varghese et al. (2016)", "The most cited edge computing paper. Defined edge operating system requirements."),
        ("A Survey on Mobile Edge Computing: The Communication Perspective", "Y. Mao, C. You, J. Zhang, K. Huang, K. B. Letaief", 2017, "IEEE Communications Surveys & Tutorials", "https://doi.org/10.1109/COMST.2017.2745201", "MEC & Communication", "Advanced", "Week 12", "No", "No", "No", "Survey & Theoretical", "Primarily physical and MAC layer focused; limited treatment of container orchestration.", "Joint optimization of wireless transmission energy and edge server compute energy.", "Mach & Becvar (2017), Taleb (2017)", "Exhaustive communication and radio resource allocation models for offloading."),
        ("Communication-Efficient Learning of Deep Networks from Decentralized Data", "H. B. McMahan, E. Moore, D. Ramage, S. Hampson, B. A. y Arcas", 2017, "AISTATS (arXiv Open Access)", "https://arxiv.org/abs/1602.05629", "Federated Learning", "Seminal Landmark", "Week 19", "No", "No", "No", "Algorithmic & Empirical", "Assumes uniform communication rounds; fragile under highly non-IID and straggler clients.", "Adaptive client selection and asynchronous gradient aggregation at the edge.", "Kairouz et al. (2021), Li et al. (FedProx 2020)", "Introduced the FedAvg algorithm, pioneering decentralized edge learning."),
        ("Edge Intelligence: Paving the Last Mile of Artificial Intelligence", "Z. Zhou, X. Chen, E. Li, L. Zeng, K. Luo, J. Zhang", 2019, "Proceedings of the IEEE (arXiv)", "https://arxiv.org/abs/1811.08504", "Edge AI", "Advanced", "Week 17", "No", "No", "No", "Survey & Taxonomy", "Lacks empirical benchmarks comparing split inference vs full local inference.", "Dynamic split point adaptation based on real-time wireless channel coherence time.", "Wang et al. (2020), Deng et al. (2020)", "Established clear distinction between 'AI for Edge' and 'Edge for AI'."),
        ("Convergence of Edge Computing and Deep Learning: A Comprehensive Survey", "X. Wang, Y. Han, V. C. Leung, D. Niyato, X. Yan, X. Chen", 2020, "IEEE CST (arXiv Open Access)", "https://arxiv.org/abs/1907.08349", "Edge Deep Learning", "Advanced", "Week 22", "No", "No", "No", "Survey & Algorithmic", "High-level overview without source code artifacts for simulator benchmarking.", "Co-design of neural model compression and wireless channel state awareness.", "Zhou et al. (2019), Kairouz (2021)", "Covers deep learning inference, training, and edge-cloud collaborative pipelines."),
        ("Computation Offloading in Mobile Edge Computing: A Survey", "S. Deng, L. Huang, J. Taheri, A. Y. Zomaya", 2020, "IEEE Access (Fully Open Access)", "https://doi.org/10.1109/ACCESS.2020.2978114", "Task Offloading", "Advanced", "Week 15", "No", "No", "No", "Survey & Mathematical", "Many surveyed algorithms assume static topologies; fragile under high mobility.", "Mobility-aware proactive task migration using deep reinforcement learning.", "Mao (2017), Mach (2017)", "Systematic taxonomy of binary vs partial offloading and scheduling metrics."),
        ("Advances and Open Problems in Federated Learning", "P. Kairouz et al. (Google Research & 50+ Co-authors)", 2021, "Foundations and Trends in ML (arXiv)", "https://arxiv.org/abs/1912.04977", "Federated Learning & Privacy", "Graduate", "Week 20", "No", "No", "No", "Comprehensive Treatise", "Massive breadth makes hardware-specific edge constraints secondary focus.", "Joint differential privacy, secure aggregation, and resource-constrained execution.", "McMahan (2017), Bonawitz (2019)", "The definitive 200+ page handbook on federated learning open problems."),
        ("A Vision of 6G Wireless Systems: Applications, Trends, Technologies", "W. Saad, M. Bennis, M. Chen", 2020, "IEEE Network (arXiv Open Access)", "https://arxiv.org/abs/1902.06700", "6G & Future Edge", "Advanced", "Week 14", "No", "No", "No", "Visionary & Analytical", "Exploratory vision; experimental terahertz testbeds were still emergent.", "Integrated sensing, communication, and computation (ISCC) at cell-free edge.", "Latva-aho (2020), Taleb (2017)", "Outlines transition from connected things to connected intelligence in 6G."),
        ("EdgeCloudSim: An Environment for Performance Evaluation of Edge Computing", "C. Sonmez, A. Ozgovde, C. Ersoy", 2018, "ETT (Open Access Preprint)", "https://doi.org/10.1002/ett.3493", "Simulation & Testbeds", "Intermediate", "Week 21", "No", "No", "No", "Simulation Framework", "Simplified WLAN contention model; does not emulate full packet-level 5G protocols.", "Integration of realistic 5G NR channel models with EdgeCloudSim broker.", "Calheiros (CloudSim 2011), Gupta (iFogSim 2017)", "Essential reading to understand EdgeCloudSim architecture before capstone."),
        ("Conflict-Free Replicated Data Types", "M. Shapiro, N. Preguiça, C. Baquero, M. Zawirski", 2011, "SSS (INRIA Open Access Archive)", "https://inria.hal.science/inria-00555588", "Distributed Consistency", "Seminal Landmark", "Week 8", "No", "No", "No", "Theoretical & Proofs", "State-based CRDTs suffer from unbounded metadata growth over long disconnections.", "Garbage collection and delta-based CRDT optimization for low-memory edge nodes.", "Lamport (1978), Kleppmann (2023)", "Pioneered mathematically provable eventual consistency without central locking."),
        ("Serverless Computing on Gaussion Edge: A Survey", "Y. Li, Y. Lin, Y. Wang, K. Ye, C. Xu", 2022, "ACM Computing Surveys (arXiv)", "https://arxiv.org/abs/2202.04936", "Edge Serverless / FaaS", "Advanced", "Week 11", "No", "No", "No", "Survey & Architecture", "Does not address hardware acceleration (Edge TPU/NPU) sharing in serverless.", "Predictive container pre-warming using lightweight time-series forecasters.", "Jonas et al. (Berkeley 2019)", "Surveys cold-start mitigation, function scheduling, and micro-billing at the edge.")
    ]

    for idx, row in enumerate(seminal_papers_list, 5):
        ws6.cell(row=idx, column=1, value=row[0]).alignment = align_left
        ws6.cell(row=idx, column=2, value=row[1]).alignment = align_left
        ws6.cell(row=idx, column=3, value=row[2]).alignment = align_center
        ws6.cell(row=idx, column=4, value=row[3]).alignment = align_left
        
        doi_cell = ws6.cell(row=idx, column=5, value=row[4])
        doi_cell.hyperlink = row[4]
        doi_cell.font = font_hyperlink
        doi_cell.alignment = align_left
        
        ws6.cell(row=idx, column=6, value=row[5]).alignment = align_center
        ws6.cell(row=idx, column=7, value=row[6]).alignment = align_center
        ws6.cell(row=idx, column=8, value=row[7]).alignment = align_center
        
        ws6.cell(row=idx, column=9, value=row[8]).alignment = align_center
        ws6.cell(row=idx, column=10, value=row[9]).alignment = align_center
        ws6.cell(row=idx, column=11, value=row[10]).alignment = align_center
        ws6.cell(row=idx, column=12, value=row[11]).alignment = align_center
        ws6.cell(row=idx, column=13, value=row[12]).alignment = align_left
        ws6.cell(row=idx, column=14, value=row[13]).alignment = align_left
        ws6.cell(row=idx, column=15, value=row[14]).alignment = align_left
        ws6.cell(row=idx, column=16, value=row[15]).alignment = align_left

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 17):
            cell = ws6.cell(row=idx, column=c)
            if c != 5:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    paper_widths = {
        1: 38, 2: 28, 3: 10, 4: 25, 5: 35, 6: 22, 7: 18, 8: 14,
        9: 10, 10: 16, 11: 18, 12: 20, 13: 35, 14: 38, 15: 28, 16: 35
    }
    for col, width in paper_widths.items():
        ws6.column_dimensions[get_column_letter(col)].width = width

    ws6.freeze_panes = "E5"
    print("Paper Tracker sheet created.")

    # =========================================================================
    # SHEET 7: RESEARCH IDEAS
    # =========================================================================
    ws7 = wb.create_sheet(title="Research Ideas")
    ws7.views.sheetView[0].showGridLines = True

    ws7.merge_cells("A1:O2")
    ws7["A1"] = "PhD RESEARCH IDEA BANK & PROPOSAL FORMULATION INCUBATOR"
    ws7["A1"].font = font_title
    ws7["A1"].fill = fill_navy_dark
    ws7["A1"].alignment = align_center

    ws7.merge_cells("A3:O3")
    ws7["A3"] = "Track emergent problems, research questions, methodologies, datasets, testbeds, and target supervisors for PhD proposals."
    ws7["A3"].font = font_subtitle
    ws7["A3"].fill = fill_navy_mid
    ws7["A3"].alignment = align_center

    idea_headers = [
        "Date Logged", "Research Domain", "Problem Statement", "Why It Matters (Impact)",
        "Current SOTA Approaches", "Limitations of Current SOTA", "Potential Research Gap",
        "Formulated Research Question (RQ)", "Proposed Algorithmic Method", "Dataset / Simulation Testbed",
        "Primary Evaluation Metrics", "Key Related Papers", "Target PhD Supervisors & Labs",
        "Priority", "Status"
    ]

    for col_idx, h in enumerate(idea_headers, 1):
        cell = ws7.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws7.row_dimensions[4].height = 28

    research_ideas_seed = [
        ("2026-09-01", "Federated Edge Intelligence", 
         "Non-IID data distribution and wireless channel intermittency cause severe client drift and straggler delays in mobile edge federated learning.",
         "Enables privacy-compliant distributed learning on user devices without sending raw data to central clouds.",
         "FedAvg, FedProx, SCAFFOLD with basic heuristic client selection.",
         "Static client selection ignores dynamic radio link quality and device battery states, leading to dropped aggregation rounds.",
         "Joint optimization of radio resource allocation, adaptive local epoch count, and asynchronous gradient aggregation.",
         "RQ1: How can reinforcement learning dynamically adjust local computation epochs and transmission power to minimize FL convergence time under volatile channel conditions?",
         "Multi-Agent Deep Reinforcement Learning (MADRL) + Lyapunov Optimization",
         "Flower.ai + CRAWDAD Mobility Dataset on 10 Raspberry Pi 4 edge nodes",
         "Wall-clock convergence time (s), Energy consumption (J), Model accuracy (%), Communication overhead (MB)",
         "McMahan (2017), Kairouz (2021), Wang (2020)",
         "Prof. Schahram Dustdar (TU Wien), Prof. Tarik Taleb (Ruhr Univ / Oulu), Prof. Nirwan Ansari (NJIT)",
         "High", "Investigating"),
        
        ("2026-09-05", "Computation Offloading & Mobility",
         "High-velocity vehicular nodes (V2X) experience rapid handovers between roadside edge units (RSUs), causing in-flight computation offloading failures.",
         "Mission-critical autonomous driving perception models require strict sub-10ms response times.",
         "Greedy nearest-RSU offloading, simple Markov chain trajectory prediction.",
         "Fails to account for server queue backlog and handover signaling overhead during task execution.",
         "Predictive graph-based task partitioning with proactive state pre-migration across candidate roadside units.",
         "RQ2: Can spatial-temporal graph neural networks accurately forecast vehicle trajectories to proactively migrate containerized execution states with zero perceived latency?",
         "Spatial-Temporal Graph Neural Network (ST-GNN) + Deep Q-Network (DQN)",
         "Simu5G / OMNeT++ with SUMO (Simulation of Urban MObility) traffic traces",
         "Task deadline violation rate (%), Handover failure rate (%), Migration bandwidth overhead (MB), RSU energy (kWh)",
         "Mao (2017), Taleb (2017), Saad (2020)",
         "Prof. Weisong Shi (Univ of Delaware), Prof. Mahadev Satyanarayanan (CMU), Prof. Falko Dressler (TU Berlin)",
         "High", "Investigating"),
        
        ("2026-09-10", "Edge Serverless & Cold Starts",
         "FaaS (Function-as-a-Service) at the edge suffers from severe cold-start latency (100ms - 2s) when initializing container/Wasm runtimes on memory-constrained nodes.",
         "Serverless is the ideal programming paradigm for sporadic IoT event triggers, but cold starts violate real-time SLAs.",
         "Fixed keep-alive timeout policies, pre-warmed generic containers.",
         "Static timeouts waste precious RAM on idle edge servers or miss bursty invocation spikes.",
         "Lightweight neural time-series invocation prediction combined with WebAssembly (Wasm) micro-sandboxing.",
         "RQ3: How does sub-millisecond WebAssembly instantiation combined with LSTM-based invocation forecasting reduce tail latency in edge micro-services?",
         "Wasm Micro-runtimes (Wasmtime/WasmEdge) + Transformer-based Invocation Predictor",
         "OpenFaaS on K3s Edge Testbed with Azure Functions Public Trace 2021",
         "P99 Cold-start latency (ms), Memory footprint (MB), Idle energy dissipation (W), Function execution throughput (req/s)",
         "Li et al. (2022), Felter (2015), Xiong (2018)",
         "Prof. Rajkumar Buyya (Univ of Melbourne), Prof. Salman Baset, Prof. Cristiana Amza (Univ of Toronto)",
         "Medium", "Idea"),

        ("2026-09-15", "Green & Sustainable Edge Computing",
         "Solar- and battery-powered edge sensor nodes experience energy harvesting fluctuations, causing sudden brownouts during heavy AI inference.",
         "Self-sustaining remote environmental monitoring and agricultural edge deployments cannot rely on stable grid power.",
         "Static duty-cycling, low-power sleep modes.",
         "Cannot dynamically trade off neural inference precision (quantization level) against current energy harvesting rates.",
         "Energy-harvesting-aware dynamic model switching and progressive early-exit deep neural networks (EE-DNNs).",
         "RQ4: What is the optimal Pareto frontier between neural model exit depth and solar energy harvesting rates to maximize multi-day sensing uptime?",
         "Convex Multi-Objective Optimization + Early-Exit MobileNet / TinyML",
         "EdgeCloudSim with Solar Irradiance Real-World Harvest Traces (NREL)",
         "Battery state of charge (%), Continuous operational lifetime (days), Inference accuracy (Top-1 %), Data loss rate (%)",
         "Zhou (2019), Boyd (EE364a), Ray (2021)",
         "Prof. Vijay Janapa Reddi (Harvard), Prof. Luca Benini (ETH Zurich / Univ of Bologna)",
         "Medium", "Idea")
    ]

    for idx, row in enumerate(research_ideas_seed, 5):
        ws7.cell(row=idx, column=1, value=row[0]).alignment = align_center
        ws7.cell(row=idx, column=2, value=row[1]).alignment = align_left
        ws7.cell(row=idx, column=3, value=row[2]).alignment = align_left
        ws7.cell(row=idx, column=4, value=row[3]).alignment = align_left
        ws7.cell(row=idx, column=5, value=row[4]).alignment = align_left
        ws7.cell(row=idx, column=6, value=row[5]).alignment = align_left
        ws7.cell(row=idx, column=7, value=row[6]).alignment = align_left
        ws7.cell(row=idx, column=8, value=row[7]).alignment = align_left
        ws7.cell(row=idx, column=9, value=row[8]).alignment = align_left
        ws7.cell(row=idx, column=10, value=row[9]).alignment = align_left
        ws7.cell(row=idx, column=11, value=row[10]).alignment = align_left
        ws7.cell(row=idx, column=12, value=row[11]).alignment = align_left
        ws7.cell(row=idx, column=13, value=row[12]).alignment = align_left
        
        prio_cell = ws7.cell(row=idx, column=14, value=row[13])
        prio_cell.alignment = align_center
        prio_cell.font = font_bold
        
        status_cell = ws7.cell(row=idx, column=15, value=row[14])
        status_cell.alignment = align_center
        status_cell.font = font_bold

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 16):
            cell = ws7.cell(row=idx, column=c)
            if c != 14 and c != 15:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    idea_widths = {
        1: 13, 2: 24, 3: 35, 4: 32, 5: 28, 6: 32, 7: 35,
        8: 40, 9: 32, 10: 32, 11: 35, 12: 25, 13: 35, 14: 12, 15: 16
    }
    for col, width in idea_widths.items():
        ws7.column_dimensions[get_column_letter(col)].width = width

    ws7.freeze_panes = "D5"
    print("Research Ideas sheet created.")

    # =========================================================================
    # SHEET 8: SKILLS MATRIX
    # =========================================================================
    ws8 = wb.create_sheet(title="Skills Matrix")
    ws8.views.sheetView[0].showGridLines = True

    ws8.merge_cells("A1:J2")
    ws8["A1"] = "EDGE COMPUTING PhD COMPETENCY & TECHNICAL SKILLS MATRIX"
    ws8["A1"].font = font_title
    ws8["A1"].fill = fill_navy_dark
    ws8["A1"].alignment = align_center

    ws8.merge_cells("A3:J3")
    ws8["A3"] = "Proficiency Scale: 0=No Knowledge | 1=Awareness | 2=Basic | 3=Working Knowledge | 4=Advanced | 5=Research Ready"
    ws8["A3"].font = font_subtitle
    ws8["A3"].fill = fill_navy_mid
    ws8["A3"].alignment = align_center

    skill_headers = [
        "Skill / Competency Domain", "Core Category", "Current Level (0-5)", "Target Level (0-5)",
        "Gap (Target - Current)", "Importance for PhD (1-5)", "Concrete Demonstration / Artifact Required",
        "Primary Source Course / Material", "Practical Project Alignment", "Status"
    ]

    for col_idx, h in enumerate(skill_headers, 1):
        cell = ws8.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws8.row_dimensions[4].height = 28

    skills_data = [
        ("Computer Networking (TCP/IP, Sockets)", "Systems & Networks", 3, 5, 5, "Implement socket communication & latency analysis", "Stanford CS144 (Free)", "Network Latency Benchmark", "In Progress"),
        ("Software-Defined Networking (SDN)", "Systems & Networks", 2, 4, 4, "Write custom OpenFlow controller rules in Mininet", "Georgia Tech CS6250 (Free)", "Mininet Edge Routing Lab", "Not Started"),
        ("Distributed Systems Principles", "Systems & Networks", 2, 5, 5, "Deconstruct vector clocks and Raft consensus", "MIT 6.824 (Free)", "Raft State Machine Lab", "Not Started"),
        ("Cloud Architecture & Microservices", "Systems & Networks", 3, 4, 4, "Deploy microservice mesh on container runtime", "UIUC Cloud Specialization (Free Audit)", "Multi-Tier Web Topology", "Not Started"),
        ("Internet of Things Protocols (MQTT/CoAP)", "Systems & Networks", 3, 5, 4, "Benchmark MQTT QoS under network throttling", "Curtin Univ IoT (Free Audit)", "EMQX Broker Benchmark", "Not Started"),
        ("Docker & Container Internals", "Systems & Networks", 3, 5, 5, "Isolate processes with Linux cgroups and namespaces", "Liz Rice Containers from Scratch", "Manual cgroup Sandbox", "Not Started"),
        ("Kubernetes / K3s Orchestration", "Systems & Networks", 2, 5, 5, "Deploy multi-node K3s cluster with ingress", "Linux Foundation LFS156x (Free Audit)", "K3s Edge Node Cluster", "Not Started"),
        ("Linux Systems Programming & C/Go", "Systems & Networks", 3, 4, 4, "Write multi-threaded RPC client-server in Go/C", "MIT 6.824 Open Labs", "RPC Go/Python Script", "Not Started"),
        ("Python Scientific Stack (NumPy/SciPy)", "AI & Optimization", 4, 5, 5, "Vectorized data processing and statistical analysis", "Self / Open Research Workflows", "Data Analysis Scripts", "In Progress"),
        ("Edge Computing Architecture (MEC)", "Edge Architecture", 2, 5, 5, "Map ETSI MEC interfaces to 5G SBA functions", "ETSI GS MEC 003 Open Specs", "MEC Taxonomy Whitepaper", "In Progress"),
        ("5G Core & Network Slicing", "Edge Architecture", 2, 4, 5, "Simulate URLLC vs eMBB slice isolation", "EURECOM 5G Course (Free Audit)", "5G Network Slice Model", "Not Started"),
        ("6G Architecture & V2X Concepts", "Edge Architecture", 1, 4, 4, "Analyze ISAC and high-mobility V2X handovers", "Univ of Oulu 6G Flagship (Free)", "Vehicular Handover Model", "Not Started"),
        ("Machine Learning & Model Compression", "AI & Optimization", 3, 5, 5, "Quantize ResNet model to INT8 with PyTorch", "Harvard CS249r TinyML (Free)", "PyTorch Quantization Lab", "Not Started"),
        ("TinyML & Embedded Neural Inference", "AI & Optimization", 2, 4, 4, "Run neural model on TFLite Micro runtime", "Harvard Edge AI Lab (Free)", "Microcontroller Audio Lab", "Not Started"),
        ("Federated Learning (FedAvg/FedProx)", "AI & Optimization", 2, 5, 5, "Simulate FL client aggregation in Flower.ai", "Flower.ai Open Framework", "5-Node FL Simulation", "Not Started"),
        ("Mathematical Optimization (Convex/LP)", "AI & Optimization", 2, 5, 5, "Formulate offloading problem and solve in CVXPY", "Stanford EE364a (Free Book/Lectures)", "CVXPY Offloading Script", "Not Started"),
        ("Reinforcement Learning (MDP/DQN)", "AI & Optimization", 2, 4, 4, "Train Q-learning agent for server load balancing", "David Silver UCL RL (Free)", "RL Edge Scheduler Lab", "Not Started"),
        ("Edge Security & Privacy (TEEs/DP)", "Systems & Networks", 2, 4, 4, "Apply Differential Privacy noise to gradients", "Stanford CS255 / Opacus", "DP-SGD Privacy Script", "Not Started"),
        ("Discrete-Event Simulation (EdgeCloudSim)", "Research & Tools", 1, 5, 5, "Execute 100+ multi-server offloading experiments", "Boğaziçi EdgeCloudSim (Free)", "Capstone Simulation", "Not Started"),
        ("Academic Writing & LaTeX Authoring", "Research & Tools", 3, 5, 5, "Write complete 6-page IEEE format paper", "Stanford SciWrite (Free Audit)", "Capstone IEEE Paper", "Not Started"),
        ("Literature Review & Gap Synthesis", "Research & Tools", 3, 5, 5, "Synthesize 20+ papers and write PhD Proposal", "Academic Open Methodology", "5-Page PhD Proposal", "Not Started")
    ]

    for idx, row in enumerate(skills_data, 5):
        ws8.cell(row=idx, column=1, value=row[0]).alignment = align_left
        ws8.cell(row=idx, column=2, value=row[1]).alignment = align_center
        ws8.cell(row=idx, column=3, value=row[2]).alignment = align_right
        ws8.cell(row=idx, column=4, value=row[3]).alignment = align_right
        
        gap_cell = ws8.cell(row=idx, column=5, value=f"=D{idx}-C{idx}")
        gap_cell.alignment = align_right
        gap_cell.font = font_bold
        
        ws8.cell(row=idx, column=6, value=row[4]).alignment = align_right
        ws8.cell(row=idx, column=7, value=row[5]).alignment = align_left
        ws8.cell(row=idx, column=8, value=row[6]).alignment = align_left
        ws8.cell(row=idx, column=9, value=row[7]).alignment = align_left
        
        status_cell = ws8.cell(row=idx, column=10, value=row[8])
        status_cell.alignment = align_center
        status_cell.font = font_bold

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 11):
            cell = ws8.cell(row=idx, column=c)
            if c != 5 and c != 10:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    skill_widths = {1: 34, 2: 20, 3: 16, 4: 16, 5: 14, 6: 18, 7: 35, 8: 25, 9: 25, 10: 15}
    for col, width in skill_widths.items():
        ws8.column_dimensions[get_column_letter(col)].width = width

    ws8.freeze_panes = "C5"
    print("Skills Matrix sheet created.")

    # =========================================================================
    # SHEET 9: SIMULATION & TOOLS GUIDE (100% Free Open-Source Platforms)
    # =========================================================================
    ws9 = wb.create_sheet(title="Simulation & Tools Guide")
    ws9.views.sheetView[0].showGridLines = True

    ws9.merge_cells("A1:J2")
    ws9["A1"] = "EDGE COMPUTING RESEARCH SIMULATORS, EMULATORS & TESTBEDS (100% FREE & OPEN SOURCE)"
    ws9["A1"].font = font_title
    ws9["A1"].fill = fill_navy_dark
    ws9["A1"].alignment = align_center

    ws9.merge_cells("A3:J3")
    ws9["A3"] = "Critical comparative analysis of 100% free open-source simulators, network emulators, and physical edge testbeds for PhD research."
    ws9["A3"].font = font_subtitle
    ws9["A3"].fill = fill_navy_mid
    ws9["A3"].alignment = align_center

    sim_headers = [
        "Tool / Platform", "Tool Category", "What It Simulates & Models", "Key Strengths & What It Is Good For",
        "Limitations & What It Cannot Model", "Typical Research Applications", "Learning Curve (1-5)",
        "PhD Value & Recommendation", "Official Open-Source Repository", "Recommended Usage Strategy"
    ]

    for col_idx, h in enumerate(sim_headers, 1):
        cell = ws9.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws9.row_dimensions[4].height = 28

    sim_tools_data = [
        ("EdgeCloudSim", "Discrete-Event Edge Simulator",
         "Edge computing environments, mobile device mobility, WLAN/WAN network delays, edge server VM processing, and task offloading policies.",
         "Extremely modular Java codebase built on CloudSim; tailored specifically for edge offloading, mobility modeling, and multi-tier queueing.",
         "Cannot perform packet-level protocol inspection; simplified wireless interference modeling compared to full network simulators.",
         "Computation offloading evaluation, edge server capacity planning, mobile handover delay assessment.",
         3, "Essential for PhD (Top Choice)", "https://github.com/CagataySonmez/EdgeCloudSim",
         "Use as the primary simulation tool for your Capstone project and initial PhD proposal experiments."),
        
        ("iFogSim / iFogSim2", "Fog/Edge Discrete Simulator",
         "Hierarchical Fog-to-Cloud infrastructure, Sense-Compute-Actuate loops, energy consumption, and distributed dataflow DAGs.",
         "Excellent built-in energy consumption models and stream processing DAG placement algorithms across IoT/Fog nodes.",
         "Mobility modeling is relatively primitive in basic version; scalability drops under massive dynamic mobile node counts.",
         "IoT stream analytics placement, energy-aware fog resource scheduling, smart city telemetry.",
         3, "Highly Recommended", "https://github.com/Cloudslab/iFogSim",
         "Use when research explicitly focuses on hierarchical energy modeling and multi-operator IoT stream processing."),
        
        ("CloudSim / CloudSim Plus", "Cloud Infrastructure Simulator",
         "Datacenter virtualization, VM provisioning, host CPU scheduling, power consumption, and storage provisioning.",
         "The global gold-standard foundation for cloud computing research; battle-tested with hundreds of extension modules.",
         "Pure cloud focus; lacks native models for edge device mobility, wireless channel fading, and multi-access edge handovers.",
         "Centralized cloud resource provisioning, datacenter energy optimization, VM migration algorithms.",
         2, "Good for Baselines", "https://github.com/cloudsimplus/cloudsimplus",
         "Understand its architecture because EdgeCloudSim and iFogSim extend it directly."),
        
        ("ns-3 (Network Simulator 3)", "Packet-Level Network Simulator",
         "Discrete-event packet-level network protocols (TCP/IP, 802.11 Wi-Fi, 4G LTE, 5G NR, routing, MAC layer queues).",
         "Extreme realism at physical and link layers; authoritative standard for telecommunications research.",
         "High learning curve (C++/Python); computationally heavy when simulating complex application compute workloads for thousands of nodes.",
         "Joint wireless channel and MEC scheduling, 5G NR Beamforming, URLLC packet latency validation.",
         5, "Essential for Comms PhD", "https://www.nsnam.org/",
         "Essential if your PhD focus is communication-centric MEC; pair with Simu5G for cellular edge."),
        
        ("Simu5G / SimuLTE (OMNeT++)", "5G Cellular MEC Simulator",
         "5G New Radio (NR) User Plane, gNodeB base stations, 5G Core (UPF) MEC data planes, and V2X sidelink communication.",
         "Unmatched accuracy for 5G cellular MEC integration, network slicing QoS, and vehicular communication (V2X).",
         "Requires OMNeT++ IDE environment; steep learning curve for non-telecommunications engineers.",
         "5G MEC UPF placement, vehicular edge computing, URLLC latency bounds.",
         4, "Highly Recommended (5G/6G)", "https://simu5g.org/",
         "Top recommendation if your PhD proposal focuses on 5G/6G cellular edge or autonomous vehicles."),
        
        ("Mininet / Mininet-WiFi", "Network Emulation Framework",
         "Software-defined networking (SDN), OpenFlow switches, Linux network namespaces, and emulated Wi-Fi access points.",
         "Runs real unmodified Linux kernel network stacks and real application binaries; interacts with real SDN controllers (ONOS, Ryu).",
         "Limited to a single machine's resource limits; cannot simulate millions of nodes faster than real-time.",
         "SDN-enabled edge traffic routing, dynamic bandwidth throttling, real-world protocol testing.",
         3, "Highly Recommended (SDN)", "http://mininet.org/",
         "Ideal for prototyping custom SDN routing controllers and validating MQTT under network throttling."),
        
        ("K3s / KubeEdge Testbed", "Real-World Edge Orchestration",
         "Production-grade lightweight Kubernetes clusters running on real hardware (Raspberry Pis, Jetson Nano, x86 mini-PCs).",
         "100% realistic real-world deployment; zero simulation bias. Uncovers OS, kernel, and real hardware bottlenecks.",
         "Hardware cost required; experiments take physical clock time to run; difficult to test 10,000 nodes without cloud emulators.",
         "Validating PhD algorithms in real physical testbeds; final paper empirical validation section.",
         3, "Essential for Systems PhD", "https://k3s.io/",
         "Build a 2-3 node testbed during Months 3-5 to provide bulletproof empirical credibility for your PhD application.")
    ]

    for idx, row in enumerate(sim_tools_data, 5):
        ws9.cell(row=idx, column=1, value=row[0]).alignment = align_left
        ws9.cell(row=idx, column=2, value=row[1]).alignment = align_center
        ws9.cell(row=idx, column=3, value=row[2]).alignment = align_left
        ws9.cell(row=idx, column=4, value=row[3]).alignment = align_left
        ws9.cell(row=idx, column=5, value=row[4]).alignment = align_left
        ws9.cell(row=idx, column=6, value=row[5]).alignment = align_left
        ws9.cell(row=idx, column=7, value=row[6]).alignment = align_right
        
        val_cell = ws9.cell(row=idx, column=8, value=row[7])
        val_cell.alignment = align_center
        val_cell.font = font_bold
        
        url_cell = ws9.cell(row=idx, column=9, value=row[8])
        url_cell.hyperlink = row[8]
        url_cell.font = font_hyperlink
        url_cell.alignment = align_left
        
        ws9.cell(row=idx, column=10, value=row[9]).alignment = align_left

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 11):
            cell = ws9.cell(row=idx, column=c)
            if c != 8 and c != 9:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    sim_widths = {1: 24, 2: 24, 3: 35, 4: 35, 5: 35, 6: 32, 7: 16, 8: 24, 9: 35, 10: 38}
    for col, width in sim_widths.items():
        ws9.column_dimensions[get_column_letter(col)].width = width

    ws9.freeze_panes = "C5"
    print("Simulation & Tools Guide sheet created.")

    # =========================================================================
    # SHEET 10: RECOMMENDED PATH (100% Strictly Free)
    # =========================================================================
    ws10 = wb.create_sheet(title="Recommended Path")
    ws10.views.sheetView[0].showGridLines = True

    ws10.merge_cells("A1:H2")
    ws10["A1"] = "CURATED PhD LEARNING PATHWAY — 100% STRICTLY FREE OPEN-ACCESS"
    ws10["A1"].font = font_title
    ws10["A1"].fill = fill_navy_dark
    ws10["A1"].alignment = align_center

    ws10.merge_cells("A3:H3")
    ws10["A3"] = "Zero Paywalls. Eliminates cognitive overload. Strictly separates non-negotiable core mastery from specialized optional topics."
    ws10["A3"].font = font_subtitle
    ws10["A3"].fill = fill_navy_mid
    ws10["A3"].alignment = align_center

    tier_headers = [
        "Selection Tier", "Thematic Focus", "Resource Title", "Institution / Platform",
        "Access / Cost", "Est. Hours", "Why This Resource is Included", "Expected Key Milestone"
    ]

    for col_idx, h in enumerate(tier_headers, 1):
        cell = ws10.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws10.row_dimensions[4].height = 28

    recommended_path_data = [
        # Must Take
        ("Tier 1: Must Take", "Edge Fundamentals", "Linux Foundation: Intro to Edge Computing & Shi (2016) Vision Paper", "LF Edge / IEEE", "100% Free Open Access", 16, "Establishes standard industrial and academic taxonomy without vendor bias.", "Taxonomy Memorandum"),
        ("Tier 1: Must Take", "Networking Depth", "Stanford CS144: Introduction to Computer Networking", "Stanford University", "100% Free OpenCourseWare", 35, "Rigorous graduate-level networking foundation (TCP/IP, latency, buffers).", "Network Latency Lab"),
        ("Tier 1: Must Take", "Distributed Systems", "MIT 6.5840 / 6.824: Distributed Systems (Prof. Robert Morris)", "MIT CSAIL / YouTube", "100% Free Full Materials", 45, "Non-negotiable bedrock for all edge systems research (Raft, RPC, consistency).", "Raft Consensus Lab"),
        ("Tier 1: Must Take", "Cloud-Native Orchestration", "LFS156x: Intro to Kubernetes on Edge with K3s", "Linux Foundation / edX", "100% Free Audit Track", 15, "Directly addresses container orchestration on resource-constrained edge hardware.", "K3s Cluster Deployment"),
        ("Tier 1: Must Take", "MEC Standards", "ETSI GS MEC 003 Architectural Specification & Whitepapers", "ETSI Standards", "100% Free Open Standards", 15, "Authoritative telecommunications framework governing multi-access edge computing.", "MEC Architecture Map"),
        ("Tier 1: Must Take", "Optimization Theory", "Stanford EE364a: Convex Optimization I (Prof. Stephen Boyd)", "Stanford University", "100% Free Book & Lectures", 35, "Mathematical formulation tool for all computation offloading & resource allocation.", "CVXPY Offloading Model"),
        ("Tier 1: Must Take", "Edge AI & TinyML", "Harvard CS249r: TinyML Course Materials & Textbook", "Harvard University Edge AI", "100% Free Open Materials", 30, "Teaches quantization, pruning, and low-power embedded neural inference.", "Quantized Edge AI Model"),
        ("Tier 1: Must Take", "Federated Intelligence", "Flower.ai Framework Tutorials & McMahan FedAvg Paper", "Flower.ai / Cambridge", "100% Free Open Source", 20, "Hands-on implementation of decentralized privacy-preserving edge machine learning.", "Federated Learning Code"),
        ("Tier 1: Must Take", "Simulation Platform", "EdgeCloudSim: Environment for Performance Evaluation", "Boğaziçi University", "100% Free Open Source", 20, "Primary research simulator for generating empirical data for PhD proposal.", "Capstone Simulation"),
        ("Tier 1: Must Take", "Research Methodology", "Writing in the Sciences (Dr. Kristin Sainani)", "Stanford Online / Coursera", "100% Free Audit Track", 15, "Essential guidance on paper structuring, abstract drafting, and proposal defense.", "PhD Research Proposal"),

        # Strongly Recommended
        ("Tier 2: Strongly Recommended", "SDN Networking", "Georgia Tech CS6250: Software-Defined Networking", "Georgia Tech / YouTube", "100% Free Full Lectures", 25, "Dynamic network slicing and programmable control plane mastery.", "Mininet Controller"),
        ("Tier 2: Strongly Recommended", "Data Systems", "Distributed Systems Theory Course (Dr. Martin Kleppmann)", "Cambridge / YouTube", "100% Free Full Course", 20, "Superb coverage of replication, partitioning, transactions, and CRDTs.", "CRDT State Sync Script"),
        ("Tier 2: Strongly Recommended", "5G Telecommunications", "5G Network Architecture and Slicing", "EURECOM / Coursera", "100% Free Audit Track", 20, "Detailed study of 5G SBA, UPF placement, and URLLC QoS specifications.", "5G Slicing Analysis"),
        ("Tier 2: Strongly Recommended", "6G Vision", "Toward 6G: Evolution, Drivers and Key Technologies", "Univ of Oulu 6G Flagship", "100% Free Open Reports", 15, "Visionary telecommunications concepts: ISAC, sub-THz, distributed AI.", "6G Thesis Hypothesis"),
        ("Tier 2: Strongly Recommended", "Reinforcement Learning", "Reinforcement Learning Course (Prof. David Silver)", "UCL & DeepMind / YouTube", "100% Free Full Lectures", 30, "MDPs and Deep Q-Networks for dynamic edge task scheduling.", "RL Load Balancer"),

        # Optional
        ("Tier 3: Optional", "IoT Protocols", "Introduction to the Internet of Things (IoT)", "Curtin University / edX", "100% Free Audit Track", 18, "Good refresher on embedded sensors, actuators, MQTT, and CoAP.", "MQTT Broker Benchmark"),
        ("Tier 3: Optional", "Observability", "Cloud Native Observability with OpenTelemetry", "OpenTelemetry Community", "100% Free Open Docs", 12, "OpenTelemetry and Prometheus distributed tracing for edge telemetry.", "Prometheus Edge Log"),
        ("Tier 3: Optional", "Serverless FaaS", "Serverless Computing and Microservices Patterns", "AWS Serverless Land", "100% Free Open Guides", 12, "FaaS event triggers and cold-start mitigations.", "OpenFaaS Latency Log"),

        # Reference Only
        ("Tier 4: Reference Only", "Network Text", "Computer Networks: A Top-Down Approach (Lectures)", "UMass Amherst", "100% Free Video Lectures", 0, "Keep on hand as the definitive reference for core network protocols.", "Reference Guide"),
        ("Tier 4: Reference Only", "FL Treatise", "Advances and Open Problems in Federated Learning (arXiv)", "Google Research", "100% Free Open Access", 0, "Exhaustive 200-page survey to reference for open problems in privacy.", "Zotero Library Item")
    ]

    for idx, row in enumerate(recommended_path_data, 5):
        tier_cell = ws10.cell(row=idx, column=1, value=row[0])
        tier_cell.alignment = align_center
        tier_cell.font = font_bold
        
        ws10.cell(row=idx, column=2, value=row[1]).alignment = align_left
        ws10.cell(row=idx, column=3, value=row[2]).alignment = align_left
        ws10.cell(row=idx, column=4, value=row[3]).alignment = align_left
        ws10.cell(row=idx, column=5, value=row[4]).alignment = align_left
        ws10.cell(row=idx, column=6, value=row[5]).alignment = align_right
        ws10.cell(row=idx, column=7, value=row[6]).alignment = align_left
        ws10.cell(row=idx, column=8, value=row[7]).alignment = align_left

        if "Tier 1" in row[0]:
            r_fill = PatternFill(start_color="E8F4F8", end_color="E8F4F8", fill_type="solid")
        elif "Tier 2" in row[0]:
            r_fill = PatternFill(start_color="F0F4F8", end_color="F0F4F8", fill_type="solid")
        elif "Tier 3" in row[0]:
            r_fill = fill_zebra
        else:
            r_fill = fill_white

        for c in range(1, 9):
            cell = ws10.cell(row=idx, column=c)
            if c != 1:
                cell.font = font_regular
            cell.fill = r_fill
            cell.border = thin_border

    rec_widths = {1: 22, 2: 22, 3: 38, 4: 28, 5: 24, 6: 12, 7: 42, 8: 25}
    for col, width in rec_widths.items():
        ws10.column_dimensions[get_column_letter(col)].width = width

    ws10.freeze_panes = "C5"
    print("Recommended Path sheet created.")

    # =========================================================================
    # SHEET 11: PhD READINESS ASSESSMENT
    # =========================================================================
    ws11 = wb.create_sheet(title="PhD Readiness Assessment")
    ws11.views.sheetView[0].showGridLines = True

    ws11.merge_cells("A1:G2")
    ws11["A1"] = "PhD APPLICANT READINESS ASSESSMENT & RUBRIC EVALUATION"
    ws11["A1"].font = font_title
    ws11["A1"].fill = fill_navy_dark
    ws11["A1"].alignment = align_center

    ws11.merge_cells("A3:G3")
    ws11["A3"] = "Scoring Rubric: 0=Not Ready | 1=Basic Awareness | 2=Competent B.Eng. | 3=Strong Master's Level | 4=Research Ready (PhD Applicant)"
    ws11["A3"].font = font_subtitle
    ws11["A3"].fill = fill_navy_mid
    ws11["A3"].alignment = align_center

    eval_headers = [
        "Competency Area", "Specific PhD Readiness Assessment Criterion", "Self-Score (0-4)",
        "Required Evidence & Demonstration", "Evaluation Guidance (What 'Research Ready' Looks Like)",
        "Status", "Verification Notes & Action Items"
    ]

    for col_idx, h in enumerate(eval_headers, 1):
        cell = ws11.cell(row=4, column=col_idx, value=h)
        cell.font = font_tbl_header
        cell.fill = fill_navy_dark
        cell.alignment = align_header
        cell.border = header_border
    ws11.row_dimensions[4].height = 28

    readiness_criteria = [
        ("Edge Foundations", "Explain Edge Computing clearly and why it is physically and economically necessary", 4, "1-Page Taxonomy Memorandum", "Can articulate latency speed-of-light limits, backhaul bandwidth bottlenecks, and data privacy drivers without vague buzzwords.", "Achieved", "Fully articulated in Month 1"),
        ("Edge Foundations", "Differentiate Edge vs Cloud vs Fog vs Cloudlets vs MEC with precise architectural distinctions", 4, "Comparative Taxonomy Architecture Map", "Can explain standard bodies (ETSI MEC vs OpenFog vs CNCF) and exact network tier placements.", "Achieved", "Diagrammed in Month 1"),
        ("Edge Foundations", "Explain device-edge-cloud hierarchical interaction and resource discovery models", 3, "Multi-tier Dataflow Simulation Script", "Can describe how edge brokers register resources, handle DNS/IP routing, and offload to cloud.", "In Progress", "Refining in Month 3"),
        ("Systems & Consensus", "Explain distributed consensus (Paxos, Raft) and why it is challenging across edge nodes", 3, "Raft State Machine Implementation", "Can explain why network partitions and high round-trip times complicate quorum formation in edge clusters.", "In Progress", "Completing in Month 2"),
        ("Cloud-Native Systems", "Explain container orchestration (K8s/K3s) and edge worker autonomy during disconnection", 3, "2-Node K3s Cluster Deployment", "Can explain how KubeEdge and K3s handle offline node operation and reconcile desired vs actual state.", "Not Started", "Scheduled for Month 3"),
        ("Telecommunications", "Explain 5G/6G Core, Service-Based Architecture (SBA), UPF placement, and Network Slicing", 3, "5G Slicing & UPF Case Study", "Can explain how 3GPP User Plane Functions integrate with ETSI MEC platforms to guarantee URLLC latency.", "Not Started", "Scheduled for Month 4"),
        ("Optimization Theory", "Formulate computation offloading and resource allocation mathematically (Convex/LP/DRL)", 3, "CVXPY Offloading Code & Proof", "Can formulate multi-variable cost functions (energy + delay), identify constraints, and prove NP-hardness.", "Not Started", "Scheduled for Month 4"),
        ("Edge AI / Intelligence", "Explain Edge AI trade-offs, model compression (quantization/pruning), and embedded inference", 3, "INT8 Quantized Neural Model Report", "Can explain post-training quantization vs quantization-aware training and memory bandwidth limits on NPUs.", "Not Started", "Scheduled for Month 5"),
        ("Federated Learning", "Explain Federated Learning (FedAvg), client drift under non-IID data, and communication costs", 3, "Flower.ai 5-Node FL Simulation", "Can explain why heterogeneous client updates diverge and how gradient compression / FedProx mitigates drift.", "Not Started", "Scheduled for Month 5"),
        ("Edge Security & Privacy", "Explain Edge attack surfaces, Trusted Execution Environments (TEEs), and Differential Privacy", 3, "Differential Privacy Python Lab", "Can explain ARM TrustZone enclaves, secure aggregation in FL, and epsilon-delta privacy budgets.", "Not Started", "Scheduled for Month 5"),
        ("Simulation Competence", "Set up and execute discrete-event simulations in EdgeCloudSim / ns-3 with realistic parameters", 3, "EdgeCloudSim Benchmark Run Data", "Can configure mobility models, network delay distributions, CPU task loads, and extract statistical results.", "Not Started", "Scheduled for Month 6"),
        ("Research Methodology", "Read top-tier Edge Computing papers and rapidly extract RQs, methodologies, and limitations", 4, "15+ Completed Paper Reviews in Tracker", "Can critically dissect IEEE/ACM papers, identify unstated assumptions, and spot methodological flaws.", "In Progress", "Ongoing weekly task"),
        ("Research Methodology", "Identify genuine open research gaps in current Edge Computing state-of-the-art literature", 3, "Research Idea Bank Entries", "Can distinguish incremental parameter tweaks from significant, publishable scientific research questions.", "In Progress", "4 RQs logged in Idea Bank"),
        ("Research Methodology", "Design a rigorous scientific experiment with control baselines and appropriate statistical metrics", 3, "Capstone Experimental Plan", "Can establish proper independent/dependent variables, repeated trials, confidence intervals, and p-values.", "Not Started", "Scheduled for Month 6"),
        ("Research Methodology", "Write a coherent, academically rigorous PhD Research Proposal in standard LaTeX template", 3, "5-Page PhD Proposal Draft", "Proposal contains compelling motivation, precise problem statement, novel methodology, and realistic timeline.", "Not Started", "Scheduled for Month 6"),
        ("Academic Presentation", "Defend proposed research methodology and articulate academic contributions clearly", 3, "Recorded Mock Proposal Presentation", "Can confidently answer probing questions regarding scalability, feasibility, and baseline comparison.", "Not Started", "Scheduled for Month 6")
    ]

    for idx, row in enumerate(readiness_criteria, 5):
        ws11.cell(row=idx, column=1, value=row[0]).alignment = align_left
        ws11.cell(row=idx, column=2, value=row[1]).alignment = align_left
        
        score_cell = ws11.cell(row=idx, column=3, value=row[2])
        score_cell.alignment = align_center
        score_cell.font = font_bold
        
        ws11.cell(row=idx, column=4, value=row[3]).alignment = align_left
        ws11.cell(row=idx, column=5, value=row[4]).alignment = align_left
        
        status_cell = ws11.cell(row=idx, column=6, value=row[5])
        status_cell.alignment = align_center
        status_cell.font = font_bold
        
        ws11.cell(row=idx, column=7, value=row[6]).alignment = align_left

        row_fill = fill_zebra if idx % 2 == 0 else fill_white
        for c in range(1, 8):
            cell = ws11.cell(row=idx, column=c)
            if c != 3 and c != 6:
                cell.font = font_regular
            cell.fill = row_fill
            cell.border = thin_border

    summary_row = len(readiness_criteria) + 5
    ws11.merge_cells(start_row=summary_row, start_column=1, end_row=summary_row, end_column=2)
    ws11.cell(row=summary_row, column=1, value="OVERALL PhD READINESS COMPOSITE INDEX (Average Score)").alignment = align_left
    ws11.cell(row=summary_row, column=1).font = font_bold
    ws11.cell(row=summary_row, column=1).fill = fill_header_accent
    
    avg_score_cell = ws11.cell(row=summary_row, column=3, value=f"=AVERAGE(C5:C{summary_row-1})")
    avg_score_cell.alignment = align_center
    avg_score_cell.font = font_kpi_num
    avg_score_cell.number_format = "0.00"
    avg_score_cell.fill = fill_header_accent
    
    ws11.merge_cells(start_row=summary_row, start_column=4, end_row=summary_row, end_column=7)
    ws11.cell(row=summary_row, column=4, value=f'=IF(C{summary_row}>=3.5, "EXCEPTIONAL — Fully Research Ready for Top-Tier PhD", IF(C{summary_row}>=2.8, "STRONG — Highly Competitive PhD Applicant with Strong Foundations", "DEVELOPING — Continue Progressing Through Curriculum"))').alignment = align_left
    ws11.cell(row=summary_row, column=4).font = font_bold
    ws11.cell(row=summary_row, column=4).fill = fill_header_accent

    for c in range(1, 8):
        ws11.cell(row=summary_row, column=c).border = total_border

    eval_widths = {1: 22, 2: 38, 3: 16, 4: 32, 5: 42, 6: 15, 7: 35}
    for col, width in eval_widths.items():
        ws11.column_dimensions[get_column_letter(col)].width = width

    ws11.freeze_panes = "C5"
    print("PhD Readiness Assessment sheet created.")

    # =========================================================================
    # APPLY DATA VALIDATIONS & CONDITIONAL FORMATTING
    # =========================================================================
    print("Applying Data Validations and Conditional Formatting...")

    ws2.add_data_validation(dv_status)
    dv_status.add("V4:V35")
    
    ws3.add_data_validation(dv_status)
    dv_status.add("N4:N27")
    
    ws4.add_data_validation(dv_goal)
    dv_goal.add("O5:O28")
    
    ws5.add_data_validation(dv_status)
    dv_status.add("M4:M25")
    
    ws6.add_data_validation(dv_read_status)
    dv_read_status.add("I5:I25")
    
    ws6.add_data_validation(dv_yesno)
    dv_yesno.add("J5:L25")
    
    ws7.add_data_validation(dv_priority)
    dv_priority.add("N5:N25")
    
    ws7.add_data_validation(dv_idea_status)
    dv_idea_status.add("O5:O25")
    
    ws8.add_data_validation(dv_skill_status)
    dv_skill_status.add("J5:J30")

    green_fill = PatternFill(start_color=FILL_GREEN, end_color=FILL_GREEN, fill_type="solid")
    green_font = Font(name="Calibri", size=10, bold=True, color=FONT_GREEN)
    rule_completed = CellIsRule(operator='equal', formula=['"Completed"'], stopIfTrue=True, fill=green_fill, font=green_font)
    rule_yes = CellIsRule(operator='equal', formula=['"Yes"'], stopIfTrue=True, fill=green_fill, font=green_font)
    rule_achieved = CellIsRule(operator='equal', formula=['"Achieved"'], stopIfTrue=True, fill=green_fill, font=green_font)
    
    yellow_fill = PatternFill(start_color=FILL_YELLOW, end_color=FILL_YELLOW, fill_type="solid")
    yellow_font = Font(name="Calibri", size=10, bold=True, color=FONT_YELLOW)
    rule_in_progress = CellIsRule(operator='equal', formula=['"In Progress"'], stopIfTrue=True, fill=yellow_fill, font=yellow_font)
    rule_partially = CellIsRule(operator='equal', formula=['"Partially"'], stopIfTrue=True, fill=yellow_fill, font=yellow_font)
    rule_investigating = CellIsRule(operator='equal', formula=['"Investigating"'], stopIfTrue=True, fill=yellow_fill, font=yellow_font)

    blue_fill = PatternFill(start_color=FILL_BLUE, end_color=FILL_BLUE, fill_type="solid")
    blue_font = Font(name="Calibri", size=10, bold=True, color=FONT_BLUE)
    rule_high = CellIsRule(operator='equal', formula=['"High"'], stopIfTrue=True, fill=blue_fill, font=blue_font)

    red_fill = PatternFill(start_color=FILL_RED, end_color=FILL_RED, fill_type="solid")
    red_font = Font(name="Calibri", size=10, bold=True, color=FONT_RED)
    rule_not_started = CellIsRule(operator='equal', formula=['"Not Started"'], stopIfTrue=True, fill=red_fill, font=red_font)
    rule_no = CellIsRule(operator='equal', formula=['"No"'], stopIfTrue=True, fill=red_fill, font=red_font)

    for ws, col_range in [
        (ws2, "V4:V35"),
        (ws3, "N4:N27"),
        (ws5, "M4:M25"),
        (ws8, "J5:J30"),
        (ws11, "F5:F25")
    ]:
        ws.conditional_formatting.add(col_range, rule_completed)
        ws.conditional_formatting.add(col_range, rule_in_progress)
        ws.conditional_formatting.add(col_range, rule_not_started)
        ws.conditional_formatting.add(col_range, rule_achieved)

    ws4.conditional_formatting.add("O5:O28", rule_yes)
    ws4.conditional_formatting.add("O5:O28", rule_partially)
    ws4.conditional_formatting.add("O5:O28", rule_no)

    ws6.conditional_formatting.add("I5:I25", rule_yes)
    ws6.conditional_formatting.add("I5:I25", rule_in_progress)
    ws6.conditional_formatting.add("I5:I25", rule_no)
    
    ws7.conditional_formatting.add("N5:N25", rule_high)
    ws7.conditional_formatting.add("O5:O25", rule_investigating)

    # =========================================================================
    # ADDITIVE MODULE HOOK: HONG KONG PhD SUPERVISOR INTELLIGENCE
    # =========================================================================
    if enable_hk_module:
        try:
            import sys
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            if "/Users/obaromoses/Desktop/AlertMe" not in sys.path:
                sys.path.insert(0, "/Users/obaromoses/Desktop/AlertMe")

            from hk_supervisor_intel.config import HONG_KONG_SUPERVISOR_INTELLIGENCE_ENABLED
            if HONG_KONG_SUPERVISOR_INTELLIGENCE_ENABLED:
                print("Integrating Additive Module: Hong Kong PhD Supervisor Intelligence...")
                from hk_supervisor_intel.excel_extension import add_hong_kong_module_sheets
                add_hong_kong_module_sheets(wb)
        except Exception as e:
            print(f"Warning: Hong Kong PhD module integration skipped ({e}). Preserving core curriculum.")

    wb.remove(default_sheet)
    wb.save(output_filename)
    print(f"100% Free Open-Access Workbook successfully saved to: {output_filename}")
    return output_filename

if __name__ == "__main__":
    import sys
    disable_hk = "--disable-hk-module" in sys.argv
    create_edge_computing_workbook(enable_hk_module=not disable_hk)
