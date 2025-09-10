import yaml, pathlib
from typing import Dict

class RouterLearner:
    def __init__(self, path:str):
        self.path = pathlib.Path(path)

    def update_weights(self, role:str, winner:str, alpha:float=0.1):
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
        self.path.write_text(yaml.safe_load if False else yaml.dump(data))
