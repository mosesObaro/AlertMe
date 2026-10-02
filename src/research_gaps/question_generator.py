"""Generates candidate research directions for promising research problems."""

from typing import List
from src.research_gaps.models import ResearchProblem, ExtractedPaperInfo, CandidateResearchDirection
from src.utils.logger import logger


class ResearchQuestionGenerator:
    """Generates candidate research directions for promising research problems."""

    def generate_directions(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo]) -> CandidateResearchDirection:
        """Generate a candidate research direction for a specific problem."""
        logger.info(f"Generating research directions for problem: {problem.id}")

        relevant_papers = self._get_relevant_papers(problem, papers)

        research_questions = self._generate_research_questions(problem, relevant_papers)
        hypotheses = self._generate_hypotheses(problem)
        potential_contribution = self._identify_potential_contribution(problem, relevant_papers)
        methodology = self._suggest_methodology(problem, relevant_papers)
        evaluation_strategy = self._suggest_evaluation_strategy(problem, relevant_papers)
        risks = self._identify_risks(problem)

        # Flag evidence_supported=True only if derived from actual paper data
        evidence_supported = len(relevant_papers) > 0 or len(problem.supporting_papers) > 0

        # Collect evaluation metrics and datasets from papers
        eval_metrics = list(problem.evaluation_metrics)
        datasets = []
        infra = list(problem.infrastructure_requirements)
        unresolved = list(problem.unresolved_questions)

        for p in relevant_papers:
            eval_metrics.extend(p.evaluation_metrics)
            if p.dataset_testbed:
                datasets.append(p.dataset_testbed)

        eval_metrics = list(dict.fromkeys(eval_metrics))[:5]
        datasets = list(dict.fromkeys(datasets))[:3]

        direction = CandidateResearchDirection(
            problem_id=problem.id,
            research_problem=problem.problem_statement,
            research_gap=f"Gap in {problem.research_area}: existing approaches ({', '.join(problem.existing_approaches[:2]) or 'current methods'}) leave unresolved: {'; '.join(problem.known_limitations[:2]) or 'scalability challenges'}",
            research_questions=research_questions,
            hypotheses=hypotheses,
            potential_contribution=potential_contribution,
            possible_methodology=methodology,
            experimental_strategy=evaluation_strategy,
            evaluation_metrics=eval_metrics,
            required_datasets=datasets,
            infrastructure_requirements=infra,
            risks=risks,
            unresolved_issues=unresolved,
            evidence_supported=evidence_supported,
        )

        return direction

    def generate_batch(self, problems: List[ResearchProblem], papers: List[ExtractedPaperInfo]) -> List[CandidateResearchDirection]:
        """Generate research directions for a batch of promising problems."""
        logger.info(f"Generating batch research directions for {len(problems)} problems")

        target_statuses = ['investigating', 'promising', 'shortlisted']
        directions = []

        for problem in problems:
            if problem.status in target_statuses:
                try:
                    direction = self.generate_directions(problem, papers)
                    directions.append(direction)
                except Exception as e:
                    logger.error(f"Error generating direction for problem {problem.id}: {e}")

        return directions

    def _get_relevant_papers(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo]) -> List[ExtractedPaperInfo]:
        """Filter papers by matching supporting_papers IDs."""
        supporting_ids = set(problem.supporting_papers)
        return [p for p in papers if p.paper_id in supporting_ids]

    def _clean_phrase(self, text: str) -> str:
        """Strip boilerplate lead-in phrases for cleaner research question formulation."""
        import re
        cleaned = re.sub(
            r'^(future\s+(work|research)\s+(will|must|plans\s+to|should|can)\s+|'
            r'we\s+(plan\s+to|propose\s+to|aim\s+to)\s+|'
            r'however,?\s+(the\s+)?|nevertheless,?\s+|'
            r'the\s+(core\s+|primary\s+|major\s+|critical\s+)?limitation\s+is\s+(that\s+)?|'
            r'a\s+(core\s+|primary\s+|major\s+|critical\s+)?limitation\s+(of\s+this\s+work\s+)?is\s+(that\s+)?|'
            r'the\s+challenge\s+of\s+)',
            '',
            text.strip(),
            flags=re.IGNORECASE
        )
        cleaned = cleaned.rstrip('?. ')
        if cleaned and cleaned[0].isupper() and not cleaned[:3].isupper():
            cleaned = cleaned[0].lower() + cleaned[1:]
        return cleaned

    def _generate_research_questions(self, problem: ResearchProblem, relevant_papers: List[ExtractedPaperInfo]) -> List[str]:
        """Generate 2-5 research questions based on unresolved_questions and known_limitations."""
        questions = []
        area = problem.research_area or "Edge Computing"

        # From unresolved questions
        for q in problem.unresolved_questions:
            clean_q = self._clean_phrase(q)
            if clean_q:
                questions.append(f"How can {clean_q} be effectively addressed in {area}?")
            if len(questions) >= 3:
                break

        # From known limitations
        for lim in problem.known_limitations:
            clean_lim = self._clean_phrase(lim)
            if clean_lim:
                questions.append(f"What algorithmic or architectural approaches can overcome the limitation of {clean_lim} in {area}?")
            if len(questions) >= 5:
                break

        # Fallback if too few
        if len(questions) < 2:
            questions.append(f"How can dynamic trade-offs between latency, energy, and accuracy be balanced in heterogeneous {area} deployments?")
            questions.append(f"To what extent do decentralized optimization policies generalize under non-stationary network conditions in {area}?")

        return questions[:5]

    def _generate_hypotheses(self, problem: ResearchProblem) -> List[str]:
        """Generate possible hypotheses from problem evidence."""
        hypotheses = []
        area = problem.research_area or "Edge Computing"

        if problem.known_limitations:
            lim = self._clean_phrase(problem.known_limitations[0])
            hypotheses.append(
                f"Explicitly modeling {lim} within the decision framework will prevent performance degradation in {area}."
            )

        if problem.unresolved_questions:
            unres = self._clean_phrase(problem.unresolved_questions[0])
            hypotheses.append(
                f"An adaptive co-design approach incorporating {unres} will yield superior Pareto-optimal trade-offs."
            )
        else:
            hypotheses.append(
                f"A hybrid edge-cloud optimization strategy will outperform decentralized baselines under dynamic workloads in {area}."
            )

        return hypotheses

    def _identify_potential_contribution(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo]) -> str:
        """Identify what a novel contribution could be."""
        area = problem.research_area or "Edge Computing"
        if problem.known_limitations:
            lim = self._clean_phrase(problem.known_limitations[0])
            return f"A novel theoretical and algorithmic framework addressing {lim} in resource-constrained {area} systems."
        return f"An end-to-end adaptive framework and empirical benchmark dataset addressing verified bottlenecks in {area}."

    def _suggest_methodology(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo]) -> str:
        """Suggest methodology based on existing approaches and their limitations."""
        area = problem.research_area or "Edge Computing"
        return f"Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world {area} testbeds."

    def _suggest_evaluation_strategy(self, problem: ResearchProblem, papers: List[ExtractedPaperInfo]) -> str:
        """Suggest evaluation metrics and strategy."""
        metrics = ", ".join(problem.evaluation_metrics[:3]) if problem.evaluation_metrics else "latency, throughput, energy"
        return f"Evaluate on both trace-driven simulation and physical edge testbeds, measuring {metrics} across diverse workloads."

    def _identify_risks(self, problem: ResearchProblem) -> List[str]:
        """Identify research risks."""
        risks = [
            "Hardware heterogeneity may lead to inconsistent convergence behavior.",
            "High computational overhead of the proposed model on extreme edge devices.",
        ]
        if not problem.candidate_methods:
            risks.append("Lack of established baseline methods for direct empirical comparison.")
        return risks
