from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
import time

@dataclass
class RollbackPlan:
    capability_id: str
    reason: str
    start_ts: float = field(default_factory=time.time)
    stages: list = field(default_factory=lambda: [0.25, 0.50, 0.75, 1.0])  # percentages of traffic to pull back
    interval_sec: int = 120
    current_stage: int = 0
    active: bool = True

class AutoRollbackController:
    def __init__(self):
        self.plans: Dict[str, RollbackPlan] = {}

    def start(self, capability_id: str, reason: str, stages=None, interval_sec: int = 120) -> RollbackPlan:
        plan = RollbackPlan(capability_id, reason, stages=stages or [0.25,0.50,0.75,1.0], interval_sec=interval_sec)
        self.plans[capability_id] = plan
        return plan

    def status(self, capability_id: str) -> Optional[RollbackPlan]:
        return self.plans.get(capability_id)

    def tick(self, capability_id: str) -> Dict:
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
