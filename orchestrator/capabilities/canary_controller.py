from typing import Callable, Dict, Any
from .quarantine import QuarantineManager

class CanaryController:
    """Controls the canarying of capabilities."""
    def __init__(self, qm: QuarantineManager, execute_fn: Callable[[str, Dict[str,Any]], Dict[str,Any]]):
        """
        Initializes the CanaryController.

        Args:
            qm (QuarantineManager): The quarantine manager.
            execute_fn (Callable[[str, Dict[str,Any]], Dict[str,Any]]): The function to execute a capability.
        """
        self.qm = qm
        self.execute_fn = execute_fn  # (capability_id, payload) -> result

    def maybe_route(self, capability_id: str, payload: Dict[str,Any]) -> Dict[str,Any] | None:
        """
        Maybe routes a request to a canary.

        Args:
            capability_id (str): The ID of the capability to route to.
            payload (Dict[str,Any]): The payload to send to the capability.

        Returns:
            Dict[str,Any] | None: The result of the canary execution, or None if not a canary.
        """
        if self.qm.should_route_canary(capability_id):
            result = self.execute_fn(capability_id, payload)
            # simplistic success heuristic
            success = bool(result) and result.get("ok", True)
            self.qm.report(capability_id, success)
            return {"canary": True, "result": result}
        return None
