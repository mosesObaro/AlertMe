"""State manager for persistent historical records and deduplication of Edge events."""

import json
import os
import tempfile
from pathlib import Path
from typing import Set, List, Dict, Any, Optional
from src.events.models import EdgeEvent
from src.utils.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_EVENTS_FILE = DATA_DIR / "events.json"
DEFAULT_SEEN_EVENTS_FILE = DATA_DIR / "seen_events.json"
DEFAULT_EVENTS_HISTORY_FILE = DATA_DIR / "events_history.json"


def _atomic_write_json(filepath: Path, data: Any):
    """Writes data to a temporary file first, then atomically replaces target file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=filepath.parent, prefix="event_state_", suffix=".tmp")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, filepath)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Failed atomic write to {filepath}: {e}")
        raise


class EventsStateManager:
    """Handles JSON persistence of active events, seen IDs, and alerting history."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        domain: str = "edge",
        events_file: Optional[Path] = None,
        seen_events_file: Optional[Path] = None,
        history_file: Optional[Path] = None
    ):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.domain = domain

        prefix = "ml_iot_" if any(d in domain.lower() for d in ["ml", "iot", "embedded"]) else ""

        self.events_file = Path(events_file) if events_file else self.data_dir / f"{prefix}events.json"
        self.seen_events_file = Path(seen_events_file) if seen_events_file else self.data_dir / f"seen_{prefix}events.json"
        self.history_file = Path(history_file) if history_file else self.data_dir / f"{prefix}events_history.json"

    def load_events(self) -> List[EdgeEvent]:
        """Loads active events list from JSON."""
        if not self.events_file.exists():
            return []
        try:
            with open(self.events_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [EdgeEvent.from_dict(item) if isinstance(item, dict) else item for item in data] if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Error loading {self.events_file}: {e}")
            return []

    def save_events(self, events: List[Any]):
        """Persists events list atomically."""
        data = [e.to_dict() if hasattr(e, "to_dict") else e for e in events]
        _atomic_write_json(self.events_file, data)

    def load_seen_event_ids(self) -> Set[str]:
        """Loads set of previously alerted/seen event IDs."""
        if not self.seen_events_file.exists():
            return set()
        try:
            with open(self.seen_events_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
        except Exception as e:
            logger.warning(f"Error loading {self.seen_events_file}: {e}")
            return set()

    def record_seen_events(self, events: List[EdgeEvent]):
        """Appends new event IDs to seen_events.json."""
        existing_ids = self.load_seen_event_ids()
        for e in events:
            existing_ids.add(e.id)

        # Cap at 2000 IDs to avoid unbounded growth
        id_list = list(existing_ids)
        if len(id_list) > 2000:
            id_list = id_list[-2000:]

        _atomic_write_json(self.seen_events_file, id_list)

    def load_history(self) -> List[Dict[str, Any]]:
        """Loads event alert history."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Error loading {self.history_file}: {e}")
            return []

    def record_history(self, events: List[EdgeEvent]):
        """Appends alerted events to history file."""
        history = self.load_history()
        for e in events:
            history.append(e.to_dict())
        if len(history) > 1000:
            history = history[-1000:]
        _atomic_write_json(self.history_file, history)


class MLEventsStateManager(EventsStateManager):
    """Convenience state manager specialized for ML, Embedded and IoT events."""

    def __init__(self, data_dir: Optional[Path] = None):
        super().__init__(data_dir=data_dir, domain="ml_iot")
