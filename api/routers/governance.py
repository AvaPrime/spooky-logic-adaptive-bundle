from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime

from models.governance import (
    ProposalRequest, ProposalResponse, VoteRequest, VoteResponse,
    GovernanceBoardResponse, ProposalDetailsResponse
)
from models.base import ErrorResponse, SuccessResponse

router = APIRouter(prefix="/governance", tags=["governance"])

<<<<<<< HEAD
# In-memory storage (replace with database in production)
BOARD = []

@router.post("/propose", response_model=ProposalResponse)
async def propose(proposal: ProposalRequest):
    """Submit a new governance proposal"""
    try:
        proposal_id = f"prop-{len(BOARD) + 1}"
        
        proposal_data = {
            "id": proposal_id,
            "title": proposal.title,
            "description": proposal.description,
            "action": proposal.action,
            "tenant": proposal.tenant,
            "capability_id": proposal.capability_id,
            "proposer": proposal.proposer,
            "rationale": proposal.rationale,
            "created_at": datetime.utcnow(),
            "expiration": proposal.expiration,
            "votes_for": 0,
            "votes_against": 0,
            "total_weight": 0.0,
            "status": "active",
            "votes": []
        }
        
        BOARD.append(proposal_data)
        
        return ProposalResponse(
            proposal_id=proposal_id,
            status="submitted",
            message="Proposal submitted successfully",
            title=proposal.title,
            action=proposal.action,
            created_at=proposal_data["created_at"],
            expiration=proposal.expiration
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vote", response_model=VoteResponse)
async def vote(vote_request: VoteRequest):
    """Cast a vote on a governance proposal"""
    try:
        # Find the proposal
        proposal = None
        for p in BOARD:
            if p["id"] == vote_request.proposal_id:
                proposal = p
                break
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        if proposal["status"] != "active":
            raise HTTPException(status_code=400, detail="Proposal is not active")
        
        # Check if voter already voted
        for existing_vote in proposal["votes"]:
            if existing_vote["voter"] == vote_request.voter:
                raise HTTPException(status_code=400, detail="Voter has already voted")
        
        # Add the vote
        vote_data = {
            "voter": vote_request.voter,
            "vote": vote_request.vote,
            "weight": vote_request.weight,
            "timestamp": datetime.utcnow(),
            "rationale": vote_request.rationale
        }
        
        proposal["votes"].append(vote_data)
        
        # Update vote counts
        if vote_request.vote == "approve":
            proposal["votes_for"] += 1
        else:
            proposal["votes_against"] += 1
        
        proposal["total_weight"] += vote_request.weight
        
        return VoteResponse(
            vote_id=f"vote-{len(proposal['votes'])}",
            proposal_id=vote_request.proposal_id,
            status="recorded",
            message="Vote recorded successfully",
            vote=vote_request.vote,
            weight=vote_request.weight,
            current_tally={
                "votes_for": proposal["votes_for"],
                "votes_against": proposal["votes_against"],
                "total_weight": proposal["total_weight"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/board", response_model=GovernanceBoardResponse)
async def get_board():
    """Get all governance proposals"""
    try:
        return GovernanceBoardResponse(
            proposals=BOARD,
            total_proposals=len(BOARD),
            active_proposals=len([p for p in BOARD if p["status"] == "active"]),
            completed_proposals=len([p for p in BOARD if p["status"] in ["approved", "rejected"]])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/proposals/{proposal_id}", response_model=ProposalDetailsResponse)
async def get_proposal(proposal_id: str):
    """Get detailed information about a specific proposal"""
    try:
        proposal = None
        for p in BOARD:
            if p["id"] == proposal_id:
                proposal = p
                break
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        return ProposalDetailsResponse(
            **proposal,
            vote_count=len(proposal["votes"]),
            participation_rate=min(100.0, (len(proposal["votes"]) / max(1, len(BOARD))) * 100)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
=======
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
>>>>>>> 3c4a90cdb18cd40d228da1653114b2f244bb47fd
