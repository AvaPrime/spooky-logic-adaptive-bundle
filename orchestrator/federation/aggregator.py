from __future__ import annotations
import json, time, statistics as st
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class ClusterSample:
    cluster_id: str
    tenant: str
    arm: str
    score: float
    cost: float
    latency_ms: float
    ts: float = field(default_factory=time.time)

class FederatedAggregator:
    """Aggregates experiment samples coming from multiple clusters, producing global stats
    while tracking per-cluster variance and drift."""
    def __init__(self):
        self.samples: List[ClusterSample] = []

    def ingest(self, sample: Dict[str, Any]):
        self.samples.append(ClusterSample(**sample))

    def _by(self, key: str):
        out: Dict[str, List[ClusterSample]] = {}
        for s in self.samples:
            out.setdefault(getattr(s, key), []).append(s)
        return out

    def summarize_global(self, tenant: str, arm_a: str, arm_b: str) -> Dict[str, Any]:
        a = [s for s in self.samples if s.tenant == tenant and s.arm == arm_a]
        b = [s for s in self.samples if s.tenant == tenant and s.arm == arm_b]
        if len(a) < 10 or len(b) < 10:
            return {"ready": False, "n_a": len(a), "n_b": len(b)}
        ma = st.mean([s.score for s in a]); mb = st.mean([s.score for s in b])
        ca = st.mean([s.cost for s in a]);  cb = st.mean([s.cost for s in b])
        la = st.mean([s.latency_ms for s in a]); lb = st.mean([s.latency_ms for s in b])
        return {"ready": True, "uplift": mb - ma, "cost_delta": cb - ca, "latency_delta": lb - la,
                "n_a": len(a), "n_b": len(b)}

    def detect_cluster_drift(self, tenant: str, arm: str, z_thresh: float = 2.5) -> Dict[str, Any]:
        xs = [(s.cluster_id, s.score) for s in self.samples if s.tenant == tenant and s.arm == arm]
        if len(xs) < 5: return {"enough_data": False}
        import statistics as st
        gmean = st.mean([x[1] for x in xs]); gstd = st.pstdev([x[1] for x in xs]) or 1e-6
        outliers = [cid for cid,score in xs if abs((score - gmean)/gstd) > z_thresh]
        return {"enough_data": True, "global_mean": gmean, "outliers": outliers}
