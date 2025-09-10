# Minimal placeholder clients for MHE interactions.
async def hybrid_search(query: str) -> dict:
    # Replace with actual MHE call
    return {"sources": [], "context": f"Context for: {query}"}

async def record_event(payload: dict) -> None:
    # Replace with POST to MHE's ingestion endpoint
    return None
