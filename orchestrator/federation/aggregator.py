from __future__ import annotations
import json, time, statistics as st
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class ClusterSample:
    """Represents a sample from a cluster.

    Attributes:
        cluster_id: The ID of the cluster.
        tenant: The tenant the sample belongs to.
        arm: The experiment arm.
        score: The score of the sample.
        cost: The cost of the sample.
        latency_ms: The latency of the sample in milliseconds.
        ts: The timestamp when the sample was created.
    """
    cluster_id: str
    tenant: str
    arm: str
    score: float
    cost: float
    latency_ms: float
    ts: float = field(default_factory=time.time)

class FederatedAggregator:
    """Aggregates experiment samples from multiple clusters.

    This class produces global statistics while tracking per-cluster variance
    and drift.
    """
    def __init__(self):
        """Initializes the FederatedAggregator."""
        self.samples: List[ClusterSample] = []

    def ingest(self, sample: Dict[str, Any]):
        """Ingests a sample from a cluster.

        Args:
            sample: The sample to ingest.
        """
        self.samples.append(ClusterSample(**sample))

    def _by(self, key: str):
        """Groups samples by a given key.

        Args:
            key: The key to group the samples by.

        Returns:
            A dictionary of samples grouped by the given key.
        """
        out: Dict[str, List[ClusterSample]] = {}
        for s in self.samples:
            out.setdefault(getattr(s, key), []).append(s)
        return out

    def summarize_global(self, tenant: str, arm_a: str, arm_b: str) -> Dict[str, Any]:
        """Summarizes the global performance of two arms for a given tenant.

        Args:
            tenant: The tenant to summarize.
            arm_a: The first arm to compare.
            arm_b: The second arm to compare.

        Returns:
            A dictionary containing the global summary.
        """
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
        """Detects cluster drift for a given arm and tenant.

        This method uses the z-score to detect outliers in the scores of a
        given arm and tenant.

        Args:
            tenant: The tenant to check for drift.
            arm: The arm to check for drift.
            z_thresh: The z-score threshold for outlier detection.

        Returns:
            A dictionary containing the drift detection results.
        """
        xs = [(s.cluster_id, s.score) for s in self.samples if s.tenant == tenant and s.arm == arm]
        if len(xs) < 5: return {"enough_data": False}
        import statistics as st
        gmean = st.mean([x[1] for x in xs]); gstd = st.pstdev([x[1] for x in xs]) or 1e-6
        outliers = [cid for cid,score in xs if abs((score - gmean)/gstd) > z_thresh]
        return {"enough_data": True, "global_mean": gmean, "outliers": outliers}
