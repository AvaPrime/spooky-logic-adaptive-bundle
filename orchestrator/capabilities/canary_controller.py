from typing import Callable, Dict, Any
from .quarantine import QuarantineManager

class CanaryController:
    """Controls the canary deployment of capabilities.

    This class is responsible for deciding whether to route a request to a
    canary version of a capability and for reporting the results of the
    canary execution.
    """

    def __init__(self, qm: QuarantineManager, execute_fn: Callable[[str, Dict[str,Any]], Dict[str,Any]]):
        """Initializes the CanaryController.

        Args:
            qm: The quarantine manager, which is used to determine if a
                capability should be canaried.
            execute_fn: The function to execute a capability. This function
                should take a capability ID and a payload as input and return a
                result dictionary.
        """
        self.qm = qm
        self.execute_fn = execute_fn  # (capability_id, payload) -> result

    def maybe_route(self, capability_id: str, payload: Dict[str,Any]) -> Dict[str,Any] | None:
        """Maybe routes a request to a canary.

        This method checks with the quarantine manager to see if the request
        should be routed to a canary. If so, it executes the capability and
        reports the result back to the quarantine manager.

        Args:
            capability_id: The ID of the capability to route to.
            payload: The payload to send to the capability.

        Returns:
            The result of the canary execution, or None if the request was not
            routed to a canary. The result is a dictionary with two keys:
            "canary" (a boolean indicating if the request was a canary) and
            "result" (the result of the capability execution).
        """
        if self.qm.should_route_canary(capability_id):
            result = self.execute_fn(capability_id, payload)
            # simplistic success heuristic
            success = bool(result) and result.get("ok", True)
            self.qm.report(capability_id, success)
            return {"canary": True, "result": result}
        return None
