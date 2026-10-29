"""Human-in-the-Loop Validation Queue & Few-Shot Feedback Store.

The real moat in WisdomTwin is the validation loop where current role holders review
low-confidence or high-stakes twin extractions/recommendations and corrections feed back
into future extraction and retrieval.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from ..schemas.decision_episode import DecisionEpisode, RoleTag


class ReviewItem(BaseModel):
    """Queue item awaiting review by a named human executive."""

    review_id: str
    episode_id: str
    role: RoleTag
    assigned_reviewer: str
    estimated_minutes: int = 38
    reason: str
    original_decision_statement: str
    corrected_decision_statement: Optional[str] = None
    reviewer_notes: Optional[str] = None
    status: str = Field(default="pending-human", description="pending-human | approved | corrected | declined")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class HumanValidationQueue:
    """Manages human escalations and stores role-holder corrections as few-shot examples."""

    def __init__(self, governance_threshold: float = 0.75) -> None:
        self.governance_threshold = governance_threshold
        self._items: Dict[str, ReviewItem] = {}
        self._few_shot_corrections: Dict[RoleTag, List[Dict[str, str]]] = {}

    def evaluate_and_enqueue(self, episode: DecisionEpisode) -> Optional[ReviewItem]:
        """Enqueues an episode if confidence is below governance threshold or action is escalate/safe_decline."""
        needs_review = (
            episode.confidence_score < self.governance_threshold
            or episode.governance_action.value in {"escalate", "safe_decline"}
        )
        if not needs_review:
            return None

        review_id = f"rev_{episode.episode_id}"
        reviewer = (
            episode.authority.named_human_reviewer
            or f"Current {episode.role.value} Role Holder"
        )
        estimated_mins = episode.authority.estimated_review_minutes or 38

        item = ReviewItem(
            review_id=review_id,
            episode_id=episode.episode_id,
            role=episode.role,
            assigned_reviewer=reviewer,
            estimated_minutes=estimated_mins,
            reason=(
                "Confidence below governance threshold; no sufficient precedent"
                if episode.confidence_score < self.governance_threshold
                else "High-consequence policy gate requiring named-human sign-off"
            ),
            original_decision_statement=episode.decision_statement,
        )
        self._items[review_id] = item
        return item

    def submit_human_correction(
        self,
        review_id: str,
        status: str,
        corrected_statement: Optional[str] = None,
        reviewer_notes: Optional[str] = None,
    ) -> ReviewItem:
        if review_id not in self._items:
            raise KeyError(f"Review item '{review_id}' not found")

        item = self._items[review_id]
        item.status = status
        item.corrected_decision_statement = corrected_statement
        item.reviewer_notes = reviewer_notes
        item.resolved_at = datetime.utcnow()

        if corrected_statement:
            self._few_shot_corrections.setdefault(item.role, []).append(
                {
                    "original": item.original_decision_statement,
                    "corrected": corrected_statement,
                    "notes": reviewer_notes or "",
                }
            )
        return item

    def list_pending(self, role: Optional[RoleTag] = None) -> List[ReviewItem]:
        items = list(self._items.values())
        if role:
            items = [i for i in items if i.role == role]
        return items

    def get_few_shot_examples(self, role: RoleTag) -> List[Dict[str, str]]:
        return self._few_shot_corrections.get(role, [])
