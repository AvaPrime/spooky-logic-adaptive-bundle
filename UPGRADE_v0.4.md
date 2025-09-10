# Spooky Logic – Upgrade Pack v0.4

Only **new** files, no overwrites.

## Adds
1. **Per-tenant playbooks**
   - `playbooks/tenants/gold_control.yaml` and `gold_variant.yaml` show how to specialize steps per tenant.

2. **Warm-start experiment sampler**
   - `orchestrator/experiments/sampler.py`
   - Tracks domain difficulty (variance) to decide how many samples needed before promotion.

3. **Causal promotion policy**
   - `policies/causal_promotion.rego`
   - Ensures lower bound of uplift CI > 0 before auto-promote.

4. **Operator CLI**
   - `cli/spookyctl.py` (Typer-based)
   - List playbooks, record experiment results, check promotion summaries.

   Usage:
   ```bash
   pip install typer requests pyyaml
   python cli/spookyctl.py list-playbooks
   ```

5. **Tenant Grafana dashboard**
   - `telemetry/grafana/dashboards/spooky_tenants.json`
   - Visualize accuracy and cost by tenant label.

## Wiring Checklist
- Tag metrics by tenant (add `tenant` label to Prometheus counters).
- Load causal promotion policy into OPA: `opa push policies/causal_promotion.rego`.
- Use sampler in orchestrator to dynamically decide N tasks needed before calling `ExperimentManager.summarize()`.
- CLI can interact with running API for operator control.

This sets the stage for v0.5: autonomous tenant-specific orchestration trees and federated experiment aggregation.
