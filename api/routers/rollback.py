from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.rollback.controller import AutoRollbackController

router = APIRouter(prefix="/rollback", tags=["rollback"])
_ctl = AutoRollbackController()

class StartReq(BaseModel):
    capability_id: str
    reason: str
    interval_sec: int = 120

@router.post("/start")
def start(req: StartReq):
    plan = _ctl.start(req.capability_id, req.reason, interval_sec=req.interval_sec)
    return {"started": plan.capability_id, "stages": plan.stages, "interval_sec": plan.interval_sec}

@router.get("/status")
def status(capability_id: str):
    plan = _ctl.status(capability_id)
    if not plan:
        return {"active": False}
    return {"active": plan.active, "stage": plan.current_stage, "stages": plan.stages, "interval_sec": plan.interval_sec}

@router.post("/tick")
def tick(capability_id: str):
    return _ctl.tick(capability_id)
