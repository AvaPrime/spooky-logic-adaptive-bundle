import time, asyncio, re
from orchestrator.clients import llm_client, mhe_client
from orchestrator.metrics import accuracy, latency, cost
from orchestrator.playbooks import load_playbook
from orchestrator.clients.router import Router

async def run_playbook(name: str, goal: str, budget: float, risk: int) -> dict:
    pb = load_playbook(name)
    t0 = time.perf_counter()

    # This context will be passed between steps
    step_context = {"goal": goal}

    for step in pb.get('steps', []):
        action, parameter = list(step.items())[0]

        if action == 'route':
            # Example: route: navigator
            # The 'navigator' is expected to interpret the goal.
            # For now, we'll assume it just returns the original goal in a structured way.
            ctx = await llm_client.call_llm(parameter, f"Interpret goal: {step_context['goal']}")
            step_context['interpreted_goal'] = ctx

        elif action == 'retrieve':
            # Example: retrieve: mhe.hybrid_search
            # The parameter here could be more complex, but for now we assume it's a method name.
            retrieved_data = await mhe_client.hybrid_search(step_context['goal'])
            step_context['retrieved_context'] = retrieved_data.get('context')

        elif action == 'solve':
            # Example: solve: primary_agent
            solution = await llm_client.call_llm(
                parameter,
                f"Solve with context: {step_context.get('retrieved_context', 'No context')}"
            )
            step_context['solution'] = solution.get('text')
            step_context['solution_confidence'] = solution.get('confidence') or 0.0

        elif action == 'validate':
            # Example: validate: validator
            critique = await llm_client.call_llm(
                parameter,
                f"Critique: {step_context.get('solution', 'No solution provided')}"
            )
            step_context['critique'] = critique.get('text')
            step_context['validator_confidence'] = critique.get('confidence') or 0.0

            # Calculate a combined score
            score = (step_context.get('solution_confidence', 0.0) + step_context.get('validator_confidence', 0.0)) / 2
            step_context['score'] = score

        elif action == 'decide':
            # Example: decide: accept_if(conf>=0.7)
            match = re.search(r'accept_if\(conf>=(.*)\)', parameter)
            if match:
                threshold = float(match.group(1))
                current_score = step_context.get('score', 0)
                if current_score < threshold:
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    # Observe metrics before early exit
                    accuracy.observe(current_score)
                    latency.observe(elapsed_ms)
                    cost.observe(min(budget, 0.01)) # Placeholder
                    return {
                        "answer": f"Solution rejected due to low confidence score: {current_score} < {threshold}",
                        "score": current_score,
                        "latency_ms": elapsed_ms,
                        "budget_used": min(budget, 0.01), # Placeholder
                        "playbook": name,
                        "status": "Rejected"
                    }
        else:
            # It's good practice to handle unknown actions
            print(f"Warning: Unknown playbook action '{action}'")

    # Finalize and return results
    elapsed_ms = (time.perf_counter() - t0) * 1000
    final_score = step_context.get('score', 0)

    # Observe metrics
    accuracy.observe(final_score)
    latency.observe(elapsed_ms)
    cost.observe(min(budget, 0.01)) # Placeholder

    return {
        "answer": step_context.get("solution", "No solution was generated."),
        "score": final_score,
        "latency_ms": elapsed_ms,
        "budget_used": min(budget, 0.01), # Placeholder
        "playbook": name,
        "status": "Success"
    }
