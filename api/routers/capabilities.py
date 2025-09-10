from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from orchestrator.capabilities.verifier import verify_signatures, check_artifacts, minimal_provenance_ok
from orchestrator.capabilities.quarantine import QuarantineManager
from orchestrator.capabilities.canary_controller import CanaryController

router = APIRouter(prefix="/capabilities", tags=["capabilities"])
qm = QuarantineManager()

class VerifyReq(BaseModel):
    bundle: Dict[str, Any]
    pubkeys: Dict[str, str]

@router.post("/verify")
def verify(req: VerifyReq):
    sig_ok = verify_signatures(req.bundle, req.pubkeys)
    sbom_ok = check_artifacts(req.bundle)
    prov_ok = minimal_provenance_ok(req.bundle)
    if not (sig_ok and sbom_ok and prov_ok):
        raise HTTPException(400, "verification failed", {"sig_ok":sig_ok,"sbom_ok":sbom_ok,"prov_ok":prov_ok})
    return {"ok": True, "sig_ok": sig_ok, "sbom_ok": sbom_ok, "prov_ok": prov_ok}

class QuarantineReq(BaseModel):
    capability_id: str
    reason: str
    canary_rate: float = 0.02

@router.post("/quarantine")
def quarantine(req: QuarantineReq):
    cap = qm.add(req.capability_id, req.reason, req.canary_rate)
    return {"quarantined": cap.capability_id, "canary_rate": cap.canary_rate}

@router.get("/quarantine/list")
def qlist():
    return [{"id":c.capability_id,"rate":c.canary_rate,"stats":c.stats} for c in qm.list()]

class PromoteCheckReq(BaseModel):
    capability_id: str

@router.post("/quarantine/ready")
def ready(req: PromoteCheckReq):
    return {"ready": qm.ready_to_promote(req.capability_id)}
