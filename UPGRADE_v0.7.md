# Spooky Logic – Upgrade Pack v0.7

Only **new** files, no overwrites.

## Adds
1) **Signed Capability Bundles**
   - Schema + example SBOM + provenance.
   - Verifier to validate signatures (ed25519), SBOM shape, and provenance sanity.

2) **Quarantine + Canary**
   - Quarantine store with success/failure counters.
   - Canary controller to route a sample of traffic through a cap and observe outcomes.

3) **Policy Auto-Adoption**
   - `policies/auto_adopt.rego` and `policies/quarantine_gate.rego` to govern auto-promotion decisions.

4) **API Endpoints**
   - `/capabilities/verify` to validate bundle integrity and trust.
   - `/capabilities/quarantine` to register a capability for canary.
   - `/capabilities/quarantine/ready` to check readiness for promotion.

## Wire-up
- Mount router in `api/main.py`:
  ```python
  from api.routers import capabilities
  app.include_router(capabilities.router)
  ```
- Load the new OPA policies (auto_adopt + quarantine_gate).
- When `ready_to_promote` AND policy allows, move capability from quarantine into your Router/Meta-Conductor via your existing integration path.
