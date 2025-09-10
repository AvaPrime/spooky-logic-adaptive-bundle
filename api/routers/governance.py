from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import time

router = APIRouter(prefix="/governance", tags=["governance"])
BOARD: List[Dict[str,Any]] = []

class Proposal(BaseModel):
    tenant: str
    capability_id: str
    action: str
    rationale: str

@router.post("/propose")
def propose(p: Proposal):
    entry = {"id": len(BOARD)+1, "ts": time.time(), **p.dict(), "votes": []}
    BOARD.append(entry)
    return {"ok": True, "proposal": entry}

class Vote(BaseModel):
    proposal_id: int
    voter: str
    approve: bool

@router.post("/vote")
def vote(v: Vote):
    for p in BOARD:
        if p["id"] == v.proposal_id:
            p["votes"].append({"voter":v.voter,"approve":v.approve})
            return {"ok": True, "proposal": p}
    raise HTTPException(404, "proposal not found")

@router.get("/board")
def board():
    return BOARD
