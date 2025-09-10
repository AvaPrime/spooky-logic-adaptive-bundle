from typing import Dict
from .weights import Weights  # user should provide path to existing weights file or adapter
from orchestrator.security.scorecard import trust_tier

class TrustAwareRouter:
    """A router that takes trust scores into account when routing."""
    def __init__(self, weights_adapter: Weights):
        """
        Initializes the TrustAwareRouter.

        Args:
            weights_adapter (Weights): The weights adapter to use.
        """
        self.w = weights_adapter  # needs get_weights(role) -> Dict[candidate, weight] and set_weights(...)

    def apply_trust_modifier(self, role: str, candidate: str, trust_score: float, alpha: float = 0.2) -> Dict[str,float]:
        """
        Applies a trust modifier to the weights of a candidate.

        Args:
            role (str): The role to apply the modifier to.
            candidate (str): The candidate to apply the modifier to.
            trust_score (float): The trust score of the candidate.
            alpha (float, optional): The learning rate. Defaults to 0.2.

        Returns:
            Dict[str,float]: The updated weights.
        """
        tier = trust_tier(trust_score)
        modifier = {"A":1.1, "B":1.0, "C":0.8, "D":0.5}[tier]
        weights = self.w.get_weights(role)
        if candidate not in weights:
            weights[candidate] = 0.1
        weights[candidate] *= (1 - alpha) + alpha*modifier
        # normalize
        s = sum(weights.values()) or 1.0
        for k in list(weights.keys()):
            weights[k] = round(weights[k]/s, 4)
        self.w.set_weights(role, weights)
        return weights
