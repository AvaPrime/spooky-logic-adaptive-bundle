from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.security.scorecard import supply_chain_score, trust_tier

router = APIRouter(prefix="/supplychain", tags=["supplychain"])

class ScoreReq(BaseModel):
    """Request model for the /score endpoint."""
    sbom_ok: bool
    provenance_ok: bool
    cosign_ok: bool
    rekor_ok: bool
    max_vuln_severity: str

@router.post("/score")
def score(req: ScoreReq):
    """
    Calculates the supply chain score for a capability.

    Args:
        req (ScoreReq): The request containing the supply chain information.

    Returns:
        dict: A dictionary containing the calculated score and trust tier.
    """
    s = supply_chain_score(req.sbom_ok, req.provenance_ok, req.cosign_ok, req.rekor_ok, req.max_vuln_severity)
    return {"score": s, "tier": trust_tier(s)}
