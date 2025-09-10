import random, math
from typing import Dict, List

class DomainDifficultySampler:
    def __init__(self, base_n: int = 20):
        self.base_n = base_n
        self._history = {}  # domain -> accuracy history

    def record(self, domain: str, score: float):
        self._history.setdefault(domain, []).append(score)

    def required_samples(self, domain: str) -> int:
        hist = self._history.get(domain, [])
        if not hist:
            return self.base_n
        mean = sum(hist)/len(hist)
        var = sum((x-mean)**2 for x in hist)/len(hist) if len(hist) > 1 else 0.1
        # More variance -> more samples needed
        k = max(1.0, var*50)
        return int(self.base_n * k)
