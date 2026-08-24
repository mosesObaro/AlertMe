"""Base Collector class with health reporting and error recording."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import datetime
import time
from src.models import ResearchItem, CredibilityTier
from src.utils.logger import logger
from src.utils.rate_limiter import PoliteRequester


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, name: str, tier: str = CredibilityTier.TIER1_ACADEMIC_STANDARDS.value, enabled: bool = True):
        self.name = name
        self.tier = tier
        self.enabled = enabled
        self.requester = PoliteRequester()
        self.last_run_time: Optional[str] = None
        self.last_status: str = "Uninitialized"
        self.failure_count: int = 0
        self.success_count: int = 0
        self.items_discovered_count: int = 0
        self.last_error: Optional[str] = None

    @abstractmethod
    def fetch(self) -> List[ResearchItem]:
        """Fetch items from the underlying source."""
        pass

    def collect(self) -> List[ResearchItem]:
        """Safely executes data collection with metrics and health recording."""
        if not self.enabled:
            logger.info(f"Collector [{self.name}] is disabled. Skipping.")
            return []

        logger.info(f"Starting collector [{self.name}]...")
        start_time = time.time()
        self.last_run_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            items = self.fetch()
            elapsed = time.time() - start_time
            self.success_count += 1
            self.failure_count = 0
            self.last_status = "Healthy"
            self.items_discovered_count += len(items)
            self.last_error = None
            logger.info(f"Collector [{self.name}] completed in {elapsed:.2f}s. Discovered {len(items)} items.")
            return items

        except Exception as e:
            elapsed = time.time() - start_time
            self.failure_count += 1
            self.last_error = str(e)
            if self.failure_count >= 3:
                self.last_status = "Failing"
            else:
                self.last_status = "Warning"

            logger.error(f"Collector [{self.name}] failed after {elapsed:.2f}s: {e}", exc_info=True)
            return []

    def get_health_status(self) -> Dict[str, Any]:
        """Returns health status report for this collector."""
        return {
            "name": self.name,
            "tier": self.tier,
            "enabled": self.enabled,
            "status": self.last_status,
            "last_run": self.last_run_time,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "total_items_discovered": self.items_discovered_count
        }
