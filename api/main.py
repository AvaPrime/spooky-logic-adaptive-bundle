from pydantic import BaseModel
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from routers import (
    capabilities, experiments, federation, governance, 
    marketplace, rollback, supplychain
)
# from orchestrator.clients.llm_client import LLMClient
# from orchestrator.clients.mhe_client import MHEClient
from models.orchestration import (
    OrchestrateRequest, OrchestrateResponse, AgentManifest, 
    AgentRegistrationResponse, PlaybookTrialRequest, PlaybookTrialResponse
)
from models.base import ErrorResponse, SuccessResponse

app = FastAPI(title="Spooky Logic API", version="0.1")

# Include routers
app.include_router(capabilities.router)
app.include_router(experiments.router)
app.include_router(federation.router)
app.include_router(governance.router)
app.include_router(marketplace.router)
app.include_router(rollback.router)
app.include_router(supplychain.router)

# @app.post("/orchestrate", response_model=OrchestrateResponse)
# async def orchestrate(req: OrchestrateRequest):
#     """Main orchestration endpoint - TODO: Implement orchestrator integration"""
#     try:
#         # TODO: Initialize orchestrator with request parameters
#         # orchestrator = Orchestrator(
#         #     goal=req.goal,
#         #     budget=req.budget,
#         #     risk=req.risk,
#         #     capabilities=req.capabilities or {}
#         # )
#         
#         # TODO: Execute orchestration
#         # result = await orchestrator.execute()
#         
#         return OrchestrateResponse(
#             status="success",
#             result={"message": "Orchestration endpoint not yet implemented"},
#             execution_id="placeholder-id",
#             goal=req.goal,
#             budget_used=0.0,
#             risk_level=req.risk,
#             capabilities_used=[],
#             execution_time_ms=0.0
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
=======
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

<<<<<<< HEAD
@app.post("/playbooks/{name}/trial", response_model=PlaybookTrialResponse)
async def trial_playbook(name: str, request: PlaybookTrialRequest):
    """Enable trial mode for a specific playbook"""
    try:
        # TODO: Implement playbook trial logic
        # TODO: Set up monitoring and limits for trial
        # TODO: Store trial configuration
        
        trial_id = f"trial-{name}-{request.duration_hours}h"
        
        return PlaybookTrialResponse(
            trial_enabled=True,
            playbook_name=name,
            trial_id=trial_id,
            duration_hours=request.duration_hours,
            max_executions=request.max_executions,
            budget_limit=request.budget_limit,
            message=f"Trial enabled for playbook '{name}' for {request.duration_hours} hours"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/register", response_model=AgentRegistrationResponse)
async def register_agent(manifest: AgentManifest):
    """Register a new agent with the system"""
    try:
        # TODO: Store agent registration in database
        # TODO: Validate agent capabilities
        # TODO: Perform security checks
        
        agent_id = f"{manifest.name}-{manifest.version}"
        
        return AgentRegistrationResponse(
            status="registered",
            agent_id=agent_id,
            message="Agent registered successfully",
            name=manifest.name,
            version=manifest.version,
            capabilities=manifest.capabilities
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
=======
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
>>>>>>> 3c4a90cdb18cd40d228da1653114b2f244bb47fd
