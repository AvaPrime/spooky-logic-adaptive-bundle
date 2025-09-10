# Spooky Logic – Upgrade Pack v0.9

Only **new** files; no overwrites.

## Adds
1) **Cosign/Rekor adapters** for bundle and attestation verification.
2) **Auto-rollback controller** with staged, timed blast-radius throttling.
3) **Supply-chain scorecard** and **trust-aware router** that influences candidate weights.
4) **API routers** for supply-chain scoring and rollback operations.

## Wiring
- Ensure `cosign` and `rekor-cli` are available in the runtime if you plan to use the adapters.
- Integrate cosign/rekor checks in your v0.7 verification pipeline:
  - Gate adoption unless both cosign and rekor checks are green.
- Include routers in `api/main.py`:
  ```python
  from api.routers import supplychain, rollback
  app.include_router(supplychain.router)
  app.include_router(rollback.router)
  ```
- Trust-aware routing:
  - After computing `score`, call `TrustAwareRouter.apply_trust_modifier(role, candidate, score)` to bias routing.
- Rollback:
  - On incident, call `/rollback/start` for the problematic capability and periodically `/rollback/tick` (or have a worker drive it).
