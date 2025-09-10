# Spooky Logic – Upgrade Pack v0.5

Only **new** files; nothing overwritten.

## Adds
1) **Per-tenant Meta-Conductors**
   - `orchestrator/tenants/meta_conductor.py`
   - A small controller with A/B counters, promotion guard, and playbook choice logic.

2) **Federated Experiment Aggregation**
   - `orchestrator/federation/aggregator.py` + `api/routers/federation.py`
   - Ingest samples from multiple clusters; emit global summaries and drift alerts.

3) **Federation Protocol**
   - `orchestrator/federation/protocol.json` — message shapes for interop.

4) **Tenant Autonomy Policy**
   - `policies/tenant_autonomy.rego` — budget gate for tenant-driven promotions.

5) **CLI for Federation**
   - `cli/spookyfed.py` to submit samples and query global stats.

## Minimal wiring
- **API**:
  ```python
  from api.routers import federation
  app.include_router(federation.router)
  ```

- **Tenant routing**:
  ```python
  from orchestrator.tenants.meta_conductor import TenantMetaConductor, TenantConfig
  meta = TenantMetaConductor(TenantConfig(tenant_id='gold', playbook_control='gold_control', playbook_variant='gold_variant'))
  # use meta.choose_playbook(risk) and meta.record_result(arm, score, cost)
  ```

- **Promotion Gate**: Pair `meta.maybe_promote()` with your OPA call to `spooky.tenant_autonomy.allow_promotion`.

- **Federation**: submit cluster samples via `/federation/ingest` or `cli/spookyfed.py`.
