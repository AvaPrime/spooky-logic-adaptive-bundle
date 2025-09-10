from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from orchestrator.capabilities.verifier import verify_signatures, check_artifacts, minimal_provenance_ok
from orchestrator.capabilities.quarantine import QuarantineManager
from orchestrator.capabilities.canary_controller import CanaryController

router = APIRouter(prefix="/capabilities", tags=["capabilities"])
qm = QuarantineManager()

class VerifyReq(BaseModel):
    """Request model for the /verify endpoint."""
    bundle: Dict[str, Any]
    pubkeys: Dict[str, str]

@router.post("/verify")
def verify(req: VerifyReq):
    """
    Verifies a capability bundle.

    This endpoint verifies the signature, SBOM, and provenance of a capability bundle.

    Args:
        req (VerifyReq): The verification request.

    Returns:
        dict: A dictionary indicating the verification status.

    Raises:
        HTTPException: If the verification fails.
    """
    sig_ok = verify_signatures(req.bundle, req.pubkeys)
    sbom_ok = check_artifacts(req.bundle)
    prov_ok = minimal_provenance_ok(req.bundle)
    if not (sig_ok and sbom_ok and prov_ok):
        raise HTTPException(400, "verification failed", {"sig_ok":sig_ok,"sbom_ok":sbom_ok,"prov_ok":prov_ok})
    return {"ok": True, "sig_ok": sig_ok, "sbom_ok": sbom_ok, "prov_ok": prov_ok}

class QuarantineReq(BaseModel):
    """Request model for the /quarantine endpoint."""
    capability_id: str
    reason: str
    canary_rate: float = 0.02

@router.post("/quarantine")
def quarantine(req: QuarantineReq):
    """
    Quarantines a capability.

    Args:
        req (QuarantineReq): The quarantine request.

    Returns:
        dict: A dictionary indicating the quarantined capability and its canary rate.
    """
    cap = qm.add(req.capability_id, req.reason, req.canary_rate)
    return {"quarantined": cap.capability_id, "canary_rate": cap.canary_rate}

@router.get("/quarantine/list")
def qlist():
    """Lists all quarantined capabilities."""
    return [{"id":c.capability_id,"rate":c.canary_rate,"stats":c.stats} for c in qm.list()]

class PromoteCheckReq(BaseModel):
    """Request model for the /quarantine/ready endpoint."""
    capability_id: str

@router.post("/quarantine/ready")
def ready(req: PromoteCheckReq):
    """
    Checks if a quarantined capability is ready to be promoted.

    Args:
        req (PromoteCheckReq): The promotion check request.

    Returns:
        dict: A dictionary indicating if the capability is ready to be promoted.
    """
    return {"ready": qm.ready_to_promote(req.capability_id)}
