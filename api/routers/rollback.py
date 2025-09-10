from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.rollback.controller import AutoRollbackController

router = APIRouter(prefix="/rollback", tags=["rollback"])
_ctl = AutoRollbackController()

class StartReq(BaseModel):
    """Request model for the /start endpoint."""
    capability_id: str
    reason: str
    interval_sec: int = 120

@router.post("/start")
def start(req: StartReq):
    """
    Starts an automated rollback process for a capability.

    Args:
        req (StartReq): The request to start the rollback.

    Returns:
        dict: A dictionary containing information about the started rollback plan.
    """
    plan = _ctl.start(req.capability_id, req.reason, interval_sec=req.interval_sec)
    return {"started": plan.capability_id, "stages": plan.stages, "interval_sec": plan.interval_sec}

@router.get("/status")
def status(capability_id: str):
    """
    Gets the status of a rollback plan.

    Args:
        capability_id (str): The ID of the capability to check.

    Returns:
        dict: A dictionary containing the status of the rollback plan.
    """
    plan = _ctl.status(capability_id)
    if not plan:
        return {"active": False}
    return {"active": plan.active, "stage": plan.current_stage, "stages": plan.stages, "interval_sec": plan.interval_sec}

@router.post("/tick")
def tick(capability_id: str):
    """
    Manually triggers the next step in a rollback plan.

    Args:
        capability_id (str): The ID of the capability to tick.

    Returns:
        dict: The result of the tick operation.
    """
    return _ctl.tick(capability_id)
