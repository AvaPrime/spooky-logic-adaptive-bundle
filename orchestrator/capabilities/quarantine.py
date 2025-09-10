import time, random
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class QuarantinedCapability:
    """Represents a capability that is in quarantine."""
    capability_id: str
    reason: str
    inserted_at: float = field(default_factory=time.time)
    canary_rate: float = 0.0
    stats: Dict[str, Any] = field(default_factory=lambda: {"success":0,"fail":0})

class QuarantineManager:
    """Manages the quarantine of capabilities."""
    def __init__(self):
        """Initializes the QuarantineManager."""
        self.q: Dict[str, QuarantinedCapability] = {}

    def add(self, capability_id: str, reason: str, canary_rate: float = 0.02):
        """
        Adds a capability to quarantine.

        Args:
            capability_id (str): The ID of the capability to add.
            reason (str): The reason for quarantining the capability.
            canary_rate (float, optional): The canary rate for the capability. Defaults to 0.02.

        Returns:
            QuarantinedCapability: The quarantined capability.
        """
        self.q[capability_id] = QuarantinedCapability(capability_id, reason, canary_rate=canary_rate)
        return self.q[capability_id]

    def remove(self, capability_id: str):
        """
        Removes a capability from quarantine.

        Args:
            capability_id (str): The ID of the capability to remove.

        Returns:
            QuarantinedCapability: The removed capability, or None if not found.
        """
        return self.q.pop(capability_id, None)

    def list(self) -> List[QuarantinedCapability]:
        """
        Lists all quarantined capabilities.

        Returns:
            List[QuarantinedCapability]: A list of all quarantined capabilities.
        """
        return list(self.q.values())

    def should_route_canary(self, capability_id: str) -> bool:
        """
        Determines if a request should be routed to a canary.

        Args:
            capability_id (str): The ID of the capability to check.

        Returns:
            bool: True if the request should be routed to a canary, False otherwise.
        """
        cap = self.q.get(capability_id)
        if not cap: return False
        return random.random() < cap.canary_rate

    def report(self, capability_id: str, success: bool):
        """
        Reports the result of a canary execution.

        Args:
            capability_id (str): The ID of the capability to report on.
            success (bool): Whether the execution was successful.
        """
        cap = self.q.get(capability_id)
        if not cap: return
        if success: cap.stats["success"] += 1
        else: cap.stats["fail"] += 1

    def ready_to_promote(self, capability_id: str, min_success: int = 20, fail_ratio_max: float = 0.1) -> bool:
        """
        Determines if a capability is ready to be promoted from quarantine.

        Args:
            capability_id (str): The ID of the capability to check.
            min_success (int, optional): The minimum number of successful executions. Defaults to 20.
            fail_ratio_max (float, optional): The maximum failure ratio. Defaults to 0.1.

        Returns:
            bool: True if the capability is ready to be promoted, False otherwise.
        """
        cap = self.q.get(capability_id)
        if not cap: return False
        total = cap.stats["success"] + cap.stats["fail"]
        if total < min_success: return False
        ratio = (cap.stats["fail"] / total) if total > 0 else 1.0
        return ratio <= fail_ratio_max
