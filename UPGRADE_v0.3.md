# Spooky Logic – Upgrade Pack v0.3

Only **new** drop-in files. No overwrites.

## Adds
1. **Prometheus exporters** for API & Worker
   - API: `orchestrator/telemetry/exporter_api.py` → mount with:
     ```python
     from orchestrator.telemetry.exporter_api import mount_metrics
     mount_metrics(app)  # exposes /metrics and latency counters
     ```
   - Worker: `orchestrator/telemetry/exporter_worker.py` → in worker main:
     ```python
     from orchestrator.telemetry.exporter_worker import boot_metrics_server, timed_task
     boot_metrics_server(8000)
     with timed_task(playbook): ...  # wrap execution
     ```

2. **Causal uplift estimator** (`orchestrator/experiments/causal/cuplift.py`)
   - Use for stratified bootstrap CI around A/B results to reduce traffic skew artifacts.

3. **Persistent experiment store**
   - Apply `db/experiments.sql` to Postgres.
   - Mount router: `api/routers/experiments_store.py` for create + record endpoints.

4. **Multi-tenant policy packs**
   - Example pack: `policies/tenants/tenant_pack_example.rego`
   - Loader: `orchestrator/policies/pack_loader.py` → pushes per-tenant rego to OPA.

5. **Grafana experiment boards**
   - Import `telemetry/grafana/dashboards/spooky_experiments.json`.

## Minimal wiring checklist
- API `main.py`:
  ```python
  from orchestrator.telemetry.exporter_api import mount_metrics
  app = FastAPI(...)
  mount_metrics(app)
  from api.routers import experiments, experiments_store
  app.include_router(experiments.router)
  app.include_router(experiments_store.router)
  ```

- Worker `worker_main.py`:
  ```python
  from orchestrator.telemetry.exporter_worker import boot_metrics_server, timed_task
  boot_metrics_server(8000)
  # around execution:
  with timed_task(playbook):
      result = await exec_play(...)
  ```

- DB:
  ```bash
  psql "$POSTGRES_URL" -f db/experiments.sql
  ```

- OPA tenant pack:
  ```python
  from orchestrator.policies.pack_loader import load_tenant_pack
  load_tenant_pack('gold', 'policies/tenants/tenant_pack_example.rego')
  ```

This prepares v0.4 for: per-tenant budgets, per-tenant playbooks, and causal promotion gates using the bootstrap CI.
