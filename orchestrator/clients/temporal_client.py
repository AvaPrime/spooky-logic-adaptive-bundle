import os, asyncio, uuid
from temporalio.client import Client
from orchestrator.worker import Orchestrate

async def start_orchestration(goal: str, playbook: str, budget: float, risk: int) -> str:
    """Starts an orchestration workflow in Temporal.

    This function connects to the Temporal server and starts a new orchestration
    workflow with the given parameters.

    Args:
        goal: The goal of the orchestration.
        playbook: The playbook to use for the orchestration.
        budget: The budget for the orchestration.
        risk: The risk level of the orchestration.

    Returns:
        The ID of the started workflow run.
    """
    client = await Client.connect(os.getenv("TEMPORAL_HOST", "temporal:7233"))
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    await client.start_workflow(Orchestrate.run, {"goal": goal, "playbook": playbook, "budget": budget, "risk": risk}, id=run_id, task_queue="spooky-orchestrations")
    return run_id
