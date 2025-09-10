from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from orchestrator.clients.opa_client import OPA
from orchestrator.clients.router import Router
from orchestrator.clients.temporal_client import start_orchestration
from orchestrator.metrics import metrics
import os

app = FastAPI(title="Spooky Logic API", version="0.1")

class OrchestrateReq(BaseModel):
    """Request model for the /orchestrate endpoint."""
    goal: str
    budget_usd: float = Field(default=float(os.getenv("BUDGET_MAX_USD", "0.25")))
    risk: int = Field(ge=0, le=5, default=2)

@app.post("/orchestrate")
async def orchestrate(req: OrchestrateReq):
    """
    Orchestrates a new goal.

    This endpoint receives a goal, validates the budget against the policy,
    selects a playbook based on the risk level, and starts the orchestration
    workflow.

    Args:
        req (OrchestrateReq): The orchestration request.

    Returns:
        dict: A dictionary containing the run ID and the selected playbook.

    Raises:
        HTTPException: If the budget exceeds the policy.
    """
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
    """Returns a 200 OK status for health checks."""
    return {"ok": True}

@app.post("/playbooks/{name}/trial")
async def trial(name: str):
    """
    Enables a trial for a given playbook.

    Args:
        name (str): The name of the playbook to enable a trial for.

    Returns:
        dict: A dictionary indicating the enabled trial.
    """
    # Placeholder: flip feature flag for A/B
    Router.enable_trial(name)
    return {"trial_enabled": name}

@app.post("/agents/register")
async def register_agent(manifest: dict):
    """
    Registers an external agent.

    Args:
        manifest (dict): The manifest of the agent to register.

    Returns:
        dict: A dictionary indicating the registered agent.

    Raises:
        HTTPException: If the manifest is invalid.
    """
    # Very light validation
    if "name" not in manifest or "capabilities" not in manifest:
        raise HTTPException(400, "Bad manifest")
    Router.register_external_tool(manifest)
    return {"registered": manifest["name"]}
