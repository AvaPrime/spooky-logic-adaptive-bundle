# Spooky Logic – Upgrade Pack v0.2

Drop these files into your repo (preserving paths). No existing files are overwritten.

## What this adds
- **Experiments Manager** with Welch t-test and promotion signal.
- **Absorption Shadow Trials** for safe capability testing.
- **Red-team Validator** to flag prompt-injection risks.
- **Router Learner** for adaptive candidate weighting.
- **Prometheus/Grafana**: full scrape config + Overview dashboard JSON.
- **OPA Policies** for playbook promotion/demotion.
- **Experiments API Router** for recording and summarizing A/B results.

## Wire-up (minimal edits)
1. **Mount experiments API** in `api/main.py`:
   ```python
   from fastapi import FastAPI
   from api.routers import experiments
   app = FastAPI(...)
   app.include_router(experiments.router)
   ```

2. **Point Prometheus** to `telemetry/prometheus_full.yml` (replace your compose mapping).

3. **Grafana**: import `telemetry/grafana/dashboards/spooky_overview.json`.

4. **Policy hook**: call `spooky.promotion.promote_variant` with stats in your meta-conductor to gate promotions.

5. **Router learner**: after a variant win, call
   ```python
   from orchestrator.router.learner import RouterLearner
   RouterLearner('orchestrator/router/weights.yaml').update_weights(role='coder', winner='deepseek_coder')
   ```

6. **Shadow trials**: wire `ShadowTrialRunner` around your normal execution path (10% sample ideal for start).
