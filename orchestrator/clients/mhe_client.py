# Minimal placeholder clients for MHE interactions.
async def hybrid_search(query: str) -> dict:
    """Performs a hybrid search.

    This function is a placeholder for a real MHE client. It simulates a
    hybrid search and returns a fake response.

    Args:
        query: The query to search for.

    Returns:
        A dictionary containing the search results. The "sources" key is an
        empty list, and the "context" key is a string with the format
        "Context for: query".
    """
    # Replace with actual MHE call
    return {"sources": [], "context": f"Context for: {query}"}

async def record_event(payload: dict) -> None:
    """Records an event.

    This function is a placeholder for a real MHE client. It simulates
    recording an event by sending a POST request to MHE's ingestion endpoint.

    Args:
        payload: The event payload to record.
    """
    # Replace with POST to MHE's ingestion endpoint
    return None
