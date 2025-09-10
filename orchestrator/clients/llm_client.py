# Placeholder LLM client. Replace with real providers.
import random

async def call_llm(role: str, prompt: str) -> dict:
    # Fake a response with a confidence score
    return {"text": f"[{role}] {prompt[:80]} ... -> draft answer", "confidence": random.uniform(0.6, 0.95)}
