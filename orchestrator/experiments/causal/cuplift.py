from __future__ import annotations
import random, math
from typing import List, Dict, Tuple

def stratified_bootstrap_uplift(scores_a: List[float], scores_b: List[float], strata: List[int], iters: int = 1000) -> Dict:
    """Estimates the uplift distribution using a stratified bootstrap.

    This function provides a lightweight stand-in for a full causal inference
    library like DoWhy. It estimates the uplift of arm B over arm A by
    stratifying the data by the given strata (e.g., task domain IDs) and
    then performing a bootstrap analysis.

    Args:
        scores_a: The scores for the first arm (A).
        scores_b: The scores for the second arm (B).
        strata: The strata for each score.
        iters: The number of bootstrap iterations to run.

    Returns:
        A dictionary containing the mean uplift and the 95% confidence
        interval.
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
