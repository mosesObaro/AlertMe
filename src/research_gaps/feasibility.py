"""Provides evidence-based feasibility assessment for research problems."""

from typing import List, Dict, Tuple
from src.research_gaps.models import (
    ResearchProblem, 
    ExtractedPaperInfo, 
    SupervisorMatch, 
    FeasibilityAssessment
)
from src.utils.logger import logger


class FeasibilityAssessor:
    """Provides evidence-based feasibility assessment for research problems."""

    def assess(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo], supervisor_matches: List[SupervisorMatch]) -> FeasibilityAssessment:
        novelty, novelty_evidence = self._assess_novelty(problem, papers)
        significance, significance_evidence = self._assess_significance(problem)
        feasibility, feasibility_evidence = self._assess_feasibility(problem, papers)
        data_rating, data_evidence = self._assess_data_availability(problem, papers)
        infra_rating, infra_evidence = self._assess_infrastructure(problem)
        supervisor_rating, supervisor_evidence = self._assess_supervisor_fit(problem, supervisor_matches)
        pub_rating, pub_evidence = self._assess_publication_potential(problem)
        phd_rating, phd_evidence = self._assess_phd_depth(problem)

        return FeasibilityAssessment(
            problem_id=problem.id,
            novelty=novelty,
            novelty_evidence=novelty_evidence,
            significance=significance,
            significance_evidence=significance_evidence,
            feasibility=feasibility,
            feasibility_evidence=feasibility_evidence,
            data_availability=data_rating,
            data_evidence=data_evidence,
            infrastructure_requirements=infra_rating,
            infrastructure_evidence=infra_evidence,
            supervisor_fit=supervisor_rating,
            supervisor_fit_evidence=supervisor_evidence,
            publication_potential=pub_rating,
            publication_evidence=pub_evidence,
            phd_depth=phd_rating,
            phd_depth_evidence=phd_evidence,
        )

    def assess_batch(self, problems: List[ResearchProblem], papers: List[ExtractedPaperInfo], supervisor_map: Dict[str, List[SupervisorMatch]]) -> Dict[str, FeasibilityAssessment]:
        logger.info(f"Assessing feasibility for {len(problems)} problems")
        results = {}
        for problem in problems:
            matches = supervisor_map.get(problem.id, [])
            results[problem.id] = self.assess(problem, papers, matches)
        return results

    def _assess_novelty(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo]) -> Tuple[str, str]:
        freq = problem.frequency
        if freq <= 3:
            return "high", f"Based on {len(problem.supporting_papers)} paper(s) found directly addressing this problem."
        elif freq <= 6:
            return "medium", f"Moderate coverage in literature with {len(problem.supporting_papers)} supporting papers."
        return "low", f"Well-studied problem with {len(problem.supporting_papers)} papers."

    def _assess_significance(self, problem: ResearchProblem) -> Tuple[str, str]:
        lim_count = len(problem.known_limitations)
        ev_count = len(problem.evidence)
        if lim_count >= 2 or ev_count >= 2:
            return "high", f"Validated by {lim_count} known limitations across publications."
        elif lim_count == 1:
            return "medium", "Addressed by at least one major limitation identified in recent work."
        return "low", "Limited evidence of critical system bottleneck."

    def _assess_feasibility(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo]) -> Tuple[str, str]:
        has_methods = len(problem.candidate_methods) > 0
        has_approaches = len(problem.existing_approaches) > 0
        if has_methods and has_approaches:
            return "high", f"Candidate methods exist ({', '.join(problem.candidate_methods[:2])}) building on existing foundations."
        elif has_methods or has_approaches:
            return "medium", "Partial methodology established in literature."
        return "low", "Requires developing foundational methodology from scratch."

    def _assess_data_availability(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo]) -> Tuple[str, str]:
        datasets_found = []
        for p in papers:
            if p.paper_id in problem.supporting_papers and p.dataset_testbed:
                datasets_found.append(p.dataset_testbed)
        if datasets_found or problem.required_datasets:
            return "high", f"Public datasets/benchmarks identified in literature ({len(datasets_found)} mentioned)."
        return "medium", "May require synthetic workloads or simulated traces."

    def _assess_infrastructure(self, problem: ResearchProblem) -> Tuple[str, str]:
        infra = problem.infrastructure_requirements
        if infra:
            return "medium", f"Requires infrastructure: {', '.join(infra[:2])}."
        return "high", "Can be evaluated with standard GPU workstations and edge emulation testbeds."

    def _assess_supervisor_fit(self, problem: ResearchProblem, matches: List[SupervisorMatch]) -> Tuple[str, str]:
        high_matches = [m for m in matches if m.match_score >= 0.2]
        if len(high_matches) >= 2:
            names = [m.name for m in high_matches[:3]]
            return "high", f"Strong alignment with {len(high_matches)} researchers ({', '.join(names)})."
        elif len(matches) >= 1:
            return "medium", f"Potential fit with {matches[0].name}."
        return "low", "No closely aligned supervisors identified in current database."

    def _assess_publication_potential(self, problem: ResearchProblem) -> Tuple[str, str]:
        if problem.frequency >= 1 and len(problem.known_limitations) >= 1:
            return "high", "High interest in top-tier conferences (SEC, INFOCOM, MobiCom, NeurIPS)."
        return "medium", "Suitable for domain-specific workshops and transactions."

    def _assess_phd_depth(self, problem: ResearchProblem) -> Tuple[str, str]:
        q_count = len(problem.unresolved_questions)
        if q_count >= 2:
            return "high", f"{q_count} unresolved questions provide sufficient scope for a multi-year thesis."
        elif q_count == 1:
            return "medium", "Sufficient for focused PhD scope or initial papers."
        return "low", "May require broader problem formulation for a complete thesis."
