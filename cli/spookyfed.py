import typer, requests, os, json, time
app = typer.Typer()

AGG_API = os.getenv("AGG_URL", "http://localhost:8080/federation")

@app.command()
def submit_sample(cluster_id:str, tenant:str, arm:str, score:float, cost:float, latency_ms:float):
    """Submits a sample to the federation aggregator.

    This command sends a POST request to the federation API to submit a sample
    from a cluster, including its score, cost, and latency.

    Args:
        cluster_id: The ID of the cluster submitting the sample.
        tenant: The tenant the sample belongs to.
        arm: The experiment arm.
        score: The score of the sample.
        cost: The cost of the sample.
        latency_ms: The latency of the sample in milliseconds.
    """
    r = requests.post(f"{AGG_API}/ingest", json={
        "cluster_id": cluster_id, "tenant": tenant, "arm": arm,
        "score": score, "cost": cost, "latency_ms": latency_ms, "ts": time.time()
    })
    typer.echo(r.json())

@app.command()
def summarize(tenant:str, a:str="control", b:str="variant"):
    """Summarizes the performance of two arms for a given tenant.

    This command sends a GET request to the federation API to retrieve a
    summary of the performance of two experiment arms for a given tenant.

    Args:
        tenant: The tenant to summarize.
        a: The first arm to compare.
        b: The second arm to compare.
    """
    r = requests.get(f"{AGG_API}/summary", params={"tenant": tenant, "arm_a": a, "arm_b": b})
    typer.echo(json.dumps(r.json(), indent=2))

@app.command()
def drift(tenant:str, arm:str):
    """Checks for drift in a given arm for a tenant.

    This command sends a GET request to the federation API to check for data
    drift in a given experiment arm for a tenant.

    Args:
        tenant: The tenant to check for drift.
        arm: The arm to check for drift.
    """
    r = requests.get(f"{AGG_API}/drift", params={"tenant": tenant, "arm": arm})
    typer.echo(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    app()
