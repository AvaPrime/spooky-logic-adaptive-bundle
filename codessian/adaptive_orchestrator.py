import asyncio, yaml, logging
from orchestrator.policy_engine import AdaptivePolicyEngine
from orchestrator.absorption_api import AbsorptionAPI

class CodessianAdaptiveOrchestrator:
    def __init__(self, config_path: str):
        self.logger = logging.getLogger(__name__)
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.metrics_client = SimpleMetricsClient(self.config['adaptive_orchestrator'].get('codessian_integration', {}).get('metrics_collection', {}))
        self.policy_engine = AdaptivePolicyEngine(self.metrics_client, self)
        self.absorption_api = AbsorptionAPI(self, self.metrics_client, self.policy_engine)
        self.agents = {}
        self.external_capabilities = {}
        self.active_workflows = {}
        self.routing_rules = {}

    async def initialize(self):
        await self.policy_engine.load_policies_from_config(self.config['adaptive_orchestrator']['policy_engine']['config_path'])
        if self.config['adaptive_orchestrator']['absorption_api']['discovery_enabled']:
            asyncio.create_task(self.absorption_api.start_absorption_loop())
        asyncio.create_task(self._main_adaptation_loop())

    async def _main_adaptation_loop(self):
        interval = self.config['adaptive_orchestrator']['policy_engine']['evaluation_interval_seconds']
        while True:
            try:
                triggered = await self.policy_engine.evaluate_policies()
                for rule in triggered[: self.config['adaptive_orchestrator']['policy_engine']['max_concurrent_adaptations']]:
                    await self.policy_engine.execute_adaptation(rule)
            except Exception as e:
                self.logger.error(f"Adaptation loop error: {e}")
            await asyncio.sleep(interval)

    async def swap_agent(self, agent_type: str, replacement: str):
        old = self.agents.get(agent_type)
        self.agents[agent_type] = {'type': agent_type, 'impl': replacement}
        return {'success': True, 'old': old, 'new': self.agents[agent_type]}

    async def enable_debate_mode(self, task_types):
        for t in task_types:
            self.active_workflows[t] = 'debate_mode'
        return {'success': True, 'workflows': self.active_workflows}

    async def update_routing_rules(self, rules: dict):
        self.routing_rules.update(rules)
        return {'success': True, 'routing_rules': self.routing_rules}

    async def scale_resources(self, factor: float):
        return {'success': True, 'scale_factor': factor}

    async def enable_caching(self, cache_types):
        return {'success': True, 'cache': cache_types}

    async def update_validation_strategy(self, strategy: str):
        self.active_workflows['validation'] = strategy
        return {'success': True}

    async def integrate_external_capability(self, config: dict) -> bool:
        cid = config.get('capability_id') or config.get('id') or f"cap-{len(self.external_capabilities)+1}"
        self.external_capabilities[cid] = config
        return True

    async def remove_external_capability(self, capability_id: str) -> bool:
        return self.external_capabilities.pop(capability_id, None) is not None

class SimpleMetricsClient:
    def __init__(self, _cfg):
        pass
    async def get_current_metrics(self):
        return {'accuracy': 0.85, 'avg_latency': 1200, 'cost_per_request': 0.02}
