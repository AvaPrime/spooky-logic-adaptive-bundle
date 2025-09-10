from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from orchestrator.clients.opa_client import OPA
from orchestrator.clients.router import Router
from orchestrator.clients.temporal_client import start_orchestration
from orchestrator.metrics import metrics
import os

app = FastAPI(title="Spooky Logic API", version="0.1")

class OrchestrateReq(BaseModel):
    goal: str
    budget_usd: float = Field(default=float(os.getenv("BUDGET_MAX_USD", "0.25")))
    risk: int = Field(ge=0, le=5, default=2)

@app.post("/orchestrate")
async def orchestrate(req: OrchestrateReq):
    # Budget gate
    opa = OPA()
    if not await opa.allow_budget(req.budget_usd):
        raise HTTPException(403, "Budget exceeds policy; escalate")
    # Route & start workflow
    playbook = Router.select_playbook(req.risk)
    run_id = await start_orchestration(req.goal, playbook, req.budget_usd, req.risk)
    metrics.submissions.inc()
    return {"run_id": run_id, "playbook": playbook}

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/playbooks/{name}/trial")
async def trial(name: str):
    # Placeholder: flip feature flag for A/B
    Router.enable_trial(name)
    return {"trial_enabled": name}

@app.post("/agents/register")
async def register_agent(manifest: dict):
    # Very light validation
    if "name" not in manifest or "capabilities" not in manifest:
        raise HTTPException(400, "Bad manifest")
    Router.register_external_tool(manifest)
    return {"registered": manifest["name"]}
