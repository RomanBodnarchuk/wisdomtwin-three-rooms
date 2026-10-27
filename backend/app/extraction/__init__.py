"""Three-Pass LLM Decision-Episode Extraction Engine, Entity Resolution, Deduplication, and Human Review Queue."""

from .prompts import (
    COUNTERFACTUAL_EXTRACTOR_PROMPT,
    DECISION_DETECTOR_PROMPT,
    MONTHLY_CONSOLIDATION_PROMPT,
    REASONING_EXTRACTOR_PROMPT,
)
from .engine import DecisionExtractionEngine
from .deduplicator import CrossSourceDeduplicator, HistoricalEntityResolver
from .review_queue import HumanValidationQueue, ReviewItem

__all__ = [
    "COUNTERFACTUAL_EXTRACTOR_PROMPT",
    "CrossSourceDeduplicator",
    "DECISION_DETECTOR_PROMPT",
    "DecisionExtractionEngine",
    "HistoricalEntityResolver",
    "HumanValidationQueue",
    "MONTHLY_CONSOLIDATION_PROMPT",
    "REASONING_EXTRACTOR_PROMPT",
    "ReviewItem",
]
