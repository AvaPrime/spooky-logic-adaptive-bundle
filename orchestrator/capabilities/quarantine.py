import time, random
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class QuarantinedCapability:
    """Represents a capability that is in quarantine.

    Attributes:
        capability_id: The ID of the capability.
        reason: The reason for quarantining the capability.
        inserted_at: The timestamp when the capability was quarantined.
        canary_rate: The rate at which traffic is routed to the canary.
        stats: A dictionary of statistics about the canary's performance.
    """
    capability_id: str
    reason: str
    inserted_at: float = field(default_factory=time.time)
    canary_rate: float = 0.0
    stats: Dict[str, Any] = field(default_factory=lambda: {"success":0,"fail":0})

class QuarantineManager:
    """Manages the quarantine of capabilities.

    This class provides methods for adding, removing, and listing quarantined
    capabilities, as well as for determining if a request should be routed to a
    canary and for reporting the results of canary executions.
    """
    def __init__(self):
        """Initializes the QuarantineManager."""
        self.q: Dict[str, QuarantinedCapability] = {}

    def add(self, capability_id: str, reason: str, canary_rate: float = 0.02):
        """Adds a capability to quarantine.

        Args:
            capability_id: The ID of the capability to add.
            reason: The reason for quarantining the capability.
            canary_rate: The canary rate for the capability.

        Returns:
            The quarantined capability.
        """
        self.q[capability_id] = QuarantinedCapability(capability_id, reason, canary_rate=canary_rate)
        return self.q[capability_id]

    def remove(self, capability_id: str):
        """Removes a capability from quarantine.

        Args:
            capability_id: The ID of the capability to remove.

        Returns:
            The removed capability, or None if not found.
        """
        return self.q.pop(capability_id, None)

    def list(self) -> List[QuarantinedCapability]:
        """Lists all quarantined capabilities.

        Returns:
            A list of all quarantined capabilities.
        """
        return list(self.q.values())

    def should_route_canary(self, capability_id: str) -> bool:
        """Determines if a request should be routed to a canary.

        This method uses the canary rate of the capability to randomly determine
        if a request should be routed to the canary.

        Args:
            capability_id: The ID of the capability to check.

        Returns:
            True if the request should be routed to a canary, False otherwise.
        """
        cap = self.q.get(capability_id)
        if not cap: return False
        return random.random() < cap.canary_rate

    def report(self, capability_id: str, success: bool):
        """Reports the result of a canary execution.

        Args:
            capability_id: The ID of the capability to report on.
            success: Whether the execution was successful.
        """
        cap = self.q.get(capability_id)
        if not cap: return
        if success: cap.stats["success"] += 1
        else: cap.stats["fail"] += 1

    def ready_to_promote(self, capability_id: str, min_success: int = 20, fail_ratio_max: float = 0.1) -> bool:
        """Determines if a capability is ready to be promoted from quarantine.

        This method checks if a capability has had enough successful executions
        and if its failure ratio is below a certain threshold.

        Args:
            capability_id: The ID of the capability to check.
            min_success: The minimum number of successful executions.
            fail_ratio_max: The maximum failure ratio.

        Returns:
            True if the capability is ready to be promoted, False otherwise.
        """
        cap = self.q.get(capability_id)
        if not cap: return False
        total = cap.stats["success"] + cap.stats["fail"]
        if total < min_success: return False
        ratio = (cap.stats["fail"] / total) if total > 0 else 1.0
        return ratio <= fail_ratio_max
