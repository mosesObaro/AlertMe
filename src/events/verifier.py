"""Verification and closed-event detection engine for Edge events."""

import datetime
from typing import List, Optional, Tuple
from src.events.models import EdgeEvent, EventStatus
from src.utils.logger import logger


class EventVerifier:
    """Verifies validity of event listings, checks dates, and flags closed or expired events."""

    def __init__(self, reference_date: Optional[datetime.date] = None):
        # Allow passing custom reference date for deterministic testing
        self.reference_date = reference_date or datetime.date.today()

    def verify_event(self, event: EdgeEvent) -> Tuple[EdgeEvent, bool]:
        """
        Verifies event dates and deadlines against reference date.
        Updates event status, last_verified_date, and returns (event, is_active).
        """
        today = self.reference_date
        event.last_verified_date = today.isoformat()
        is_active = True

        # Check end date / start date for event conclusion
        end_dt = self._parse_date_safe(event.end_date)
        start_dt = self._parse_date_safe(event.start_date)

        if end_dt and end_dt < today:
            event.status = EventStatus.CONCLUDED.value
            is_active = False
        elif not end_dt and start_dt and start_dt < today:
            event.status = EventStatus.CONCLUDED.value
            is_active = False
        elif start_dt and end_dt and start_dt <= today <= end_dt:
            event.status = EventStatus.ONGOING.value
        else:
            # Event is in future: check CFP deadline
            cfp_dt = self._parse_date_safe(event.cfp_deadline)
            if cfp_dt:
                if cfp_dt >= today:
                    event.status = EventStatus.CFP_OPEN.value
                else:
                    event.status = EventStatus.REGISTRATION_OPEN.value
            else:
                event.status = EventStatus.UPCOMING.value

        return event, is_active

    def verify_all(self, events: List[EdgeEvent]) -> List[EdgeEvent]:
        """Verifies a list of events in place."""
        verified = []
        for event in events:
            ev, _ = self.verify_event(event)
            verified.append(ev)
        return verified

    def filter_active(self, events: List[EdgeEvent], include_concluded: bool = False) -> List[EdgeEvent]:
        """Filters out concluded or cancelled events unless explicitly requested."""
        filtered = []
        for event in events:
            ev, is_active = self.verify_event(event)
            if is_active or include_concluded:
                filtered.append(ev)
        return filtered

    def filter_open_cfps(self, events: List[EdgeEvent]) -> List[EdgeEvent]:
        """Filters events that currently have an open CFP submission deadline."""
        open_cfps = []
        today = self.reference_date
        for event in events:
            cfp_dt = self._parse_date_safe(event.cfp_deadline)
            if cfp_dt and cfp_dt >= today:
                open_cfps.append(event)
        return open_cfps

    @staticmethod
    def _parse_date_safe(date_str: Optional[str]) -> Optional[datetime.date]:
        if not date_str:
            return None
        try:
            return datetime.date.fromisoformat(date_str[:10])
        except Exception:
            return None
