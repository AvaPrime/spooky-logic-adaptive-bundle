import random, math
from typing import Dict, List

class DomainDifficultySampler:
    """A sampler that determines the number of required samples based on domain
    difficulty.

    This class uses the historical accuracy of a domain to determine the
    number of samples required for that domain. The more variance in the
    accuracy, the more samples are required.
    """
    def __init__(self, base_n: int = 20):
        """Initializes the DomainDifficultySampler.

        Args:
            base_n: The base number of samples required.
        """
        self.base_n = base_n
        self._history = {}  # domain -> accuracy history

    def record(self, domain: str, score: float):
        """Records the score for a given domain.

        Args:
            domain: The domain to record the score for.
            score: The score to record.
        """
        self._history.setdefault(domain, []).append(score)

    def required_samples(self, domain: str) -> int:
        """Determines the number of required samples for a given domain.

        The number of required samples is determined by the historical variance
        of the domain's accuracy. More variance means more samples are
        required.

        Args:
            domain: The domain to determine the number of samples for.

        Returns:
            The number of required samples.
        """
        hist = self._history.get(domain, [])
        if not hist:
            return self.base_n
        mean = sum(hist)/len(hist)
        var = sum((x-mean)**2 for x in hist)/len(hist) if len(hist) > 1 else 0.1
        # More variance -> more samples needed
        k = max(1.0, var*50)
        return int(self.base_n * k)
