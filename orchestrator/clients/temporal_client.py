import os, asyncio, uuid
from temporalio.client import Client
from orchestrator.worker import Orchestrate

async def start_orchestration(goal: str, playbook: str, budget: float, risk: int) -> str:
    client = await Client.connect(os.getenv("TEMPORAL_HOST", "temporal:7233"))
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    await client.start_workflow(Orchestrate.run, {"goal": goal, "playbook": playbook, "budget": budget, "risk": risk}, id=run_id, task_queue="spooky-orchestrations")
    return run_id
