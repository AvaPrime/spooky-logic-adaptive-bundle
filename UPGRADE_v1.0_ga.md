# Spooky Logic – Upgrade Pack v1.0 GA

Only new files; nothing overwritten.

## Adds
- **Multi-cluster governance sync** (CRDT + sync API).
- **Cosign signing helper** to complement verification.
- **Helm prod overlays** (service, ingress, values-prod).
- **OpenTelemetry collector** sample config.
- **RBAC & Governance policies** (OPA).
- **CI workflow** (GitHub Actions).
- **Backup/Restore scripts**.
- **Operator Guide & Release Notes**.

## Wiring
- Mount routers in `api/main.py`:
  ```python
  from api.routers import governance_sync
  app.include_router(governance_sync.router)
  ```
- Load OPA policies: rbac, governance.
- Use `state_sync` to merge governance snapshots between clusters.
- Deploy with Helm using `values-prod.yaml` for production.
- Stand up the OpenTelemetry collector with `telemetry/otel-collector-config.yaml`.
