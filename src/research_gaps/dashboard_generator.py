"""Generates dashboard data and markdown reports for the research gap analysis module."""

import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.storage.state_manager import _atomic_write_json
from src.research_gaps.models import ProblemStatus
from src.research_gaps.state_manager import ResearchGapStateManager
from src.utils.logger import logger

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"
REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"


class ResearchGapDashboardGenerator:
    """Exports structured data for the GitHub Pages research-gap dashboard."""

    def __init__(self, state_manager: Optional[ResearchGapStateManager] = None):
        self.state_manager = state_manager or ResearchGapStateManager()
        self.docs_dir = DOCS_DIR
        self.docs_data_dir = self.docs_dir / "data"
        self.docs_data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir = REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_dashboard_data(
        self,
        problems: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        directions: List[Dict[str, Any]],
        papers: List[Dict[str, Any]],
        feasibility_map: Dict[str, Any],
        supervisor_map: Dict[str, Any],
        link_results: Dict[str, Any],
        pipeline_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Builds the full dashboard JSON payload."""
        today = datetime.date.today().isoformat()
        meta = pipeline_meta or {}

        new_count = sum(1 for p in problems if p.get("status") == ProblemStatus.NEW)
        promising_count = sum(1 for p in problems if p.get("status") == ProblemStatus.PROMISING)
        shortlisted_count = sum(1 for p in problems if p.get("status") == ProblemStatus.SHORTLISTED)
        investigating_count = sum(1 for p in problems if p.get("status") == ProblemStatus.INVESTIGATING)

        verified_links = sum(1 for v in link_results.values() if isinstance(v, dict) and v.get("link_status") == "valid")
        broken_links = sum(1 for v in link_results.values() if isinstance(v, dict) and v.get("link_status") == "broken")

        # ── Embed full Citation objects from papers directly into problems ────
        citations_map: Dict[str, Dict[str, Any]] = {}
        for p in papers:
            pid = p.get("paper_id") or p.get("id")
            if pid:
                doi = p.get("doi") or None
                url = p.get("url") or ""
                link = f"https://doi.org/{doi}" if doi else url
                authors = p.get("authors") or []
                year = p.get("year") or 0
                title = p.get("title") or "Untitled"
                venue = p.get("venue") or ""

                if len(authors) > 3:
                    author_str = f"{authors[0]} et al."
                elif len(authors) == 2:
                    author_str = f"{authors[0]} & {authors[1]}"
                elif len(authors) == 1:
                    author_str = authors[0]
                else:
                    author_str = "Unknown authors"
                year_str = str(year) if year else "n.d."
                citation_str = f"{author_str} ({year_str}). {title.rstrip('.')}."
                if venue:
                    citation_str += f" {venue.rstrip('.')}."

                citations_map[pid] = {
                    "paper_id": pid,
                    "doi": doi,
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "venue": venue,
                    "url": url,
                    "link": link,
                    "citation_string": citation_str,
                }

        # ── Enrich problems with supervisor matches and embedded citations ──
        supervisor_list: List[Dict[str, Any]] = []
        supervisor_stats: Dict[str, Any] = {
            "total_matches": 0,
            "by_country": {},
            "by_area": {},
        }

        for prob_dict in problems:
            prob_id = prob_dict.get("id", "")
            prob_matches = supervisor_map.get(prob_id, [])
            prob_dict["supervisor_matches"] = prob_matches

            # Embed citations directly inside each problem record
            prob_citations = []
            for pid in prob_dict.get("supporting_papers", []):
                if pid in citations_map:
                    prob_citations.append(citations_map[pid])
                else:
                    prob_citations.append({
                        "paper_id": pid,
                        "doi": None,
                        "title": pid,
                        "authors": [],
                        "year": 0,
                        "venue": "",
                        "url": "",
                        "link": "",
                        "citation_string": pid,
                    })
            prob_dict["citations"] = prob_citations

            for m in prob_matches:
                if not isinstance(m, dict):
                    continue
                supervisor_stats["total_matches"] += 1
                country = m.get("country", "Unknown")
                supervisor_stats["by_country"][country] = supervisor_stats["by_country"].get(country, 0) + 1
                area = prob_dict.get("research_area", "Unknown")
                supervisor_stats["by_area"][area] = supervisor_stats["by_area"].get(area, 0) + 1

                # Add to flat supervisor list for the supervisors tab
                supervisor_list.append({
                    "problem_id": prob_id,
                    "problem_statement": prob_dict.get("problem_statement", "")[:120],
                    "research_area": prob_dict.get("research_area", ""),
                    **m,
                })

        payload = {
            "meta": {
                "last_updated": meta.get("last_updated", today),
                "last_link_verification": meta.get("last_link_verification", today),
                "total_papers": len(papers),
                "total_problems": len(problems),
                "total_clusters": len(clusters),
                "total_directions": len(directions),
                "new_problems": new_count,
                "investigating_problems": investigating_count,
                "promising_problems": promising_count,
                "shortlisted_problems": shortlisted_count,
                "verified_links": verified_links,
                "broken_links": broken_links,
                "total_supervisor_matches": supervisor_stats["total_matches"],
                "supervisor_matches_by_country": supervisor_stats["by_country"],
            },
            "problems": problems,
            "clusters": clusters,
            "directions": directions,
            "papers": papers[:200],
            "feasibility": feasibility_map,
            "supervisors": supervisor_map,
            "supervisor_list": supervisor_list,
            "link_verification": link_results,
        }
        return payload

    def write_dashboard_data(self, payload: Dict[str, Any]) -> None:
        """Writes dashboard JSON files to docs/data/ for GitHub Pages consumption."""
        try:
            # Individual data files for the dashboard
            _atomic_write_json(self.docs_data_dir / "research_problems.json", payload.get("problems", []))
            _atomic_write_json(self.docs_data_dir / "research_gap_clusters.json", payload.get("clusters", []))
            _atomic_write_json(self.docs_data_dir / "research_questions.json", payload.get("directions", []))
            _atomic_write_json(self.docs_data_dir / "professor_matches.json", payload.get("supervisor_list", []))
            # Combined payload for single-fetch dashboard loading
            _atomic_write_json(self.docs_data_dir / "research_gap_data.json", payload)
            logger.info(f"Dashboard data written to {self.docs_data_dir}")
        except Exception as e:
            logger.error(f"Failed to write dashboard data: {e}")

    def generate_report_markdown(
        self,
        problems: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        directions: List[Dict[str, Any]],
        feasibility_map: Dict[str, Any],
        supervisor_map: Dict[str, Any],
    ) -> str:
        """Generates a Markdown report summarizing the research gap analysis."""
        lines = [
            "# Research Gap Analysis Report",
            "",
            f"*Generated: {datetime.date.today().isoformat()}*",
            "",
            f"**Papers analyzed:** {sum(len(p.get('supporting_papers', [])) for p in problems)}  ",
            f"**Research problems identified:** {len(problems)}  ",
            f"**Research-gap clusters:** {len(clusters)}  ",
            f"**Candidate research directions:** {len(directions)}  ",
            "",
            "---",
            "",
            "## Research Problems",
            "",
        ]

        # Group by status
        for status in [ProblemStatus.SHORTLISTED, ProblemStatus.PROMISING, ProblemStatus.INVESTIGATING, ProblemStatus.NEW]:
            status_problems = [p for p in problems if p.get("status") == status]
            if not status_problems:
                continue
            lines.append(f"### {status.capitalize()} ({len(status_problems)})")
            lines.append("")
            for p in status_problems:
                lines.append(f"#### {p.get('problem_statement', 'Unknown')}")
                lines.append(f"- **Research Area:** {p.get('research_area', 'N/A')}")
                lines.append(f"- **Cluster:** {p.get('problem_cluster', 'N/A')}")
                lines.append(f"- **Frequency:** {p.get('frequency', 0)}")
                lines.append(f"- **Status:** {p.get('status', 'new')}")

                if p.get("known_limitations"):
                    lines.append("- **Known Limitations:**")
                    for lim in p["known_limitations"][:5]:
                        lim_text = lim.get("claim_text", "") if isinstance(lim, dict) else str(lim)
                        lines.append(f"  - {lim_text}")

                if p.get("unresolved_questions"):
                    lines.append("- **Unresolved Questions:**")
                    for q in p["unresolved_questions"][:5]:
                        q_text = q.get("claim_text", "") if isinstance(q, dict) else str(q)
                        lines.append(f"  - {q_text}")

                if p.get("citations"):
                    lines.append("- **Supporting Literature:**")
                    for cit in p["citations"][:5]:
                        c_str = cit.get("citation_string") or cit.get("title", "")
                        c_link = cit.get("link") or ""
                        lines.append(f"  - [{c_str}]({c_link})" if c_link else f"  - {c_str}")

                # Feasibility
                feas = feasibility_map.get(p.get("id", ""), {})
                if feas:
                    lines.append(f"- **Novelty:** {feas.get('novelty', 'unknown')} ({feas.get('novelty_evidence', '')})")
                    lines.append(f"- **Feasibility:** {feas.get('feasibility', 'unknown')} ({feas.get('feasibility_evidence', '')})")
                    lines.append(f"- **Publication Potential:** {feas.get('publication_potential', 'unknown')} ({feas.get('publication_evidence', '')})")
                    lines.append(f"- **PhD Depth:** {feas.get('phd_depth', 'unknown')} ({feas.get('phd_depth_evidence', '')})")

                lines.append("")

        # Clusters
        lines.extend(["---", "", "## Research Gap Clusters", ""])
        for c in clusters:
            lines.append(f"### {c.get('name', 'Unknown Cluster')}")
            lines.append(f"- **Research Area:** {c.get('research_area', 'N/A')}")
            lines.append(f"- **Problems:** {len(c.get('supporting_problems', []))}")
            lines.append(f"- **Papers:** {len(c.get('supporting_papers', []))}")
            if c.get("recurring_limitations"):
                lines.append("- **Recurring Limitations:**")
                for lim in c["recurring_limitations"][:5]:
                    lines.append(f"  - {lim}")
            if c.get("open_questions"):
                lines.append("- **Open Questions:**")
                for q in c["open_questions"][:5]:
                    lines.append(f"  - {q}")
            lines.append("")

        # Directions
        lines.extend(["---", "", "## Candidate Research Directions", ""])
        for d in directions:
            lines.append(f"### {d.get('research_problem', 'Unknown')}")
            lines.append(f"- **Gap:** {d.get('research_gap', 'N/A')}")
            if d.get("research_questions"):
                lines.append("- **Research Questions:**")
                for rq in d["research_questions"]:
                    lines.append(f"  1. {rq}")
            lines.append(f"- **Potential Contribution:** {d.get('potential_contribution', 'N/A')}")
            lines.append(f"- **Possible Methodology:** {d.get('possible_methodology', 'N/A')}")
            lines.append(f"- **Evidence Supported:** {'Yes' if d.get('evidence_supported') else 'Speculative'}")
            lines.append("")

        return "\n".join(lines)

    def write_report(self, content: str) -> None:
        """Writes the Markdown report to the reports directory."""
        report_path = self.reports_dir / "research_gap_report.md"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Research gap report written to {report_path}")
        except Exception as e:
            logger.error(f"Failed to write report: {e}")
