# Placeholder LLM client. Replace with real providers.
import random

async def call_llm(role: str, prompt: str) -> dict:
    """
    Calls the LLM with a given role and prompt.

    Args:
        role (str): The role of the LLM to call.
        prompt (str): The prompt to send to the LLM.

    Returns:
        dict: A dictionary containing the LLM's response and a confidence score.
    """
    # Fake a response with a confidence score
    return {"text": f"[{role}] {prompt[:80]} ... -> draft answer", "confidence": random.uniform(0.6, 0.95)}
