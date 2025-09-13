"""
Adaptive Policy Engine for Codessian Orchestrator
=================================================

A dynamic rule engine that evaluates performance metrics and triggers
orchestration adaptations. Goes beyond static rules to learn and evolve
policies based on system performance.
"""

import asyncio
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

# Import database persistence classes
try:
    from .governance.persistence import PolicyPersistence
except ImportError:
    # Fallback for when persistence is not available
    PolicyPersistence = None

class PolicyTrigger(Enum):
    """Enum for the different types of policy triggers."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    COST_THRESHOLD = "cost_threshold"
    FAILURE_PATTERN = "failure_pattern"
    ACCURACY_DROP = "accuracy_drop"
    LATENCY_SPIKE = "latency_spike"
    RESOURCE_CONSTRAINT = "resource_constraint"
    EXPERIMENT_SUCCESS = "experiment_success"

class AdaptationAction(Enum):
    """Enum for the different types of adaptation actions."""
    SWAP_AGENT = "swap_agent"
    ENABLE_DEBATE_MODE = "enable_debate_mode"
    ADJUST_ROUTING = "adjust_routing"
    SCALE_RESOURCES = "scale_resources"
    ENABLE_CACHING = "enable_caching"
    MODIFY_VALIDATION = "modify_validation"
    UPDATE_PROMPTS = "update_prompts"
    INTEGRATE_CAPABILITY = "integrate_capability"

@dataclass
class PolicyCondition:
    """Represents a condition that triggers policy evaluation."""
    metric: str
    operator: str  # <, >, <=, >=, ==, !=, in, contains
    threshold: Any
    time_window: Optional[str] = None  # "1h", "24h", "7d"
    min_samples: int = 5
    
    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """
        Evaluate if this condition is met.

        Args:
            metrics (Dict[str, Any]): The current metrics.

        Returns:
            bool: True if the condition is met, False otherwise.
        """
        if self.metric not in metrics:
            return False
            
        value = metrics[self.metric]
        
        # Handle time-window aggregation
        if self.time_window and isinstance(value, list):
            # Assume value is time-series data
            cutoff = datetime.utcnow() - self._parse_time_window(self.time_window)
            recent_values = [v for v in value if v.get('timestamp', datetime.min) > cutoff]
            
            if len(recent_values) < self.min_samples:
                return False
                
            # Calculate aggregate (mean for now)
            if not recent_values:
                return False
            value = sum(v.get('value', 0) for v in recent_values) / len(recent_values)
        
        return self._apply_operator(value, self.operator, self.threshold)
    
    def _parse_time_window(self, window: str) -> timedelta:
        """Parse time window string to timedelta."""
        if window.endswith('h'):
            return timedelta(hours=int(window[:-1]))
        elif window.endswith('d'):
            return timedelta(days=int(window[:-1]))
        elif window.endswith('m'):
            return timedelta(minutes=int(window[:-1]))
        return timedelta(hours=1)  # default
    
    def _apply_operator(self, value: Any, operator: str, threshold: Any) -> bool:
        """Apply comparison operator."""
        if operator == '<':
            return value < threshold
        elif operator == '>':
            return value > threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '==':
            return value == threshold
        elif operator == '!=':
            return value != threshold
        elif operator == 'in':
            return value in threshold
        elif operator == 'contains':
            return threshold in value
        return False

@dataclass
class PolicyRule:
    """A complete policy rule with conditions and actions."""
    name: str
    trigger: PolicyTrigger
    conditions: List[PolicyCondition]
    action: AdaptationAction
    parameters: Dict[str, Any]
    priority: int = 5
    cooldown_minutes: int = 60
    max_executions_per_day: int = 10
    confidence_threshold: float = 0.7
    
    # Execution tracking
    last_executed: Optional[datetime] = None
    execution_count_today: int = 0
    success_rate: float = 1.0
    
    def can_execute(self) -> bool:
        """
        Check if rule can be executed based on cooldown and daily limits.

        Returns:
            bool: True if the rule can be executed, False otherwise.
        """
        now = datetime.utcnow()
        
        if (self.last_executed and 
            now - self.last_executed < timedelta(minutes=self.cooldown_minutes)):
            return False
        
        if self.execution_count_today >= self.max_executions_per_day:
            return False
            
        return True
    
    def should_execute(self, metrics: Dict[str, Any]) -> bool:
        """
        Evaluate if all conditions for the rule are met.

        Args:
            metrics (Dict[str, Any]): The current system metrics.

        Returns:
            bool: True if all conditions are met and the rule can execute,
                False otherwise.
        """
        if not self.can_execute():
            return False
            
        return all(condition.evaluate(metrics) for condition in self.conditions)

class PolicyLearner:
    """Learns from policy execution outcomes to improve rules."""

    def __init__(self, persistence: Optional[PolicyPersistence] = None):
        """Initializes the PolicyLearner.

        Args:
            persistence (Optional[PolicyPersistence]): The database persistence
                layer. If None, history is stored in-memory.
        """
        self.execution_history: List[Dict[str, Any]] = []
        self.rule_effectiveness: Dict[str, Dict[str, Any]] = {}
        self.persistence = persistence

    async def record_execution(self, rule_name: str, outcome: Dict[str, Any]):
        """
        Record the outcome of a policy execution for learning.

        Args:
            rule_name (str): The name of the rule that was executed.
            outcome (Dict[str, Any]): The outcome of the execution, containing
                keys like 'success' and 'improvement_score'.
        """
        record = {
            'rule_name': rule_name,
            'timestamp': datetime.utcnow(),
            'outcome': outcome,
            'success': outcome.get('success', False),
            'improvement_score': outcome.get('improvement_score', 0)
        }

        if self.persistence:
            await self.persistence.record_policy_execution(
                rule_name=rule_name,
                outcome=outcome,
                success=record['success'],
                improvement_score=record['improvement_score']
            )
        else:
            self.execution_history.append(record)

        await self._update_rule_effectiveness(rule_name, record)

    async def _update_rule_effectiveness(self, rule_name: str, record: Dict[str, Any]):
        """
        Update effectiveness metrics for a rule using an exponential moving average.

        Args:
            rule_name (str): The name of the rule to update.
            record (Dict[str, Any]): The execution record containing success
                and improvement score.
        """
        if rule_name not in self.rule_effectiveness:
            self.rule_effectiveness[rule_name] = {
                'success_rate': 0.0,
                'avg_improvement': 0.0,
                'execution_count': 0,
                'last_updated': datetime.utcnow()
            }

        stats = self.rule_effectiveness[rule_name]
        stats['execution_count'] += 1
        alpha = 0.2  # Learning rate

        stats['success_rate'] = (
            (1 - alpha) * stats['success_rate'] +
            alpha * (1.0 if record['success'] else 0.0)
        )
        stats['avg_improvement'] = (
            (1 - alpha) * stats['avg_improvement'] +
            alpha * record['improvement_score']
        )
        stats['last_updated'] = datetime.utcnow()

    async def suggest_rule_adjustments(self, rule: PolicyRule) -> Dict[str, Any]:
        """
        Suggest adjustments to a rule based on its performance history.

        Args:
            rule (PolicyRule): The rule to analyze.

        Returns:
            Dict[str, Any]: A dictionary of suggested adjustments, e.g.,
            {'increase_thresholds': True}.
        """
        if rule.name not in self.rule_effectiveness:
            return {}

        stats = self.rule_effectiveness[rule.name]
        suggestions = {}

        if stats['success_rate'] < 0.3:
            suggestions['increase_thresholds'] = True
            suggestions['increase_cooldown'] = True

        if stats['avg_improvement'] < 0.1:
            suggestions['consider_alternative_action'] = True

        return suggestions

class AdaptivePolicyEngine:
    """
    Evaluates rules, triggers adaptations, and learns from outcomes.

    This class loads policies, evaluates them against system metrics, executes
    adaptation actions, and uses a learning component to improve policy
    effectiveness over time.

    Attributes:
        metrics_client: Client for collecting system metrics.
        orchestrator: The main orchestrator to apply adaptations.
        rules (List[PolicyRule]): List of loaded policy rules.
        learner (PolicyLearner): The learning component.
        persistence: Optional database persistence layer.
        logger: The logger for this class.
        action_handlers (Dict[AdaptationAction, Callable]): Maps actions to
            handler methods.
    """

    def __init__(self, metrics_client: Any, orchestrator: Any,
                 persistence: Optional[PolicyPersistence] = None):
        """
        Initializes the AdaptivePolicyEngine.

        Args:
            metrics_client: The client for collecting metrics.
            orchestrator: The main orchestrator.
            persistence (Optional[PolicyPersistence]): The database persistence
                layer.
        """
        self.metrics_client = metrics_client
        self.orchestrator = orchestrator
        self.rules: List[PolicyRule] = []
        self.learner = PolicyLearner(persistence)
        self.persistence = persistence
        self.logger = logging.getLogger(__name__)

        self.action_handlers: Dict[AdaptationAction, Callable] = {
            AdaptationAction.SWAP_AGENT: self._handle_swap_agent,
            AdaptationAction.ENABLE_DEBATE_MODE: self._handle_enable_debate_mode,
            AdaptationAction.ADJUST_ROUTING: self._handle_adjust_routing,
            AdaptationAction.SCALE_RESOURCES: self._handle_scale_resources,
            AdaptationAction.ENABLE_CACHING: self._handle_enable_caching,
            AdaptationAction.MODIFY_VALIDATION: self._handle_modify_validation,
            AdaptationAction.UPDATE_PROMPTS: self._handle_update_prompts,
            AdaptationAction.INTEGRATE_CAPABILITY: self._handle_integrate_capability,
        }

    async def load_policies_from_config(self, config_path: str):
        """
        Load policies from a YAML configuration file.

        Args:
            config_path (str): The path to the YAML configuration file.
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        for rule_config in config.get('policies', []):
            rule = self._parse_rule_config(rule_config)
            self.rules.append(rule)

            if self.persistence:
                await self.persistence.store_policy_rule(rule)

    async def load_policies_from_database(self):
        """Load all policy rules from the configured database."""
        if not self.persistence:
            self.logger.warning("No persistence layer configured.")
            return

        stored_rules = await self.persistence.get_policy_rules()
        self.rules.extend(stored_rules)
        self.logger.info(f"Loaded {len(stored_rules)} policies from database.")

    def _parse_rule_config(self, config: Dict[str, Any]) -> PolicyRule:
        """
        Parse a dictionary from config into a PolicyRule object.

        Args:
            config (Dict[str, Any]): The dictionary containing rule data.

        Returns:
            PolicyRule: The parsed PolicyRule object.
        """
        conditions = [
            PolicyCondition(
                metric=cond_config['metric'],
                operator=cond_config['operator'],
                threshold=cond_config['threshold'],
                time_window=cond_config.get('time_window'),
                min_samples=cond_config.get('min_samples', 5)
            ) for cond_config in config.get('conditions', [])
        ]
        return PolicyRule(
            name=config['name'],
            trigger=PolicyTrigger(config['trigger']),
            conditions=conditions,
            action=AdaptationAction(config['action']),
            parameters=config.get('parameters', {}),
            priority=config.get('priority', 5),
            cooldown_minutes=config.get('cooldown_minutes', 60),
            max_executions_per_day=config.get('max_executions_per_day', 10),
            confidence_threshold=config.get('confidence_threshold', 0.7)
        )

    async def evaluate_policies(self) -> List[PolicyRule]:
        """
        Evaluate policies against metrics and return triggered rules.

        Gathers metrics, checks which rules should execute based on their
        conditions and confidence, and returns them sorted by priority.

        Returns:
            List[PolicyRule]: A list of triggered rules, sorted by priority.
        """
        metrics = await self.metrics_client.get_current_metrics()
        triggered_rules = []

        for rule in self.rules:
            if rule.should_execute(metrics) and rule.success_rate >= rule.confidence_threshold:
                triggered_rules.append(rule)
                self.logger.info(f"Policy triggered: {rule.name}")
            elif rule.should_execute(metrics):
                self.logger.warning(
                    f"Policy {rule.name} triggered but success rate too low: "
                    f"{rule.success_rate:.2f} < {rule.confidence_threshold}"
                )

        triggered_rules.sort(key=lambda r: r.priority, reverse=True)
        return triggered_rules

    async def execute_adaptation(self, rule: PolicyRule) -> Dict[str, Any]:
        """
        Execute a rule's action and record the outcome.

        Calls the handler, measures the impact, and feeds the result to the
        PolicyLearner.

        Args:
            rule (PolicyRule): The policy rule to execute.

        Returns:
            Dict[str, Any]: The outcome of the adaptation, including success
            status and improvement score.
        """
        start_time = datetime.utcnow()
        try:
            baseline_metrics = await self.metrics_client.get_current_metrics()
            handler = self.action_handlers.get(rule.action)
            if not handler:
                raise ValueError(f"No handler for action: {rule.action}")

            result = await handler(rule.parameters)
            await asyncio.sleep(30)  # Wait for metrics to update

            new_metrics = await self.metrics_client.get_current_metrics()
            improvement_score = self._calculate_improvement(
                baseline_metrics, new_metrics, rule.action
            )

            rule.last_executed = datetime.utcnow()
            rule.execution_count_today += 1

            outcome = {
                'success': True,
                'improvement_score': improvement_score,
                'execution_time_seconds': (datetime.utcnow() - start_time).total_seconds(),
                'details': result
            }
            self.logger.info(
                f"Executed policy {rule.name}; improvement: {improvement_score:.2f}"
            )

        except Exception as e:
            self.logger.error(f"Failed to execute policy {rule.name}: {e}")
            outcome = {
                'success': False,
                'error': str(e),
                'improvement_score': -1.0,
                'execution_time_seconds': (datetime.utcnow() - start_time).total_seconds()
            }

        await self.learner.record_execution(rule.name, outcome)
        return outcome

    def _calculate_improvement(self, baseline: Dict, new: Dict, action: AdaptationAction) -> float:
        """
        Calculate a normalized improvement score based on the action type.

        Args:
            baseline (Dict): Metrics before the action.
            new (Dict): Metrics after the action.
            action (AdaptationAction): The action performed.

        Returns:
            float: A normalized improvement score between -1.0 and 1.0.
        """
        improvement = 0.0
        if action == AdaptationAction.SWAP_AGENT:
            improvement = new.get('accuracy', 0) - baseline.get('accuracy', 0)
        elif action == AdaptationAction.ENABLE_DEBATE_MODE:
            accuracy_gain = new.get('accuracy', 0) - baseline.get('accuracy', 0)
            cost_increase = new.get('cost_per_request', 0) - baseline.get('cost_per_request', 0)
            improvement = accuracy_gain - (cost_increase * 0.1)
        elif action in [AdaptationAction.SCALE_RESOURCES, AdaptationAction.ENABLE_CACHING]:
            base_latency = baseline.get('avg_latency', 0)
            if base_latency > 0:
                improvement = (base_latency - new.get('avg_latency', 0)) / base_latency
        return max(-1.0, min(1.0, improvement))

    async def adapt_rules_based_on_learning(self):
        """Adapt rules based on learned effectiveness from past executions."""
        for rule in self.rules:
            suggestions = await self.learner.suggest_rule_adjustments(rule)
            if suggestions.get('increase_thresholds'):
                for condition in rule.conditions:
                    if isinstance(condition.threshold, (int, float)):
                        condition.threshold *= 1.1
                self.logger.info(f"Increased thresholds for rule: {rule.name}")
            if suggestions.get('increase_cooldown'):
                rule.cooldown_minutes = min(rule.cooldown_minutes * 2, 480)
                self.logger.info(f"Increased cooldown for rule: {rule.name}")

    async def _handle_swap_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the SWAP_AGENT action."""
        result = await self.orchestrator.swap_agent(
            params['agent_type'], params['replacement']
        )
        return {'swapped': params['agent_type'], 'to': params['replacement'], 'result': result}

    async def _handle_enable_debate_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the ENABLE_DEBATE_MODE action."""
        task_types = params.get('task_types', ['reasoning', 'analysis'])
        result = await self.orchestrator.enable_debate_mode(task_types)
        return {'enabled_for': task_types, 'result': result}

    async def _handle_adjust_routing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the ADJUST_ROUTING action."""
        rules = params.get('routing_rules', {})
        result = await self.orchestrator.update_routing_rules(rules)
        return {'updated_routing': rules, 'result': result}

    async def _handle_scale_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the SCALE_RESOURCES action."""
        factor = params.get('scale_factor', 1.5)
        result = await self.orchestrator.scale_resources(factor)
        return {'scale_factor': factor, 'result': result}

    async def _handle_enable_caching(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the ENABLE_CACHING action."""
        types = params.get('cache_types', ['embeddings', 'responses'])
        result = await self.orchestrator.enable_caching(types)
        return {'enabled_caching': types, 'result': result}

    async def _handle_modify_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the MODIFY_VALIDATION action."""
        strategy = params.get('strategy', 'enhanced')
        result = await self.orchestrator.update_validation_strategy(strategy)
        return {'validation_strategy': strategy, 'result': result}

    async def _handle_update_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the UPDATE_PROMPTS action."""
        updates = params.get('prompt_updates', {})
        result = await self.orchestrator.update_prompts(updates)
        return {'updated_prompts': updates, 'result': result}

    async def _handle_integrate_capability(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the INTEGRATE_CAPABILITY action."""
        config = params.get('capability_config', {})
        result = await self.orchestrator.integrate_external_capability(config)
        return {'integrated_capability': config, 'result': result}
