# Spooky Logic – Upgrade Pack v1.0 RC

Only new files; no overwrites.

## Adds
1) **IaC** — Helm chart (`iac/helm`) and Kustomize base (`iac/kustomize`).  
2) **OpenTelemetry middleware** (`orchestrator/telemetry/otel_middleware.py`).  
3) **Strategy Bundle schema** (`strategy/strategy_bundle.schema.json`).  
4) **Governance Board API** (`api/routers/governance.py`).  

## Wiring
- In `api/main.py`, mount governance router:
  ```python
  from api.routers import governance
  app.include_router(governance.router)
  ```
- Add middleware:
  ```python
  from orchestrator.telemetry.otel_middleware import OpenTelemetryMiddleware
  app.add_middleware(OpenTelemetryMiddleware)
  ```
- Deploy with Helm/Kustomize in `iac/` folder.
