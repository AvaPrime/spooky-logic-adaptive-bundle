# Placeholder LLM client. Replace with real providers.
import random

async def call_llm(role: str, prompt: str) -> dict:
    """Calls a large language model (LLM) with a given role and prompt.

    This function is a placeholder for a real LLM client. It simulates a call
    to an LLM and returns a fake response with a confidence score.

    Args:
        role: The role of the LLM to call (e.g., "analyst", "writer").
        prompt: The prompt to send to the LLM.

    Returns:
        A dictionary containing the LLM's response and a confidence score.
        The response is a string with the format "[role] prompt ... -> draft answer".
        The confidence score is a random float between 0.6 and 0.95.
    """
    # Fake a response with a confidence score
    return {"text": f"[{role}] {prompt[:80]} ... -> draft answer", "confidence": random.uniform(0.6, 0.95)}
