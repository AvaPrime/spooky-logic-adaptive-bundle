import random, math
from typing import Dict, List

class DomainDifficultySampler:
    """A sampler that determines the number of required samples based on domain difficulty."""
    def __init__(self, base_n: int = 20):
        """
        Initializes the DomainDifficultySampler.

        Args:
            base_n (int, optional): The base number of samples required. Defaults to 20.
        """
        self.base_n = base_n
        self._history = {}  # domain -> accuracy history

    def record(self, domain: str, score: float):
        """
        Records the score for a given domain.

        Args:
            domain (str): The domain to record the score for.
            score (float): The score to record.
        """
        self._history.setdefault(domain, []).append(score)

    def required_samples(self, domain: str) -> int:
        """
        Determines the number of required samples for a given domain.

        Args:
            domain (str): The domain to determine the number of samples for.

        Returns:
            int: The number of required samples.
        """
        hist = self._history.get(domain, [])
        if not hist:
            return self.base_n
        mean = sum(hist)/len(hist)
        var = sum((x-mean)**2 for x in hist)/len(hist) if len(hist) > 1 else 0.1
        # More variance -> more samples needed
        k = max(1.0, var*50)
        return int(self.base_n * k)
