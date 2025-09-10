import os, httpx, json, asyncio

OPA_URL = os.getenv("OPA_URL", "http://opa:8181")

class OPA:
    """A client for interacting with the Open Policy Agent (OPA) API."""
    async def _query(self, path: str, payload: dict):
        """
        Queries the OPA API.

        Args:
            path (str): The path to query.
            payload (dict): The payload to send with the query.

        Returns:
            dict: The JSON response from the OPA API.
        """
        url = f"{OPA_URL}/v1/data/{path}"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json={"input": payload})
            r.raise_for_status()
            return r.json()

    async def allow_budget(self, estimated_cost: float) -> bool:
        """
        Checks if a given budget is allowed by the OPA policy.

        Args:
            estimated_cost (float): The estimated cost of the task.

        Returns:
            bool: True if the budget is allowed, False otherwise.
        """
        max_budget = float(os.getenv("BUDGET_MAX_USD", "0.25"))
        data = await self._query("spooky/budget", {"estimated_cost": estimated_cost, "budget":{"max": max_budget}})
        return bool(data.get("result", {}).get("allow", False))

    async def debate_required(self, risk: int, validator_error_rate: float) -> bool:
        """
        Checks if a debate is required based on the risk and validator error rate.

        Args:
            risk (int): The risk level of the task.
            validator_error_rate (float): The error rate of the validator.

        Returns:
            bool: True if a debate is required, False otherwise.
        """
        data = await self._query("spooky/quality", {"task":{"risk": risk}, "validator_error_rate": validator_error_rate})
        res = data.get("result", {})
        return bool(res.get("debate_required") or res.get("second_opinion"))
