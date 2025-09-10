from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from orchestrator.experiments.manager import ExperimentManager

router = APIRouter(prefix="/experiments", tags=["experiments"])
_mgr = ExperimentManager()

class Record(BaseModel):
    experiment: str
    arm: str
    score: float
    cost: float
    latency_ms: float

@router.post("/record")
def record(res: Record):
    _mgr.record(res.experiment, res.arm, res.score, res.cost, res.latency_ms)
    return {"ok": True}

@router.get("/summary")
def summary(experiment: str, a: str="control_single_pass", b: str="variant_debate_tools"):
    s = _mgr.summarize(experiment, a, b)
    if not s.get("ready"):
        return {"ready": False, **s}
    return {"ready": True, **s}
