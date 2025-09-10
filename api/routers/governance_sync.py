from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from orchestrator.governance.state_sync import GovernanceState

router = APIRouter(prefix="/governance/sync", tags=["governance-sync"])
STATE = GovernanceState()

class Snapshot(BaseModel):
    data: Dict[str, Any]

@router.get("/snapshot")
def snapshot():
    return STATE.serialize()

@router.post("/merge")
def merge(s: Snapshot):
    inbound = GovernanceState.deserialize(s.data)
    STATE.merge(inbound)
    return STATE.serialize()
