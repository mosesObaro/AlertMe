"""Research Gap Analysis pipeline orchestrator."""

import datetime
from typing import Dict, Any, List, Optional
from src.utils.config_loader import ConfigManager, load_yaml_file
from src.utils.logger import logger
from src.models import ResearchItem
from src.collectors.arxiv import ArxivCollector
from src.collectors.openalex import OpenAlexCollector
from src.collectors.crossref import CrossrefCollector
from src.collectors.semantic_scholar import SemanticScholarCollector
from src.deduplication.deduplicator import Deduplicator
from src.research_gaps.models import (
    ExtractedPaperInfo, ResearchProblem, ResearchGapCluster,
    CandidateResearchDirection, FeasibilityAssessment, SupervisorMatch,
    ProblemStatus,
)
from src.research_gaps.gap_extractor import GapExtractor
from src.research_gaps.problem_tracker import ProblemTracker
from src.research_gaps.clustering import ProblemClusterer
from src.research_gaps.question_generator import ResearchQuestionGenerator
from src.research_gaps.supervisor_matcher import SupervisorMatcher
from src.research_gaps.feasibility import FeasibilityAssessor
from src.research_gaps.link_verifier import LinkVerifier
from src.research_gaps.state_manager import ResearchGapStateManager
from src.research_gaps.dashboard_generator import ResearchGapDashboardGenerator
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


class ResearchGapPipeline:
    """End-to-end pipeline for research gap discovery and PhD topic analysis."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.gap_config = load_yaml_file(CONFIG_DIR / "research_gaps.yaml")
        self.state_manager = ResearchGapStateManager()
        self.deduplicator = Deduplicator()
        self.gap_extractor = GapExtractor()
        self.problem_tracker = ProblemTracker()
        self.clusterer = ProblemClusterer(
            similarity_threshold=self.gap_config.get("clustering", {}).get("similarity_threshold", 0.55),
            min_cluster_size=self.gap_config.get("clustering", {}).get("min_cluster_size", 2),
        )
        self.question_generator = ResearchQuestionGenerator()
        self.supervisor_matcher = SupervisorMatcher()
        self.feasibility_assessor = FeasibilityAssessor()

        lv_cfg = self.gap_config.get("link_verification", {})
        self.link_verifier = LinkVerifier(
            timeout=lv_cfg.get("timeout", 10),
            rate_limit_delay=lv_cfg.get("rate_limit_delay", 0.5),
            retry_attempts=lv_cfg.get("retry_attempts", 2),
        )
        self.dashboard_gen = ResearchGapDashboardGenerator(self.state_manager)

    def _init_collectors(self) -> List:
        """Initialise academic collectors from the research gaps config."""
        collectors = []
        queries = self.gap_config.get("search_queries", {})
        max_results = self.gap_config.get("collection", {}).get("max_results_per_query", 40)

        for q in queries.get("arxiv", []):
            collectors.append(ArxivCollector(
                name=f"ResearchGap arXiv: {q[:50]}",
                query=q,
                max_results=max_results,
            ))
        for q in queries.get("openalex", []):
            collectors.append(OpenAlexCollector(
                name=f"ResearchGap OpenAlex: {q[:50]}",
                search_query=q,
                max_results=max_results,
            ))
        for q in queries.get("crossref", []):
            collectors.append(CrossrefCollector(
                name=f"ResearchGap Crossref: {q[:50]}",
                query=q,
                rows=max_results,
            ))
        for q in queries.get("semantic_scholar", []):
            collectors.append(SemanticScholarCollector(
                name=f"ResearchGap S2: {q[:50]}",
                query=q,
                limit=max_results,
            ))
        return collectors

    def run(self, verify_links: bool = True) -> Dict[str, Any]:
        """Execute the full research gap analysis pipeline."""
        logger.info("=== Starting Research Gap Analysis Pipeline ===")
        start_time = datetime.datetime.now(datetime.timezone.utc)

        # ── 1. Collect literature ─────────────────────────────────────
        logger.info("Step 1: Collecting literature from academic sources")
        collectors = self._init_collectors()
        all_items: List[ResearchItem] = []
        for collector in collectors:
            try:
                items = collector.collect()
                all_items.extend(items)
            except Exception as e:
                logger.error(f"Collector {collector.name} failed: {e}")

        # Also ingest seed literature and historical AlertMe papers
        seed_file = Path(__file__).resolve().parent.parent.parent / "data" / "research_gaps_seed_papers.json"
        if seed_file.exists():
            try:
                import json
                with open(seed_file, "r", encoding="utf-8") as f:
                    seed_data = json.load(f)
                    for item_dict in seed_data:
                        all_items.append(ResearchItem.from_dict(item_dict))
                logger.info(f"Loaded {len(seed_data)} seed papers across target research areas")
            except Exception as e:
                logger.warning(f"Failed to load seed papers: {e}")

        # Ingest from existing alert history if present
        alert_history_file = Path(__file__).resolve().parent.parent.parent / "data" / "alert_history.json"
        if alert_history_file.exists():
            try:
                import json
                with open(alert_history_file, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
                    for h_dict in history_data:
                        if h_dict.get("item_type") in ["paper", "preprint", "survey"] and h_dict.get("abstract"):
                            try:
                                all_items.append(ResearchItem.from_dict(h_dict))
                            except Exception:
                                pass
                logger.info("Loaded papers from AlertMe alert history")
            except Exception as e:
                logger.warning(f"Failed to load alert history: {e}")

        logger.info(f"Collected {len(all_items)} total literature items (live + seed + history)")

        # ── 2. Deduplicate ────────────────────────────────────────────
        logger.info("Step 2: Deduplicating papers")
        unique_items = self.deduplicator.deduplicate(all_items)
        logger.info(f"After deduplication: {len(unique_items)} unique papers")

        # ── 3. Extract research gaps ──────────────────────────────────
        logger.info("Step 3: Extracting research gap information")
        extracted_papers = self.gap_extractor.extract_batch(unique_items)
        logger.info(f"Extracted info from {len(extracted_papers)} papers")

        # ── 4. Update research problem tracker ────────────────────────
        logger.info("Step 4: Updating research problem tracker")
        research_areas = self.gap_config.get("research_areas", [])
        problems = self.problem_tracker.load_problems()

        for paper in extracted_papers:
            if not paper.research_problem:
                continue
            # Determine research area from paper keywords/topics
            area = self._classify_research_area(paper, research_areas)
            self.problem_tracker.add_or_update_problem(paper, area)

        problems = self.problem_tracker.load_problems()
        logger.info(f"Problem tracker now has {len(problems)} problems")

        # ── 5. Cluster research problems ──────────────────────────────
        logger.info("Step 5: Clustering research problems")
        existing_clusters_data = self.state_manager.load_research_gap_clusters()
        existing_clusters = [ResearchGapCluster.from_dict(c) for c in existing_clusters_data]

        problem_objs = [p if isinstance(p, ResearchProblem) else ResearchProblem.from_dict(p) for p in problems]
        new_clusters = self.clusterer.cluster_problems(problem_objs, extracted_papers)
        merged_clusters = self.clusterer.update_clusters(existing_clusters, new_clusters)

        # Assign cluster names back to problems
        cluster_map = {}
        for cl in merged_clusters:
            for pid in cl.supporting_problems:
                cluster_map[pid] = cl.name

        for p in problem_objs:
            if p.id in cluster_map:
                p.problem_cluster = cluster_map[p.id]

        # Save updated problems
        self.problem_tracker.save_problems(problem_objs)
        problems = [p.to_dict() for p in problem_objs]
        clusters = [c.to_dict() for c in merged_clusters]
        logger.info(f"Created {len(merged_clusters)} research gap clusters")

        # ── 6. Generate candidate research directions ─────────────────
        logger.info("Step 6: Generating candidate research directions")
        eligible_problems = [
            p for p in problem_objs
            if p.status in [ProblemStatus.INVESTIGATING, ProblemStatus.PROMISING, ProblemStatus.SHORTLISTED]
        ]
        # If no problems have reached investigating/promising yet, pick the most actionable ones
        if not eligible_problems and problem_objs:
            eligible_problems = [
                p for p in problem_objs
                if p.candidate_methods or p.known_limitations or p.unresolved_questions
            ][:8]
            # Automatically classify high-potential problems with candidate methods + limitations as investigating
            for ep in eligible_problems:
                if ep.candidate_methods and ep.known_limitations:
                    ep.status = ProblemStatus.INVESTIGATING
            self.problem_tracker.save_problems(problem_objs)
            problems = [p.to_dict() for p in problem_objs]

        directions_objs = []
        for ep in eligible_problems:
            try:
                directions_objs.append(self.question_generator.generate_directions(ep, extracted_papers))
            except Exception as e:
                logger.warning(f"Failed to generate directions for {ep.id}: {e}")
        directions = [d.to_dict() for d in directions_objs]
        logger.info(f"Generated {len(directions)} candidate research directions")

        # ── 7. Match supervisors ──────────────────────────────────────
        logger.info("Step 7: Matching supervisors to research problems")
        supervisor_map_raw = self.supervisor_matcher.match_all(problem_objs)
        supervisor_map = {pid: [s.to_dict() for s in slist] for pid, slist in supervisor_map_raw.items()}
        logger.info(f"Matched supervisors for {len(supervisor_map)} problems")

        # ── 8. Assess feasibility ─────────────────────────────────────
        logger.info("Step 8: Assessing PhD feasibility")
        feasibility_map_raw = self.feasibility_assessor.assess_batch(
            problem_objs, extracted_papers, supervisor_map_raw
        )
        feasibility_map = {pid: f.to_dict() for pid, f in feasibility_map_raw.items()}

        # ── 9. Verify links ───────────────────────────────────────────
        link_results: Dict[str, Any] = {}
        if verify_links:
            logger.info("Step 9: Verifying external links")
            try:
                supervisor_match_objs = []
                for slist in supervisor_map_raw.values():
                    supervisor_match_objs.extend(slist)
                link_results_raw = self.link_verifier.verify_all_links(
                    extracted_papers, problem_objs, supervisor_match_objs
                )
                link_results = {url: r.to_dict() for url, r in link_results_raw.items()}
                logger.info(f"Verified {len(link_results)} links")
            except Exception as e:
                logger.warning(f"Link verification failed: {e}")
        else:
            logger.info("Step 9: Link verification skipped")

        # ── 10. Persist state ─────────────────────────────────────────
        logger.info("Step 10: Persisting state")
        papers_data = [p.to_dict() for p in extracted_papers]

        self.state_manager.save_research_problems(problems)
        self.state_manager.save_research_gap_clusters(clusters)
        self.state_manager.save_research_questions(directions)
        self.state_manager.save_extracted_papers(papers_data)
        self.state_manager.save_feasibility_assessments(feasibility_map)
        self.state_manager.save_supervisor_matches(supervisor_map)
        if link_results:
            self.state_manager.save_link_verification(link_results)

        end_time = datetime.datetime.now(datetime.timezone.utc)
        pipeline_meta = {
            "last_updated": end_time.isoformat(),
            "last_link_verification": end_time.isoformat() if verify_links else "",
            "execution_duration_seconds": (end_time - start_time).total_seconds(),
            "raw_items_collected": len(all_items),
            "unique_papers": len(unique_items),
            "extracted_papers": len(extracted_papers),
            "total_problems": len(problems),
            "total_clusters": len(clusters),
            "total_directions": len(directions),
            "new_problems": sum(1 for p in problems if p.get("status") == ProblemStatus.NEW),
            "promising_problems": sum(1 for p in problems if p.get("status") == ProblemStatus.PROMISING),
            "shortlisted_problems": sum(1 for p in problems if p.get("status") == ProblemStatus.SHORTLISTED),
        }
        self.state_manager.save_pipeline_metadata(pipeline_meta)

        # ── 11. Generate dashboard + report ───────────────────────────
        logger.info("Step 11: Generating dashboard data and report")
        payload = self.dashboard_gen.generate_dashboard_data(
            problems=problems,
            clusters=clusters,
            directions=directions,
            papers=papers_data,
            feasibility_map=feasibility_map,
            supervisor_map=supervisor_map,
            link_results=link_results,
            pipeline_meta=pipeline_meta,
        )
        self.dashboard_gen.write_dashboard_data(payload)

        report_md = self.dashboard_gen.generate_report_markdown(
            problems=problems,
            clusters=clusters,
            directions=directions,
            feasibility_map=feasibility_map,
            supervisor_map=supervisor_map,
        )
        self.dashboard_gen.write_report(report_md)

        logger.info("=== Research Gap Analysis Pipeline Finished ===")
        return pipeline_meta

    def _classify_research_area(self, paper: ExtractedPaperInfo, areas: List[str]) -> str:
        """Determine the best-matching research area for a paper."""
        text = f"{paper.title} {paper.abstract} {' '.join(paper.keywords)}".lower()
        best_area = areas[0] if areas else "Edge Computing"
        best_score = 0

        for area in areas:
            area_lower = area.lower()
            tokens = area_lower.split()
            score = sum(1 for t in tokens if t in text)
            # Bonus for exact phrase match
            if area_lower in text:
                score += 3
            if score > best_score:
                best_score = score
                best_area = area

        return best_area
