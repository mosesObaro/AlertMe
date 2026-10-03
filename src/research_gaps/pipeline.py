"""Research Gap Analysis pipeline orchestrator.

Implements the 4-step deterministic rule-based algorithm for PhD topic discovery:
STEP 1: Corpus of at least 20 highly relevant recent papers per professor
STEP 2: Potential unsolved problems & solution testing
STEP 3: PhD qualification rubric (Dublin Descriptors Level 8)
STEP 4: IEEE-structured research statement generation

Preserves legacy flow via --mode legacy.
"""

import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.utils.config_loader import ConfigManager, load_yaml_file
from src.utils.logger import logger
from src.models import ResearchItem
from src.deduplication.deduplicator import Deduplicator
from src.storage.state_manager import _atomic_write_json
from src.research_gaps.models import (
    ExtractedPaperInfo,
    ResearchProblem,
    ResearchGapCluster,
    CandidateResearchDirection,
    FeasibilityAssessment,
    SupervisorMatch,
    ProblemStatus,
    ProfessorCorpus,
    UnsolvedProblemCluster,
    PhDQualificationResult,
    IEEEResearchStatement,
)
from src.research_gaps.corpus_builder import CorpusBuilder, ProfessorRegistry
from src.research_gaps.unsolved_extractor import UnsolvedProblemExtractor
from src.research_gaps.phd_assessor import PhDQualificationAssessor
from src.research_gaps.statement_generator import IEEEResearchStatementGenerator
from src.research_gaps.dashboard_generator import ResearchGapDashboardGenerator
from src.research_gaps.state_manager import ResearchGapStateManager
from src.research_gaps.gap_extractor import GapExtractor
from src.research_gaps.problem_tracker import ProblemTracker
from src.research_gaps.clustering import ProblemClusterer
from src.research_gaps.question_generator import ResearchQuestionGenerator
from src.research_gaps.supervisor_matcher import SupervisorMatcher
from src.research_gaps.feasibility import FeasibilityAssessor
from src.research_gaps.link_verifier import LinkVerifier

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "data"


class ResearchGapPipeline:
    """End-to-end pipeline for research gap discovery and PhD topic analysis."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.gap_config = load_yaml_file(CONFIG_DIR / "research_gaps.yaml")
        self.state_manager = ResearchGapStateManager()
        self.deduplicator = Deduplicator()
        self.registry = ProfessorRegistry(config=self.gap_config)
        self.corpus_builder = CorpusBuilder(config=self.gap_config)
        self.unsolved_extractor = UnsolvedProblemExtractor(config=self.gap_config)
        self.phd_assessor = PhDQualificationAssessor(config=self.gap_config)
        self.statement_generator = IEEEResearchStatementGenerator()
        self.dashboard_gen = ResearchGapDashboardGenerator(self.state_manager)

        # Legacy components
        self.gap_extractor = GapExtractor(config=self.gap_config)
        self.problem_tracker = ProblemTracker(config=self.gap_config)
        self.clusterer = ProblemClusterer(
            similarity_threshold=self.gap_config.get("clustering", {}).get("similarity_threshold", 0.55),
            min_cluster_size=self.gap_config.get("clustering", {}).get("min_cluster_size", 2),
        )
        self.question_generator = ResearchQuestionGenerator()
        self.supervisor_matcher = SupervisorMatcher()
        self.feasibility_assessor = FeasibilityAssessor(config=self.gap_config)

    def run(
        self,
        mode: str = "4step",
        professor_name: Optional[str] = None,
        batch_size: int = 10,
        verify_links: bool = True,
    ) -> Dict[str, Any]:
        """Runs the research gap pipeline. Default mode is '4step'."""
        if mode == "legacy":
            return self._run_legacy(verify_links=verify_links)
        return self._run_4step(professor_name=professor_name, batch_size=batch_size)

    def _run_4step(self, professor_name: Optional[str] = None, batch_size: int = 10) -> Dict[str, Any]:
        """Executes the 4-step algorithm per professor."""
        logger.info("=== Starting 4-Step PhD Topic Discovery Pipeline ===")
        start_time = datetime.datetime.now(datetime.timezone.utc)

        # Select rotating batch of professors or specific professor
        professors_batch = self.registry.select_batch(
            batch_size=batch_size, target_name=professor_name
        )
        logger.info(f"Processing batch of {len(professors_batch)} professors")

        fetch_failures = 0
        corpora_list: List[ProfessorCorpus] = []
        clusters_by_prof: Dict[str, List[UnsolvedProblemCluster]] = {}
        qualifications_by_prof: Dict[str, Dict[str, PhDQualificationResult]] = {}
        statements_by_prof: Dict[str, Dict[str, IEEEResearchStatement]] = {}

        for prof in professors_batch:
            p_name = prof.get("name", "Unknown")
            logger.info(f"--- Processing Professor: {p_name} ---")
            try:
                # Step 1: Corpus of at least 20 highly relevant papers
                corpus = self.corpus_builder.build_corpus(prof)
                corpora_list.append(corpus)
                logger.info(f"Step 1 Corpus for {p_name}: {corpus.corpus_count} papers (insufficient={corpus.insufficient_corpus})")

                # Step 2: Extract unsolved problem clusters
                clusters = self.unsolved_extractor.extract_from_corpus(corpus)
                clusters_by_prof[p_name] = clusters
                logger.info(f"Step 2 Unsolved Clusters for {p_name}: {len(clusters)} open/partial clusters")

                # Step 3: PhD qualification rubric
                qual_map: Dict[str, PhDQualificationResult] = {}
                stmt_map: Dict[str, IEEEResearchStatement] = {}

                for cl in clusters:
                    qual = self.phd_assessor.assess_qualification(cl, corpus.papers, corpus)
                    qual_map[cl.cluster_id] = qual

                    # Step 4: IEEE research statement for qualified & borderline topics
                    if qual.outcome in ("qualified", "borderline"):
                        stmt = self.statement_generator.generate_statement(
                            cluster=cl,
                            qualification=qual,
                            corpus_papers=corpus.papers,
                            professor_corpus=corpus,
                        )
                        stmt_map[cl.cluster_id] = stmt

                qualifications_by_prof[p_name] = qual_map
                statements_by_prof[p_name] = stmt_map

            except Exception as e:
                fetch_failures += 1
                logger.error(f"Failed processing for professor {p_name}: {e}")

        # Check silent failure constraint: fail workflow if no professor produced a corpus
        valid_corpora = [c for c in corpora_list if c.corpus_count > 0]
        if not valid_corpora and professors_batch:
            raise RuntimeError("Pipeline execution failure: No professor produced a valid literature corpus.")

        # Persist data under data/
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(DATA_DIR / "research_gaps_corpora.json", [c.to_dict() for c in corpora_list])

        # Write accumulated dashboard payload
        payload = self._build_4step_dashboard_payload(
            corpora_list=corpora_list,
            clusters_by_prof=clusters_by_prof,
            qualifications_by_prof=qualifications_by_prof,
            statements_by_prof=statements_by_prof,
            start_time=start_time,
            fetch_failures=fetch_failures,
        )

        DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(DOCS_DATA_DIR / "research_gap_data.json", payload)

        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration = (end_time - start_time).total_seconds()

        summary_meta = {
            "last_updated": end_time.isoformat(),
            "execution_duration_seconds": duration,
            "professors_processed": len(professors_batch),
            "fetch_failures": fetch_failures,
            "total_papers": sum(c.corpus_count for c in corpora_list),
            "total_clusters": sum(len(cl_list) for cl_list in clusters_by_prof.values()),
            "total_qualified": sum(
                1
                for prof_q in qualifications_by_prof.values()
                for q in prof_q.values()
                if q.outcome == "qualified"
            ),
            "extraction_method": "rules",
        }
        logger.info(f"=== 4-Step Pipeline Completed in {duration:.1f}s ===")
        return summary_meta

    def _build_4step_dashboard_payload(
        self,
        corpora_list: List[ProfessorCorpus],
        clusters_by_prof: Dict[str, List[UnsolvedProblemCluster]],
        qualifications_by_prof: Dict[str, Dict[str, PhDQualificationResult]],
        statements_by_prof: Dict[str, Dict[str, IEEEResearchStatement]],
        start_time: datetime.datetime,
        fetch_failures: int,
    ) -> Dict[str, Any]:
        """Builds combined JSON payload for docs/data/research_gap_data.json."""
        professors_data = []
        total_papers = 0
        total_problems = 0
        total_qualified = 0

        for corpus in corpora_list:
            p_name = corpus.professor_name
            clusters = clusters_by_prof.get(p_name, [])
            qual_map = qualifications_by_prof.get(p_name, {})
            stmt_map = statements_by_prof.get(p_name, {})

            total_papers += corpus.corpus_count
            total_problems += len(clusters)
            total_qualified += sum(1 for q in qual_map.values() if q.outcome == "qualified")

            professors_data.append({
                "professor_name": corpus.professor_name,
                "university": corpus.university,
                "orcid": corpus.orcid,
                "openalex_author_id": corpus.openalex_author_id,
                "match_confidence": corpus.match_confidence,
                "match_reason": corpus.match_reason,
                "last_processed_date": corpus.last_processed_date,
                "corpus_summary": {
                    "count": corpus.corpus_count,
                    "target_count": corpus.target_count,
                    "insufficient_corpus": corpus.insufficient_corpus,
                    "own_count": sum(1 for p in corpus.papers if p.role == "own"),
                    "related_count": sum(1 for p in corpus.papers if p.role == "related"),
                },
                "papers": [p.to_dict() for p in corpus.papers],
                "unsolved_problems": [cl.to_dict() for cl in clusters],
                "phd_qualifications": {k: q.to_dict() for k, q in qual_map.items()},
                "research_statements": {k: s.to_dict() for k, s in stmt_map.items()},
            })

        return {
            "meta": {
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "extraction_method": "rules",
                "note": "Rule-based PhD topic discovery using TF-IDF/Jaccard statistics and Dublin Descriptors rubric. No AI model used.",
                "total_professors": len(professors_data),
                "total_papers": total_papers,
                "total_unsolved_problems": total_problems,
                "total_qualified_phd_topics": total_qualified,
                "fetch_failures": fetch_failures,
            },
            "professors": professors_data,
        }

    def _run_legacy(self, verify_links: bool = True) -> Dict[str, Any]:
        """Executes the legacy research gap analysis pipeline."""
        logger.info("=== Starting Legacy Research Gap Analysis Pipeline ===")
        start_time = datetime.datetime.now(datetime.timezone.utc)
        # Execute legacy flow
        all_items: List[ResearchItem] = []
        seed_file = DATA_DIR / "research_gaps_seed_papers.json"
        if seed_file.exists():
            try:
                import json
                with open(seed_file, "r", encoding="utf-8") as f:
                    for item_dict in json.load(f):
                        all_items.append(ResearchItem.from_dict(item_dict))
            except Exception as e:
                logger.warning(f"Legacy seed load error: {e}")

        unique_items = self.deduplicator.deduplicate(all_items)
        extracted_papers = self.gap_extractor.extract_batch(unique_items)
        problems = [p.to_dict() for p in self.problem_tracker.load_problems()]

        end_time = datetime.datetime.now(datetime.timezone.utc)
        return {
            "mode": "legacy",
            "execution_duration_seconds": (end_time - start_time).total_seconds(),
            "unique_papers": len(unique_items),
            "extracted_papers": len(extracted_papers),
            "total_problems": len(problems),
        }
