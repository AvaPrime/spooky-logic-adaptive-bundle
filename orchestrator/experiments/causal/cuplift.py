from __future__ import annotations
import random, math
from typing import List, Dict, Tuple

def stratified_bootstrap_uplift(scores_a: List[float], scores_b: List[float], strata: List[int], iters: int = 1000) -> Dict:
    """Estimate uplift distribution via bootstrap stratified by 'strata' (e.g., task domain ids).
    Returns mean uplift and 95% CI. This is a lightweight stand-in for full DoWhy.
    """
    rng = random.Random(1337)
    by_stratum_a = {}
    by_stratum_b = {}
    for s,sa,sb in zip(strata, scores_a, scores_b):
        by_stratum_a.setdefault(s, []).append(sa)
        by_stratum_b.setdefault(s, []).append(sb)
    lifts = []
    for _ in range(iters):
        boot_a, boot_b = [], []
        for s in by_stratum_a.keys():
            aa = rng.choices(by_stratum_a[s], k=len(by_stratum_a[s]))
            bb = rng.choices(by_stratum_b[s], k=len(by_stratum_b[s]))
            boot_a.extend(aa); boot_b.extend(bb)
        ma = sum(boot_a)/len(boot_a)
        mb = sum(boot_b)/len(boot_b)
        lifts.append(mb - ma)
    lifts.sort()
    mean = sum(lifts)/len(lifts)
    lo = lifts[int(0.025*len(lifts))]
    hi = lifts[int(0.975*len(lifts))]
    return {"uplift_mean": mean, "uplift_ci95": [lo, hi]}
