from __future__ import annotations
import random, time
from typing import Dict, Any, Callable

class ShadowTrialRunner:
    """Runs shadow trials for new capabilities."""
    def __init__(self, run_fn: Callable[[str, str], dict]):
        """
        Initializes the ShadowTrialRunner.

        Args:
            run_fn (Callable[[str, str], dict]): A function that runs a capability with a goal.
        """
        self.run_fn = run_fn  # (capability_id, goal) -> result dict

    async def shadow(self, capability_id:str, goal:str, sample_rate:float=0.1) -> Dict[str, Any]:
        """
        Runs a capability in shadow mode.

        With a probability of sample_rate, the new capability is run in shadow mode and its
        result is returned for comparison.

        Args:
            capability_id (str): The ID of the capability to run.
            goal (str): The goal to run the capability with.
            sample_rate (float, optional): The rate at which to sample. Defaults to 0.1.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the shadow trial.
        """
        # With probability sample_rate, run the new capability in shadow and compare.
        if random.random() > sample_rate:
            return {"shadowed": False}
        candidate = self.run_fn(capability_id, goal)
        # Caller should provide baseline result to compare
        return {"shadowed": True, "candidate": candidate}
