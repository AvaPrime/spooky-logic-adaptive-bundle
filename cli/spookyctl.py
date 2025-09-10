import typer, requests, os, json

app = typer.Typer()

API = os.getenv("API_URL", "http://localhost:8080")

@app.command()
def list_playbooks():
    # For now, just list local YAML files
    import pathlib, yaml
    pbdir = pathlib.Path("playbooks")
    for pb in pbdir.rglob("*.yaml"):
        data = yaml.safe_load(pb.read_text())
        typer.echo(f"{pb.name}: tenant={data.get('tenant','-')} steps={len(data.get('steps',[]))}")

@app.command()
def record_exp(experiment:str, arm:str, score:float, cost:float, latency:float, domain:str="general"):
    url = f"{API}/expstore/record"
    r = requests.post(url, json={"experiment":experiment,"arm":arm,"score":score,"cost":cost,"latency_ms":latency,"domain":domain})
    typer.echo(r.json())

@app.command()
def promote_check(experiment:str):
    url = f"{API}/experiments/summary?experiment={experiment}"
    r = requests.get(url)
    typer.echo(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    app()
