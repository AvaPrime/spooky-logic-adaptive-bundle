from typing import Callable, Dict, Any
from .quarantine import QuarantineManager

class CanaryController:
    def __init__(self, qm: QuarantineManager, execute_fn: Callable[[str, Dict[str,Any]], Dict[str,Any]]):
        self.qm = qm
        self.execute_fn = execute_fn  # (capability_id, payload) -> result

    def maybe_route(self, capability_id: str, payload: Dict[str,Any]) -> Dict[str,Any] | None:
        if self.qm.should_route_canary(capability_id):
            result = self.execute_fn(capability_id, payload)
            # simplistic success heuristic
            success = bool(result) and result.get("ok", True)
            self.qm.report(capability_id, success)
            return {"canary": True, "result": result}
        return None
