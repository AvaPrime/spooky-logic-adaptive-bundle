from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
import time

@dataclass
class RollbackPlan:
    """Represents a plan for rolling back a capability.

    Attributes:
        capability_id: The ID of the capability to roll back.
        reason: The reason for the rollback.
        start_ts: The timestamp when the rollback started.
        stages: The stages of the rollback, as a list of traffic percentages
            to pull back.
        interval_sec: The interval between stages in seconds.
        current_stage: The current stage of the rollback.
        active: Whether the rollback is active.
    """
    capability_id: str
    reason: str
    start_ts: float = field(default_factory=time.time)
    stages: list = field(default_factory=lambda: [0.25, 0.50, 0.75, 1.0])  # percentages of traffic to pull back
    interval_sec: int = 120
    current_stage: int = 0
    active: bool = True

class AutoRollbackController:
    """Controls the automated rollback of capabilities.

    This class provides methods for starting, getting the status of, and
    advancing the stage of a rollback plan.
    """
    def __init__(self):
        """Initializes the AutoRollbackController."""
        self.plans: Dict[str, RollbackPlan] = {}

    def start(self, capability_id: str, reason: str, stages=None, interval_sec: int = 120) -> RollbackPlan:
        """Starts a new rollback plan.

        Args:
            capability_id: The ID of the capability to roll back.
            reason: The reason for the rollback.
            stages: The stages of the rollback. If not provided, it defaults
                to [0.25, 0.50, 0.75, 1.0].
            interval_sec: The interval between stages in seconds.

        Returns:
            The created rollback plan.
        """
        plan = RollbackPlan(capability_id, reason, stages=stages or [0.25,0.50,0.75,1.0], interval_sec=interval_sec)
        self.plans[capability_id] = plan
        return plan

    def status(self, capability_id: str) -> Optional[RollbackPlan]:
        """Gets the status of a rollback plan.

        Args:
            capability_id: The ID of the capability to get the status of.

        Returns:
            The rollback plan, or None if not found.
        """
        return self.plans.get(capability_id)

    def tick(self, capability_id: str) -> Dict:
        """Moves a rollback plan to the next stage.

        This method advances the stage of a rollback plan based on the elapsed
        time since the rollback started.

        Args:
            capability_id: The ID of the capability to tick.

        Returns:
            A dictionary containing the status of the rollback plan.
        """
        plan = self.plans.get(capability_id)
        if not plan or not plan.active:
            return {"active": False}
        # Move through stages based on elapsed time
        elapsed = time.time() - plan.start_ts
        target_stage = min(int(elapsed // plan.interval_sec), len(plan.stages)-1)
        progressed = False
        while plan.current_stage < target_stage:
            plan.current_stage += 1
            progressed = True
        blast_radius = plan.stages[plan.current_stage]  # portion of traffic to rollback (remove)
        if plan.current_stage >= len(plan.stages)-1:
            plan.active = False
        return {"active": plan.active, "blast_radius": blast_radius, "stage": plan.current_stage}
