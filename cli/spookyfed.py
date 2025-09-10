import typer, requests, os, json, time
app = typer.Typer()

AGG_API = os.getenv("AGG_URL", "http://localhost:8080/federation")

@app.command()
def submit_sample(cluster_id:str, tenant:str, arm:str, score:float, cost:float, latency_ms:float):
    r = requests.post(f"{AGG_API}/ingest", json={
        "cluster_id": cluster_id, "tenant": tenant, "arm": arm,
        "score": score, "cost": cost, "latency_ms": latency_ms, "ts": time.time()
    })
    typer.echo(r.json())

@app.command()
def summarize(tenant:str, a:str="control", b:str="variant"):
    r = requests.get(f"{AGG_API}/summary", params={"tenant": tenant, "arm_a": a, "arm_b": b})
    typer.echo(json.dumps(r.json(), indent=2))

@app.command()
def drift(tenant:str, arm:str):
    r = requests.get(f"{AGG_API}/drift", params={"tenant": tenant, "arm": arm})
    typer.echo(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    app()
