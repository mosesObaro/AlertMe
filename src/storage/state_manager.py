"""State manager for persistent historical records and deduplication tracking."""

import json
import os
import tempfile
from pathlib import Path
from typing import Set, List, Dict, Any, Optional
from src.models import ResearchItem
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEEN_ITEMS_FILE = DATA_DIR / "seen_items.json"
ALERT_HISTORY_FILE = DATA_DIR / "alert_history.json"
SOURCE_HEALTH_FILE = DATA_DIR / "source_health.json"
TRENDS_FILE = DATA_DIR / "trends.json"
SUPERVISORS_FILE = DATA_DIR / "supervisors.json"
PHD_OPPORTUNITIES_FILE = DATA_DIR / "phd_opportunities.json"
SCHOLARSHIPS_FILE = DATA_DIR / "scholarships.json"
RESEARCHER_WATCHLIST_FILE = DATA_DIR / "researcher_watchlist.json"



def _atomic_write_json(filepath: Path, data: Any):
    """Writes data to a temporary file first, then atomically replaces target file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=filepath.parent, prefix="state_", suffix=".tmp")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Failed atomic write to {filepath}: {e}")
        raise


class StateManager:
    """Handles persistent storage of seen items, alert history, and source health."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.seen_items_file = self.data_dir / "seen_items.json"
        self.alert_history_file = self.data_dir / "alert_history.json"
        self.source_health_file = self.data_dir / "source_health.json"
        self.trends_file = self.data_dir / "trends.json"
        self.supervisors_file = self.data_dir / "supervisors.json"
        self.phd_opportunities_file = self.data_dir / "phd_opportunities.json"
        self.scholarships_file = self.data_dir / "scholarships.json"
        self.researcher_watchlist_file = self.data_dir / "researcher_watchlist.json"

    def load_seen_ids(self) -> Set[str]:
        """Loads set of previously alerted/seen item IDs."""
        if not self.seen_items_file.exists():
            return set()
        try:
            with open(self.seen_items_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
        except Exception as e:
            logger.warning(f"Error loading {self.seen_items_file}: {e}")
            return set()

    def record_seen_items(self, items: List[ResearchItem]):
        """Appends new item IDs to seen_items.json."""
        existing_ids = self.load_seen_ids()
        for item in items:
            existing_ids.add(item.id)
            if item.doi:
                existing_ids.add(f"doi_{item.doi.strip().lower()}")
            if item.arxiv_id:
                existing_ids.add(f"arxiv_{item.arxiv_id.strip().lower()}")

        # Keep latest 2000 IDs to avoid uncontrolled growth
        id_list = list(existing_ids)
        if len(id_list) > 2000:
            id_list = id_list[-2000:]

        _atomic_write_json(self.seen_items_file, id_list)

    def load_alert_history(self) -> List[Dict[str, Any]]:
        """Loads alert history list."""
        if not self.alert_history_file.exists():
            return []
        try:
            with open(self.alert_history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Error loading {self.alert_history_file}: {e}")
            return []

    def record_alerts_sent(self, items: List[ResearchItem], alert_mode: str = "daily"):
        """Records alerted items into alert_history.json."""
        history = self.load_alert_history()
        for item in items:
            record = item.to_dict()
            record["alert_mode"] = alert_mode
            history.append(record)

        # Rotate history to retain latest 500 items
        if len(history) > 500:
            history = history[-500:]

        _atomic_write_json(self.alert_history_file, history)

    def save_source_health(self, health_records: List[Dict[str, Any]]):
        """Saves current collector health statuses."""
        _atomic_write_json(self.source_health_file, health_records)

    def load_source_health(self) -> List[Dict[str, Any]]:
        """Loads collector health statuses."""
        if not self.source_health_file.exists():
            return []
        try:
            with open(self.source_health_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_trends(self, trends_data: List[Dict[str, Any]]):
        """Saves emerging topic trends."""
        _atomic_write_json(self.trends_file, trends_data)

    def load_trends(self) -> List[Dict[str, Any]]:
        """Loads recorded trends."""
        if not self.trends_file.exists():
            return []
        try:
            with open(self.trends_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_supervisors(self, supervisors_data: Dict[str, Any]):
        """Saves researcher/supervisor registry."""
        _atomic_write_json(self.supervisors_file, supervisors_data)

    def load_supervisors(self) -> Dict[str, Any]:
        """Loads researcher/supervisor registry."""
        if not self.supervisors_file.exists():
            return {}
        try:
            with open(self.supervisors_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_opportunities(self, opportunities_data: List[Dict[str, Any]]):
        """Saves discovered PhD/research opportunities."""
        _atomic_write_json(self.phd_opportunities_file, opportunities_data)

    def load_opportunities(self) -> List[Dict[str, Any]]:
        """Loads discovered PhD/research opportunities."""
        if not self.phd_opportunities_file.exists():
            return []
        try:
            with open(self.phd_opportunities_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Error loading {self.phd_opportunities_file}: {e}")
            return []

    def save_scholarships(self, scholarships_data: List[Dict[str, Any]]):
        """Saves curated scholarship records."""
        _atomic_write_json(self.scholarships_file, scholarships_data)

    def load_scholarships(self) -> List[Dict[str, Any]]:
        """Loads curated scholarship records."""
        if not self.scholarships_file.exists():
            return []
        try:
            with open(self.scholarships_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Error loading {self.scholarships_file}: {e}")
            return []

    def save_researcher_watchlist(self, watchlist_data: Dict[str, Any]):
        """Saves enriched researcher watchlist and lab recruitment tracking."""
        _atomic_write_json(self.researcher_watchlist_file, watchlist_data)

    def load_researcher_watchlist(self) -> Dict[str, Any]:
        """Loads enriched researcher watchlist."""
        if not self.researcher_watchlist_file.exists():
            return {}
        try:
            with open(self.researcher_watchlist_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"Error loading {self.researcher_watchlist_file}: {e}")
            return {}

