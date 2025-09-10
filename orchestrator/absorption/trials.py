from __future__ import annotations
import random, time
from typing import Dict, Any, Callable

class ShadowTrialRunner:
    def __init__(self, run_fn: Callable[[str, str], dict]):
        self.run_fn = run_fn  # (capability_id, goal) -> result dict

    async def shadow(self, capability_id:str, goal:str, sample_rate:float=0.1) -> Dict[str, Any]:
        # With probability sample_rate, run the new capability in shadow and compare.
        if random.random() > sample_rate:
            return {"shadowed": False}
        candidate = self.run_fn(capability_id, goal)
        # Caller should provide baseline result to compare
        return {"shadowed": True, "candidate": candidate}
