import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.storage.state_manager import _atomic_write_json
from src.utils.logger import logger

class ResearchGapStateManager:
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.data_dir = Path(__file__).resolve().parent.parent.parent / 'data'
        else:
            self.data_dir = data_dir
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.problems_file = self.data_dir / "research_problems.json"
        self.clusters_file = self.data_dir / "research_gap_clusters.json"
        self.questions_file = self.data_dir / "research_questions.json"
        self.papers_file = self.data_dir / "extracted_papers.json"
        self.feasibility_file = self.data_dir / "feasibility_assessments.json"
        self.supervisor_file = self.data_dir / "supervisor_matches.json"
        self.link_file = self.data_dir / "link_verification.json"
        self.meta_file = self.data_dir / "research_gap_meta.json"

    def _load_json(self, path: Path, default: Any = None) -> Any:
        if default is None:
            default = []
        if not path.exists():
            return default
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return default

    def load_research_problems(self) -> List[Dict[str, Any]]:
        return self._load_json(self.problems_file, default=[])

    def save_research_problems(self, data: List[Dict[str, Any]]) -> None:
        _atomic_write_json(self.problems_file, data)

    def load_research_gap_clusters(self) -> List[Dict[str, Any]]:
        return self._load_json(self.clusters_file, default=[])

    def save_research_gap_clusters(self, data: List[Dict[str, Any]]) -> None:
        _atomic_write_json(self.clusters_file, data)

    def load_research_questions(self) -> List[Dict[str, Any]]:
        return self._load_json(self.questions_file, default=[])

    def save_research_questions(self, data: List[Dict[str, Any]]) -> None:
        _atomic_write_json(self.questions_file, data)

    def load_extracted_papers(self) -> List[Dict[str, Any]]:
        return self._load_json(self.papers_file, default=[])

    def save_extracted_papers(self, data: List[Dict[str, Any]]) -> None:
        _atomic_write_json(self.papers_file, data)

    def load_feasibility_assessments(self) -> Dict[str, Any]:
        return self._load_json(self.feasibility_file, default={})

    def save_feasibility_assessments(self, data: Dict[str, Any]) -> None:
        _atomic_write_json(self.feasibility_file, data)

    def load_supervisor_matches(self) -> Dict[str, Any]:
        return self._load_json(self.supervisor_file, default={})

    def save_supervisor_matches(self, data: Dict[str, Any]) -> None:
        _atomic_write_json(self.supervisor_file, data)

    def load_link_verification(self) -> Dict[str, Any]:
        return self._load_json(self.link_file, default={})

    def save_link_verification(self, data: Dict[str, Any]) -> None:
        _atomic_write_json(self.link_file, data)

    def load_pipeline_metadata(self) -> Dict[str, Any]:
        return self._load_json(self.meta_file, default={})

    def save_pipeline_metadata(self, meta: Dict[str, Any]) -> None:
        _atomic_write_json(self.meta_file, meta)
