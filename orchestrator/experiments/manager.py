from __future__ import annotations
import math, time
from collections import defaultdict
from typing import Dict, List, Tuple

class ABResult:
    """Represents the result of an A/B test."""
    def __init__(self, playbook:str, score:float, cost:float, latency_ms:float):
        """
        Initializes the ABResult.

        Args:
            playbook (str): The playbook that was run.
            score (float): The score of the result.
            cost (float): The cost of the result.
            latency_ms (float): The latency of the result in milliseconds.
        """
        self.playbook = playbook
        self.score = score
        self.cost = cost
        self.latency_ms = latency_ms
        self.ts = time.time()

def mean(xs):
    """Calculates the mean of a list of numbers."""
    return sum(xs)/max(1,len(xs))
def var(xs, m): 
    """Calculates the variance of a list of numbers."""
    n = len(xs)
    return (sum((x-m)**2 for x in xs) / (n-1)) if n>1 else 0.0

def welch_ttest(a:List[float], b:List[float]) -> Tuple[float,float]:
    """
    Performs Welch's t-test.

    Args:
        a (List[float]): The first sample.
        b (List[float]): The second sample.

    Returns:
        Tuple[float,float]: A tuple containing the t-statistic and degrees of freedom.
    """
    # Returns (t_stat, df). p-value can be approximated externally if needed.
    ma, mb = mean(a), mean(b)
    va, vb = var(a, ma), var(b, mb)
    na, nb = len(a), len(b)
    numer = ma - mb
    denom = math.sqrt( (va/na) + (vb/nb) ) if na>0 and nb>0 else 1.0
    t = numer/denom if denom != 0 else 0.0
    # Welch-Satterthwaite df
    df_num = (va/na + vb/nb)**2
    df_den = ((va/na)**2/(na-1 if na>1 else 1)) + ((vb/nb)**2/(nb-1 if nb>1 else 1))
    df = df_num/df_den if df_den != 0 else max(na-1, nb-1, 1)
    return t, df

class ExperimentManager:
    """Manages experiments."""
    def __init__(self, promote_uplift=0.03, max_cost_delta=0.10, min_n=10):
        """
        Initializes the ExperimentManager.

        Args:
            promote_uplift (float, optional): The minimum uplift required to promote. Defaults to 0.03.
            max_cost_delta (float, optional): The maximum cost delta allowed to promote. Defaults to 0.10.
            min_n (int, optional): The minimum number of samples required to summarize. Defaults to 10.
        """
        self.promote_uplift = promote_uplift
        self.max_cost_delta = max_cost_delta
        self.min_n = min_n
        self._data = defaultdict(list)  # key=(exp_name, arm) -> [ABResult]

    def record(self, exp:str, arm:str, score:float, cost:float, latency_ms:float):
        """
        Records an experiment result.

        Args:
            exp (str): The name of the experiment.
            arm (str): The arm of the experiment.
            score (float): The score of the result.
            cost (float): The cost of the result.
            latency_ms (float): The latency of the result in milliseconds.
        """
        self._data[(exp, arm)].append(ABResult(arm, score, cost, latency_ms))

    def summarize(self, exp:str, a_arm:str, b_arm:str) -> Dict:
        """
        Summarizes an experiment.

        Args:
            exp (str): The name of the experiment.
            a_arm (str): The name of the first arm.
            b_arm (str): The name of the second arm.

        Returns:
            Dict: A dictionary containing the summary of the experiment.
        """
        a = self._data[(exp, a_arm)]
        b = self._data[(exp, b_arm)]
        a_scores = [r.score for r in a]; b_scores = [r.score for r in b]
        a_cost   = [r.cost  for r in a]; b_cost   = [r.cost  for r in b]
        a_lat    = [r.latency_ms for r in a]; b_lat = [r.latency_ms for r in b]
        if len(a_scores) < self.min_n or len(b_scores) < self.min_n:
            return {"ready": False, "n_a": len(a_scores), "n_b": len(b_scores)}
        uplift = mean(b_scores) - mean(a_scores)
        cost_delta = mean(b_cost) - mean(a_cost)
        t, df = welch_ttest(b_scores, a_scores)
        return {
            "ready": True,
            "n_a": len(a_scores), "n_b": len(b_scores),
            "uplift": uplift, "cost_delta": cost_delta,
            "t_stat": t, "df": df,
            "recommend_promote": uplift > self.promote_uplift and cost_delta <= self.max_cost_delta
        }
