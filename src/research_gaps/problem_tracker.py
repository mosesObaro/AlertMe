"""Manages the persistent research problem tracker."""

import difflib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.research_gaps.models import ResearchProblem, ExtractedPaperInfo, ProblemStatus
from src.storage.state_manager import _atomic_write_json
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / 'data'


class ProblemTracker:
    """Manages the persistent research problem tracker."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.problems_file = self.data_dir / 'research_problems.json'

    def load_problems(self) -> List[ResearchProblem]:
        """Load problems from the JSON data file."""
        if not self.problems_file.exists():
            return []
        try:
            import json
            with open(self.problems_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ResearchProblem.from_dict(p) for p in data]
        except Exception as e:
            logger.error(f"Failed to load problems from {self.problems_file}: {e}")
            return []

    def save_problems(self, problems: List[ResearchProblem]) -> None:
        """Save the list of problems to the JSON data file using an atomic write."""
        try:
            data = [p.to_dict() for p in problems]
            _atomic_write_json(self.problems_file, data)
        except Exception as e:
            logger.error(f"Failed to save problems to {self.problems_file}: {e}")

    def find_existing_problem(self, problem_statement: str, research_area: str) -> Optional[ResearchProblem]:
        """Fuzzy match against existing problems using difflib.SequenceMatcher (threshold 0.65)."""
        problems = self.load_problems()
        area_problems = [p for p in problems if p.research_area.lower() == research_area.lower()]

        for p in area_problems:
            similarity = difflib.SequenceMatcher(None, p.problem_statement.lower(), problem_statement.lower()).ratio()
            if similarity >= 0.65:
                return p
        return None

    def merge_evidence(self, existing: ResearchProblem, paper: ExtractedPaperInfo) -> ResearchProblem:
        """Merge new evidence into an existing problem without duplicating."""
        existing.last_updated = datetime.now().isoformat()

        if paper.paper_id not in existing.supporting_papers:
            existing.supporting_papers.append(paper.paper_id)
            existing.frequency += 1

        for limitation in paper.limitations:
            if limitation not in existing.known_limitations:
                existing.known_limitations.append(limitation)

        for future_work in paper.future_work:
            if future_work not in existing.unresolved_questions:
                existing.unresolved_questions.append(future_work)

        # Upgrade to investigating at frequency >= 3, but NEVER auto-promote to promising
        if existing.status == ProblemStatus.NEW and existing.frequency >= 3:
            existing.status = ProblemStatus.INVESTIGATING

        return existing

    def add_or_update_problem(self, paper_info: ExtractedPaperInfo, research_area: str) -> ResearchProblem:
        """Creates or updates a problem from extracted paper info."""
        problems = self.load_problems()
        problem_statement = paper_info.research_problem

        existing_problem = self.find_existing_problem(problem_statement, research_area)

        if existing_problem:
            merged = self.merge_evidence(existing_problem, paper_info)
            for i, p in enumerate(problems):
                if p.id == merged.id:
                    problems[i] = merged
                    break
            self.save_problems(problems)
            return merged
        else:
            new_problem = ResearchProblem(
                problem_statement=problem_statement,
                research_area=research_area,
                frequency=1,
                status=ProblemStatus.NEW,
                first_seen=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                supporting_papers=[paper_info.paper_id],
                known_limitations=list(paper_info.limitations),
                unresolved_questions=list(paper_info.future_work),
                candidate_methods=[paper_info.proposed_approach] if paper_info.proposed_approach else [],
                evaluation_metrics=list(paper_info.evaluation_metrics),
                supervisor_keywords=list(paper_info.keywords),
            )
            problems.append(new_problem)
            self.save_problems(problems)
            return new_problem

    def update_status(self, problem_id: str, new_status: str) -> bool:
        """Update problem status, validating against ProblemStatus.ALL."""
        if new_status not in ProblemStatus.ALL:
            logger.warning(f"Invalid status: {new_status}")
            return False
        problems = self.load_problems()
        for p in problems:
            if p.id == problem_id:
                p.status = new_status
                p.last_updated = datetime.now().isoformat()
                self.save_problems(problems)
                return True
        return False

    def get_problems_by_status(self, status: str) -> List[ResearchProblem]:
        """Return all problems with the given status."""
        return [p for p in self.load_problems() if p.status == status]

    def get_problems_by_area(self, area: str) -> List[ResearchProblem]:
        """Return all problems in the given research area."""
        return [p for p in self.load_problems() if p.research_area.lower() == area.lower()]
