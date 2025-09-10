from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from orchestrator.federation.aggregator import FederatedAggregator

router = APIRouter(prefix="/federation", tags=["federation"])
agg = FederatedAggregator()

class Sample(BaseModel):
    cluster_id: str
    tenant: str
    arm: str
    score: float
    cost: float
    latency_ms: float
    ts: float

@router.post("/ingest")
def ingest(s: Sample):
    agg.ingest(s.dict())
    return {"ok": True}

@router.get("/summary")
def summary(tenant: str, arm_a: str = "control", arm_b: str = "variant"):
    return agg.summarize_global(tenant, arm_a, arm_b)

@router.get("/drift")
def drift(tenant: str, arm: str):
    return agg.detect_cluster_drift(tenant, arm)
