from __future__ import annotations
import math, time
from collections import defaultdict
from typing import Dict, List, Tuple

class ABResult:
    def __init__(self, playbook:str, score:float, cost:float, latency_ms:float):
        self.playbook = playbook
        self.score = score
        self.cost = cost
        self.latency_ms = latency_ms
        self.ts = time.time()

def mean(xs): return sum(xs)/max(1,len(xs))
def var(xs, m): 
    n = len(xs)
    return (sum((x-m)**2 for x in xs) / (n-1)) if n>1 else 0.0

def welch_ttest(a:List[float], b:List[float]) -> Tuple[float,float]:
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
    def __init__(self, promote_uplift=0.03, max_cost_delta=0.10, min_n=10):
        self.promote_uplift = promote_uplift
        self.max_cost_delta = max_cost_delta
        self.min_n = min_n
        self._data = defaultdict(list)  # key=(exp_name, arm) -> [ABResult]

    def record(self, exp:str, arm:str, score:float, cost:float, latency_ms:float):
        self._data[(exp, arm)].append(ABResult(arm, score, cost, latency_ms))

    def summarize(self, exp:str, a_arm:str, b_arm:str) -> Dict:
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
