# Codessian Adaptive Orchestrator — **Spooky Logic**

[![CI](https://img.shields.io/github/actions/workflow/status/codessa-systems/spooky-logic/ci.yml?branch=main)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)]()
[![Docs](https://img.shields.io/badge/docs-available-blue)]()

> Become the board. Absorb the game. Rewrite the rules.

Spooky Logic is a **biosynthetic adaptive orchestrator**. It self‑observes, reconfigures its agent ecology, and absorbs external AI capabilities — all under **policy‑as‑code governance**.

---

## ✨ Features

- **Self‑Tuning Orchestration**: A/B playbook trials, causal promotion policies, adaptive routing.
- **Absorption API**: Discovers, sandboxes, and integrates external tools/models.
- **Policy Engine**: OPA/Rego‑based rules enforce budgets, safety, and quality.
- **Federated Clusters**: CRDT state sync, event bus adapters (NATS/Kafka), signed playbook marketplace.
- **Governance**: RBAC, provenance chains, cosign/rekor attestation, rollback/quarantine controllers.
- **Observability**: Prometheus exporters, Grafana dashboards, OpenTelemetry spans.

---

## 🏛 Architecture

```mermaid
graph TD
    A[API Ingress] --> B[Temporal Orchestration]
    B --> C[Meta-Conductor]
    C --> D[Policy Engine]
    C --> E[Absorption API]
    B --> F[Agents]
    F --> G[Navigator]
    F --> H[Retriever]
    F --> I[Coder]
    F --> J[Mathematician]
    F --> K[Validator]
    F --> L[Scribe]
    D --> M[OPA Policies]
    E --> N[External Capabilities]
    B --> O[MHE Memory]
```

- **Temporal Orchestration** handles task decomposition and retries.
- **Meta-Conductor** adapts playbooks, routing, and promotions.
- **Policy Engine** applies Rego rules (budgets, egress, risk).
- **Absorption API** discovers → tests → integrates external capabilities.
- **Memory Harvester Engine (MHE)** provides vector + relational memory and provenance.

---

## 🚀 Quickstart

```bash
# Clone repo
git clone https://github.com/codessa-systems/spooky-logic.git
cd spooky-logic

# Copy env template
cp .env.example .env

# Start services
docker compose up --build -d

# Test orchestration endpoint
curl -X POST http://localhost:8080/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"goal":"Write Fibonacci in Python","budget_usd":0.05,"risk":2}'
```

---

## 📦 Deployment

- **Local Dev**: `docker compose`
- **Staging**: Helm + Kustomize (`iac/` folder)
- **Production**: Helm charts with values‑prod.yaml

Includes:
- IaC: Helm/Kustomize
- GitHub Actions CI (lint, test, OPA eval, SBOM, cosign verify)
- Backup/Restore scripts for Postgres + playbooks

---

## 📊 Observability

Metrics (Prometheus):
- `spooky_task_accuracy{playbook,agent}`
- `spooky_latency_ms{step}`
- `spooky_cost_usd{tenant,agent}`
- `spooky_absorption_win_rate{capability}`
- `spooky_policy_trigger_total{policy}`

Dashboards:
- Overview
- Quality & Accuracy
- Spend & Cost Control
- Federation & Bus
- Absorption Trials

---

## 🔒 Governance & Safety

- **OPA Policies**: budgets, risk thresholds, tenant autonomy.
- **Signed Bundles**: ed25519 signatures + cosign/rekor attestation.
- **Quarantine/Canary**: isolate and slow‑roll risky integrations.
- **Provenance Chains**: every step logs `{who, when, inputs, outputs, cost}`.
- **Human‑in‑the‑loop**: escalation for high‑risk tasks.

---

## 🛣 Roadmap

- Chaos & fault injection tests
- Policy drift detection across clusters
- Vault/KMS key integration
- Standardized semantic event bus
- Operator Codex portal (docs + dashboards)

---

## 📚 Learn More

- [Operator Guide (docs/operator_guide.md)]()
- [Absorption API](absorption_api_implementation.py)
- [Adaptive Policy Engine](policy_engine_design.py)
- [Architecture Config](adaptive_orchestrator_config.md)

---

## 🏷 License

MIT — see [LICENSE](LICENSE).
