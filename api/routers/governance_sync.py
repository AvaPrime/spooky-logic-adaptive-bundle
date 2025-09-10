from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from orchestrator.governance.state_sync import GovernanceState

router = APIRouter(prefix="/governance/sync", tags=["governance-sync"])
STATE = GovernanceState()

class Snapshot(BaseModel):
    """Request model for the /merge endpoint."""
    data: Dict[str, Any]

@router.get("/snapshot")
def snapshot():
    """
    Returns a snapshot of the current governance state.

    Returns:
        dict: A serialized snapshot of the governance state.
    """
    return STATE.serialize()

@router.post("/merge")
def merge(s: Snapshot):
    """
    Merges an incoming governance state snapshot with the current state.

    Args:
        s (Snapshot): The incoming governance state snapshot.

    Returns:
        dict: The merged and serialized governance state.
    """
    inbound = GovernanceState.deserialize(s.data)
    STATE.merge(inbound)
    return STATE.serialize()
