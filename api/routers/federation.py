from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from orchestrator.federation.aggregator import FederatedAggregator

router = APIRouter(prefix="/federation", tags=["federation"])
agg = FederatedAggregator()

class Sample(BaseModel):
    """Request model for the /ingest endpoint."""
    cluster_id: str
    tenant: str
    arm: str
    score: float
    cost: float
    latency_ms: float
    ts: float

@router.post("/ingest")
def ingest(s: Sample):
    """
    Ingests a sample from a federated cluster.

    Args:
        s (Sample): The sample to ingest.

    Returns:
        dict: A dictionary indicating success.
    """
    agg.ingest(s.dict())
    return {"ok": True}

@router.get("/summary")
def summary(tenant: str, arm_a: str = "control", arm_b: str = "variant"):
    """
    Summarizes the performance of two arms for a given tenant across all clusters.

    Args:
        tenant (str): The tenant to summarize.
        arm_a (str, optional): The first arm to compare. Defaults to "control".
        arm_b (str, optional): The second arm to compare. Defaults to "variant".

    Returns:
        dict: A dictionary containing the global summary.
    """
    return agg.summarize_global(tenant, arm_a, arm_b)

@router.get("/drift")
def drift(tenant: str, arm: str):
    """
    Detects drift for a given arm and tenant across all clusters.

    Args:
        tenant (str): The tenant to check for drift.
        arm (str): The arm to check for drift.

    Returns:
        dict: A dictionary containing the drift detection results.
    """
    return agg.detect_cluster_drift(tenant, arm)
