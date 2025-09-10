# Spooky Logic – Upgrade Pack v0.6

Only **new** files, nothing overwritten.

## Adds
1. **Event Bus Adapters**
   - `orchestrator/eventbus/nats_adapter.py` (async) and `kafka_adapter.py` (sync loop)
   - Use to broadcast experiment samples, promotion decisions, and capability absorption events.

2. **CRDT Merge (LWW-Map)**
   - `orchestrator/federation/crdt.py` to converge shared state (router weights, marketplace index) across clusters even when offline.

3. **Playbook Marketplace**
   - `marketplace/manifest.schema.json` (validation shape)
   - `marketplace/client.py` (ed25519 verify + download + sha256)
   - `api/routers/marketplace.py` endpoint: POST `/market/install` to verify & install signed playbooks into `playbooks/market/`.

4. **Event Bus Grafana**
   - `telemetry/grafana/dashboards/spooky_bus.json` to visualize event flow and lag.

## Wiring
- **API**: mount the marketplace router
  ```python
  from api.routers import marketplace
  app.include_router(marketplace.router)
  ```

- **NATS**:
  ```python
  from orchestrator.eventbus.nats_adapter import NATSAdapter
  bus = NATSAdapter("nats://nats:4222", subject="spooky.events")
  await bus.connect()
  await bus.publish({"type":"exp.sample","payload":{...}})
  ```

- **Kafka**:
  ```python
  from orchestrator.eventbus.kafka_adapter import KafkaAdapter
  bus = KafkaAdapter(brokers="kafka:9092", topic="spooky.events")
  bus.publish({"type":"promotion","tenant":"gold","uplift":0.04})
  ```

- **CRDT**:
  ```python
  from orchestrator.federation.crdt import LWWMap
  a, b = LWWMap(), LWWMap()
  a.put("router_weights", {"coder":{"deepseek":0.7}})
  b.put("router_weights", {"coder":{"deepseek":0.65,"gpt4o":0.35}})
  a.merge(b)
  merged = a.get("router_weights")
  ```

- **Marketplace**:
  - Generate an ed25519 keypair (outside scope) and sign your manifest (include the public key hex when calling `/market/install`).

This pack sets the stage for **v0.7**: signed capability bundles, SBOM & provenance attestation, and policy-governed marketplace auto-adoption.
