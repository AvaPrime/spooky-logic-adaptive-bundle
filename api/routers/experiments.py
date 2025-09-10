from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from orchestrator.experiments.manager import ExperimentManager

router = APIRouter(prefix="/experiments", tags=["experiments"])
_mgr = ExperimentManager()

class Record(BaseModel):
    """Request model for the /record endpoint."""
    experiment: str
    arm: str
    score: float
    cost: float
    latency_ms: float

@router.post("/record")
def record(res: Record):
    """
    Records an experiment result.

    Args:
        res (Record): The experiment result to record.

    Returns:
        dict: A dictionary indicating success.
    """
    _mgr.record(res.experiment, res.arm, res.score, res.cost, res.latency_ms)
    return {"ok": True}

@router.get("/summary")
def summary(experiment: str, a: str="control_single_pass", b: str="variant_debate_tools"):
    """
    Summarizes an experiment.

    Args:
        experiment (str): The name of the experiment to summarize.
        a (str, optional): The first arm to compare. Defaults to "control_single_pass".
        b (str, optional): The second arm to compare. Defaults to "variant_debate_tools".

    Returns:
        dict: A dictionary containing the experiment summary.
    """
    s = _mgr.summarize(experiment, a, b)
    if not s.get("ready"):
        return {"ready": False, **s}
    return {"ready": True, **s}
