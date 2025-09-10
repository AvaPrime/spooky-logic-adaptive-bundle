import time, random
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class QuarantinedCapability:
    capability_id: str
    reason: str
    inserted_at: float = field(default_factory=time.time)
    canary_rate: float = 0.0
    stats: Dict[str, Any] = field(default_factory=lambda: {"success":0,"fail":0})

class QuarantineManager:
    def __init__(self):
        self.q: Dict[str, QuarantinedCapability] = {}

    def add(self, capability_id: str, reason: str, canary_rate: float = 0.02):
        self.q[capability_id] = QuarantinedCapability(capability_id, reason, canary_rate=canary_rate)
        return self.q[capability_id]

    def remove(self, capability_id: str):
        return self.q.pop(capability_id, None)

    def list(self) -> List[QuarantinedCapability]:
        return list(self.q.values())

    def should_route_canary(self, capability_id: str) -> bool:
        cap = self.q.get(capability_id)
        if not cap: return False
        return random.random() < cap.canary_rate

    def report(self, capability_id: str, success: bool):
        cap = self.q.get(capability_id)
        if not cap: return
        if success: cap.stats["success"] += 1
        else: cap.stats["fail"] += 1

    def ready_to_promote(self, capability_id: str, min_success: int = 20, fail_ratio_max: float = 0.1) -> bool:
        cap = self.q.get(capability_id)
        if not cap: return False
        total = cap.stats["success"] + cap.stats["fail"]
        if total < min_success: return False
        ratio = (cap.stats["fail"] / total) if total > 0 else 1.0
        return ratio <= fail_ratio_max
