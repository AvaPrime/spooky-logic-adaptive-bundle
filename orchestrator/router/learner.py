import yaml, pathlib
from typing import Dict

class RouterLearner:
    """A simple learner for updating router weights.

    This class provides a simple implementation of a learner that updates the
    weights of different candidates for a given role based on which candidate
    was the "winner".
    """
    def __init__(self, path:str):
        """Initializes the RouterLearner.

        Args:
            path: The path to the router weights file.
        """
        self.path = pathlib.Path(path)

    def update_weights(self, role:str, winner:str, alpha:float=0.1):
        """Updates the weights for a given role.

        This method uses a simple multiplicative weight update rule to increase
        the weight of the winning candidate and decrease the weights of the
        other candidates. The weights are then normalized to sum to 1.

        Args:
            role: The role to update the weights for.
            winner: The winning candidate.
            alpha: The learning rate.
        """
        data = yaml.safe_load(self.path.read_text())
        weights = data.get("roles", {}).get(role, {})
        if not weights: return
        # Simple multiplicative weight update
        for k in list(weights.keys()):
            if k == winner:
                weights[k] = float(weights[k]) * (1 + alpha)
            else:
                weights[k] = float(weights[k]) * (1 - alpha/2)
        # Normalize
        s = sum(weights.values()) or 1.0
        for k in weights: weights[k] = round(weights[k]/s, 4)
        data["roles"][role] = weights
        self.path.write_text(yaml.dump(data))
