"""Events Discovery and Tracking Module (Edge Computing & ML/Embedded/IoT)."""

from src.events.models import (
    EdgeEvent,
    MLEmbeddedIoTEvent,
    EventItem,
    EventType,
    EventFormat,
    FeeStatus,
    EventStatus,
    DiscountType,
    DiscountOpportunity,
    EventScoreBreakdown
)
from src.events.normalizer import EventNormalizer
from src.events.deduplicator import EventDeduplicator
from src.events.verifier import EventVerifier
from src.events.scorer import EventScorer
from src.events.collector import (
    ConfigurableEventCollector,
    EdgeEventCollector,
    MLEmbeddedIoTEventCollector
)
from src.events.state_manager import EventsStateManager, MLEventsStateManager
from src.events.pipeline import (
    EventsPipeline,
    EdgeEventsPipeline,
    MLEmbeddedIoTEventsPipeline
)

__all__ = [
    "EdgeEvent",
    "MLEmbeddedIoTEvent",
    "EventItem",
    "EventType",
    "EventFormat",
    "FeeStatus",
    "EventStatus",
    "DiscountType",
    "DiscountOpportunity",
    "EventScoreBreakdown",
    "EventNormalizer",
    "EventDeduplicator",
    "EventVerifier",
    "EventScorer",
    "ConfigurableEventCollector",
    "EdgeEventCollector",
    "MLEmbeddedIoTEventCollector",
    "EventsStateManager",
    "MLEventsStateManager",
    "EventsPipeline",
    "EdgeEventsPipeline",
    "MLEmbeddedIoTEventsPipeline",
]
