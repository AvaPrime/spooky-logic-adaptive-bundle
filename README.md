# Spooky Logic — Codessian Adaptive Orchestrator (v0.1 Starter)

Become the board. Absorb the game. Rewrite the rules.

## What this is
A runnable starter scaffold for the **Adaptive Orchestrator**:
- **FastAPI** ingress (`/orchestrate`) + operator endpoints
- **Temporal** worker orchestrating playbooks (control vs variant)
- **MHE client** placeholders (hybrid search, memory writes)
- **OPA/Rego** policy gates (budget, egress, quality)
- **Prometheus** + **Grafana** telemetry (basic boards)
- **Docker Compose** for local dev

> This is intentionally minimal. Add real model connectors and your MHE endpoints, then iterate playbooks.

## Quickstart
```bash
# 1) Copy env and edit
cp .env.example .env

# 2) Bring up infra + app
docker compose up --build -d

# 3) Hit the API
curl -X POST http://localhost:8080/orchestrate -H "Content-Type: application/json"   -d '{"goal":"Write a Python function to fibonacci(n) with tests","budget_usd":0.05,"risk":2}'
```

## Layout
```
api/                 FastAPI service (ingress + operator APIs)
orchestrator/        Temporal worker, strategies, router, clients
policies/            OPA Rego bundles
playbooks/           Orchestration strategies (YAML)
telemetry/           Prometheus + Grafana
docker/              Healthchecks, Dockerfiles
tests/               Basic test harness (toy)
```

## Next steps
- Wire real LLM providers (OpenAI, Anthropic, Ollama) in `clients/llm_client.py`.
- Connect to your MHE endpoints in `clients/mhe_client.py`.
- Expand playbooks and enable A/B trials via `/playbooks/:id/trial`.
- Add absorption trials by registering external tools at `/agents/register`.
