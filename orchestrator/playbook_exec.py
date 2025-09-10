import time, asyncio
from orchestrator.clients import llm_client, mhe_client
from orchestrator.metrics import accuracy, latency, cost
from orchestrator.playbooks import load_playbook
from orchestrator.clients.router import Router

async def run_playbook(name: str, goal: str, budget: float, risk: int) -> dict:
    """
    Runs a playbook.

    Args:
        name (str): The name of the playbook to run.
        goal (str): The goal to achieve.
        budget (float): The budget for the playbook.
        risk (int): The risk level for the playbook.

    Returns:
        dict: A dictionary containing the result of the playbook execution.
    """
    pb = load_playbook(name)
    t0 = time.perf_counter()
    ctx = await llm_client.call_llm("navigator", f"Interpret goal: {goal}")
    retrieve = await mhe_client.hybrid_search(goal)
    result = await llm_client.call_llm("primary", f"Solve with context: {retrieve['context']}")
    # Fake validator pass
    validator = await llm_client.call_llm("validator", f"Critique: {result['text']}")
    score = (result['confidence'] + validator['confidence'])/2
    elapsed_ms = (time.perf_counter()-t0)*1000
    accuracy.observe(score)
    latency.observe(elapsed_ms)
    cost.observe(min(budget, 0.01))
    return {
        "answer": result["text"],
        "score": score,
        "latency_ms": elapsed_ms,
        "budget_used": min(budget, 0.01),
        "playbook": name
    }
