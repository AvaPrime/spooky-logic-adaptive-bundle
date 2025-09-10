from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import time

router = APIRouter(prefix="/governance", tags=["governance"])
BOARD: List[Dict[str,Any]] = []

class Proposal(BaseModel):
    """Request model for the /propose endpoint."""
    tenant: str
    capability_id: str
    action: str
    rationale: str

@router.post("/propose")
def propose(p: Proposal):
    """
    Submits a new proposal to the governance board.

    Args:
        p (Proposal): The proposal to submit.

    Returns:
        dict: A dictionary indicating success and the created proposal.
    """
    entry = {"id": len(BOARD)+1, "ts": time.time(), **p.dict(), "votes": []}
    BOARD.append(entry)
    return {"ok": True, "proposal": entry}

class Vote(BaseModel):
    """Request model for the /vote endpoint."""
    proposal_id: int
    voter: str
    approve: bool

@router.post("/vote")
def vote(v: Vote):
    """
    Casts a vote on a proposal.

    Args:
        v (Vote): The vote to cast.

    Returns:
        dict: A dictionary indicating success and the updated proposal.

    Raises:
        HTTPException: If the proposal is not found.
    """
    for p in BOARD:
        if p["id"] == v.proposal_id:
            p["votes"].append({"voter":v.voter,"approve":v.approve})
            return {"ok": True, "proposal": p}
    raise HTTPException(404, "proposal not found")

@router.get("/board")
def board():
    """Returns the current state of the governance board."""
    return BOARD
