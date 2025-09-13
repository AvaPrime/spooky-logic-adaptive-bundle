from __future__ import annotations
import asyncio, yaml, logging, time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable

@dataclass
class TenantConfig:
    """Configuration for a tenant.

    Attributes:
        tenant_id: The ID of the tenant.
        playbook_control: The control playbook for the tenant.
        playbook_variant: The variant playbook for the tenant.
        budget_max_usd: The maximum budget in USD.
        risk_threshold: The risk threshold for choosing the variant playbook.
        absorb_sample_rate: The sample rate for absorbing external capabilities.
        ab_min_samples: The minimum number of samples for A/B testing.
        promote_guard: A dictionary of promotion guardrails.
    """
    tenant_id: str
    playbook_control: str
    playbook_variant: str
    budget_max_usd: float = 0.25
    risk_threshold: int = 3
    absorb_sample_rate: float = 0.1
    ab_min_samples: int = 20
    promote_guard: dict = field(default_factory=lambda: {"uplift":0.03, "max_cost_delta":0.1})

class TenantMetaConductor:
    """An autonomous controller that runs an adaptive loop per tenant.

    This class maintains its own experiment counters, promotion state, and
    routing tweaks, while delegating enforcement to OPA policies upstream.
    """
    def __init__(self, tenant_cfg: TenantConfig, *, record_metric: Callable[[str, float, dict], None] | None = None):
        """Initializes the TenantMetaConductor.

        Args:
            tenant_cfg: The configuration for the tenant.
            record_metric: An optional function for recording metrics.
        """
        self.cfg = tenant_cfg
        self.logger = logging.getLogger(f"TenantMetaConductor[{tenant_cfg.tenant_id}]")
        self.state: Dict[str, Any] = {
            "active_playbook": tenant_cfg.playbook_control,
            "trial_enabled": False,
            "variant_wins": 0,
            "control_wins": 0,
            "last_promotion": None,
        }
        self.results: Dict[str, list] = {"control":[], "variant":[]}
        self._running = False
        self._record = record_metric or (lambda n,v,l: None)

    async def start(self):
        """Starts the meta-conductor."""
        self._running = True
        self.logger.info("started")    

    async def stop(self):
        """Stops the meta-conductor."""
        self._running = False
        self.logger.info("stopped")    

    def choose_playbook(self, risk: int) -> str:
        """Chooses a playbook based on the risk level.

        If trial mode is enabled or the risk is above the threshold, the
        variant playbook is chosen. Otherwise, the control playbook is chosen.

        Args:
            risk: The risk level of the task.

        Returns:
            The name of the chosen playbook.
        """
        if self.state["trial_enabled"] or risk >= self.cfg.risk_threshold:
            return self.cfg.playbook_variant
        return self.cfg.playbook_control

    def record_result(self, arm: str, score: float, cost: float):
        """Records the result of a playbook execution.

        Args:
            arm: The arm of the experiment.
            score: The score of the result.
            cost: The cost of the result.
        """
        self.results["variant" if arm == "variant" else "control"].append((score, cost, time.time()))
        if arm == "variant": self.state["variant_wins"] += 1
        else: self.state["control_wins"] += 1
        self._record("tenant_result", score, {"tenant": self.cfg.tenant_id, "arm": arm})

    def summarize(self) -> Dict[str, Any]:
        """Summarizes the results of the experiments.

        Returns:
            A dictionary containing the summary of the experiments.
        """
        import statistics as st
        c = self.results["control"]; v = self.results["variant"]
        if len(c) < self.cfg.ab_min_samples or len(v) < self.cfg.ab_min_samples:
            return {"ready": False, "n_control": len(c), "n_variant": len(v)}
        cs, vs = [x[0] for x in c], [x[0] for x in v]
        cc, vc = [x[1] for x in c], [x[1] for x in v]
        uplift = (st.mean(vs) - st.mean(cs))
        cost_delta = (st.mean(vc) - st.mean(cc))
        return {"ready": True, "uplift": uplift, "cost_delta": cost_delta, "n_control": len(c), "n_variant": len(v)}

    def maybe_promote(self) -> Optional[Dict[str, Any]]:
        """Promotes the variant if it is performing better than the control.

        This method checks if the variant is ready to be promoted based on the
        promotion guardrails in the tenant configuration.

        Returns:
            A dictionary containing the promotion result, or None if not ready.
        """
        s = self.summarize()
        if not s.get("ready"): return None
        if s["uplift"] > self.cfg.promote_guard["uplift"] and s["cost_delta"] <= self.cfg.promote_guard["max_cost_delta"]:
            self.state["active_playbook"] = self.cfg.playbook_variant
            self.state["trial_enabled"] = False
            self.state["last_promotion"] = time.time()
            return {"promoted": True, **s}
        return {"promoted": False, **s}
