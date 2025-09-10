"""
Adaptive Policy Engine for Codessian Orchestrator
=================================================

A dynamic rule engine that evaluates performance metrics and triggers
orchestration adaptations. Goes beyond static rules to learn and evolve
policies based on system performance.
"""

import asyncio
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
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
            value = sum(v.get('value', 0) for v in recent_values) / len(recent_values)
        
        return self._apply_operator(value, self.operator, self.threshold)
    
    def _parse_time_window(self, window: str) -> timedelta:
        """Parse time window string to timedelta"""
        if window.endswith('h'):
            return timedelta(hours=int(window[:-1]))
        elif window.endswith('d'):
            return timedelta(days=int(window[:-1]))
        elif window.endswith('m'):
            return timedelta(minutes=int(window[:-1]))
        return timedelta(hours=1)  # default
    
    def _apply_operator(self, value: Any, operator: str, threshold: Any) -> bool:
        """Apply comparison operator"""
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
        Check if rule can be executed (cooldown, limits).

        Returns:
            bool: True if the rule can be executed, False otherwise.
        """
        now = datetime.utcnow()
        
        # Check cooldown
        if (self.last_executed and 
            now - self.last_executed < timedelta(minutes=self.cooldown_minutes)):
            return False
        
        # Check daily limit
        if self.execution_count_today >= self.max_executions_per_day:
            return False
            
        return True
    
    def should_execute(self, metrics: Dict[str, Any]) -> bool:
        """
        Evaluate if all conditions are met.

        Args:
            metrics (Dict[str, Any]): The current metrics.

        Returns:
            bool: True if all conditions are met, False otherwise.
        """
        if not self.can_execute():
            return False
            
        # All conditions must be true (AND logic)
        return all(condition.evaluate(metrics) for condition in self.conditions)

class PolicyLearner:
    """Learns from policy execution outcomes to improve rules."""
    
<<<<<<< HEAD
    def __init__(self, persistence=None):
=======
    def __init__(self):
        """Initializes the PolicyLearner."""
>>>>>>> 3c4a90cdb18cd40d228da1653114b2f244bb47fd
        self.execution_history = []
        self.rule_effectiveness = {}
        self.persistence = persistence  # Database persistence layer
    
    async def record_execution(self, rule_name: str, outcome: Dict[str, Any]):
        """
        Record the outcome of a policy execution.

        Args:
            rule_name (str): The name of the rule that was executed.
            outcome (Dict[str, Any]): The outcome of the execution.
        """
        record = {
            'rule_name': rule_name,
            'timestamp': datetime.utcnow(),
            'outcome': outcome,
            'success': outcome.get('success', False),
            'improvement_score': outcome.get('improvement_score', 0)
        }
        
        # Store in database if persistence is available
        if self.persistence:
            await self.persistence.record_policy_execution(
                rule_name=rule_name,
                outcome=outcome,
                success=record['success'],
                improvement_score=record['improvement_score']
            )
        else:
            # Fallback to in-memory storage
            self.execution_history.append(record)
        
        await self._update_rule_effectiveness(rule_name, record)
    
    async def _update_rule_effectiveness(self, rule_name: str, record: Dict[str, Any]):
        """Update effectiveness metrics for a rule"""
        if rule_name not in self.rule_effectiveness:
            self.rule_effectiveness[rule_name] = {
                'success_rate': 0.0,
                'avg_improvement': 0.0,
                'execution_count': 0,
                'last_updated': datetime.utcnow()
            }
        
        stats = self.rule_effectiveness[rule_name]
        stats['execution_count'] += 1
        
        # Update success rate with exponential moving average
        alpha = 0.2  # learning rate
        stats['success_rate'] = (
            (1 - alpha) * stats['success_rate'] + 
            alpha * (1.0 if record['success'] else 0.0)
        )
        
        # Update improvement score
        stats['avg_improvement'] = (
            (1 - alpha) * stats['avg_improvement'] + 
            alpha * record['improvement_score']
        )
        
        stats['last_updated'] = datetime.utcnow()
    
    async def suggest_rule_adjustments(self, rule: PolicyRule) -> Dict[str, Any]:
        """
        Suggest adjustments to a rule based on learning.

        Args:
            rule (PolicyRule): The rule to suggest adjustments for.

        Returns:
            Dict[str, Any]: A dictionary of suggested adjustments.
        """
        if rule.name not in self.rule_effectiveness:
            return {}
        
        stats = self.rule_effectiveness[rule.name]
        suggestions = {}
        
        # If success rate is low, suggest increasing thresholds
        if stats['success_rate'] < 0.3:
            suggestions['increase_thresholds'] = True
            suggestions['increase_cooldown'] = True
        
        # If improvement is consistently low, suggest different action
        if stats['avg_improvement'] < 0.1:
            suggestions['consider_alternative_action'] = True
        
        return suggestions

class AdaptivePolicyEngine:
    """
    Main policy engine that evaluates rules and triggers adaptations.
    Learns from outcomes to improve policy effectiveness.
    """
    
<<<<<<< HEAD
    def __init__(self, metrics_client, orchestrator, persistence=None):
=======
    def __init__(self, metrics_client, orchestrator):
        """
        Initializes the AdaptivePolicyEngine.

        Args:
            metrics_client: The client for collecting metrics.
            orchestrator: The main orchestrator.
        """
>>>>>>> 3c4a90cdb18cd40d228da1653114b2f244bb47fd
        self.metrics_client = metrics_client
        self.orchestrator = orchestrator
        self.rules: List[PolicyRule] = []
        self.learner = PolicyLearner(persistence)
        self.persistence = persistence
        self.logger = logging.getLogger(__name__)
        
        # Action handlers
        self.action_handlers = {
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
        Load policies from YAML configuration.

        Args:
            config_path (str): The path to the configuration file.
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for rule_config in config.get('policies', []):
            rule = self._parse_rule_config(rule_config)
            self.rules.append(rule)
            
            # Store rule in database if persistence is available
            if self.persistence:
                await self.persistence.store_policy_rule(rule)
    
    async def load_policies_from_database(self):
        """Load policies from database"""
        if not self.persistence:
            self.logger.warning("No persistence layer configured")
            return
        
        stored_rules = await self.persistence.get_policy_rules()
        self.rules.extend(stored_rules)
        self.logger.info(f"Loaded {len(stored_rules)} policies from database")
    
    def _parse_rule_config(self, config: Dict[str, Any]) -> PolicyRule:
        """Parse a rule configuration into a PolicyRule object"""
        conditions = []
        for cond_config in config.get('conditions', []):
            condition = PolicyCondition(
                metric=cond_config['metric'],
                operator=cond_config['operator'],
                threshold=cond_config['threshold'],
                time_window=cond_config.get('time_window'),
                min_samples=cond_config.get('min_samples', 5)
            )
            conditions.append(condition)
        
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
        Evaluate all policies and return triggered rules.

        Returns:
            List[PolicyRule]: A list of triggered policy rules.
        """
        # Get current metrics
        metrics = await self.metrics_client.get_current_metrics()
        
        triggered_rules = []
        
        for rule in self.rules:
            if rule.should_execute(metrics):
                # Check rule effectiveness before executing
                if rule.success_rate >= rule.confidence_threshold:
                    triggered_rules.append(rule)
                    self.logger.info(f"Policy triggered: {rule.name}")
                else:
                    self.logger.warning(
                        f"Policy {rule.name} triggered but success rate too low: {rule.success_rate}"
                    )
        
        # Sort by priority
        triggered_rules.sort(key=lambda r: r.priority, reverse=True)
        return triggered_rules
    
    async def execute_adaptation(self, rule: PolicyRule) -> Dict[str, Any]:
        """
        Execute a policy rule's adaptation.

        Args:
            rule (PolicyRule): The policy rule to execute.

        Returns:
            Dict[str, Any]: The outcome of the adaptation.
        """
        start_time = datetime.utcnow()
        
        try:
            # Get baseline metrics
            baseline_metrics = await self.metrics_client.get_current_metrics()
            
            # Execute the action
            handler = self.action_handlers.get(rule.action)
            if not handler:
                raise ValueError(f"No handler for action: {rule.action}")
            
            result = await handler(rule.parameters)
            
            # Wait a bit for metrics to update
            await asyncio.sleep(30)
            
            # Measure improvement
            new_metrics = await self.metrics_client.get_current_metrics()
            improvement_score = self._calculate_improvement(
                baseline_metrics, new_metrics, rule.action
            )
            
            # Update rule execution tracking
            rule.last_executed = datetime.utcnow()
            rule.execution_count_today += 1
            
            outcome = {
                'success': True,
                'improvement_score': improvement_score,
                'execution_time_seconds': (datetime.utcnow() - start_time).total_seconds(),
                'baseline_metrics': baseline_metrics,
                'new_metrics': new_metrics,
                'details': result
            }
            
            # Record for learning
            await self.learner.record_execution(rule.name, outcome)
            
            self.logger.info(
                f"Successfully executed policy {rule.name} with improvement score: {improvement_score}"
            )
            
            return outcome
            
        except Exception as e:
            outcome = {
                'success': False,
                'error': str(e),
                'improvement_score': -1.0,
                'execution_time_seconds': (datetime.utcnow() - start_time).total_seconds()
            }
            
            await self.learner.record_execution(rule.name, outcome)
            self.logger.error(f"Failed to execute policy {rule.name}: {e}")
            
            return outcome
    
    def _calculate_improvement(self, baseline: Dict, new: Dict, action: AdaptationAction) -> float:
        """Calculate improvement score based on action type"""
        improvement = 0.0
        
        if action == AdaptationAction.SWAP_AGENT:
            # Look for accuracy improvement
            if 'accuracy' in baseline and 'accuracy' in new:
                improvement = new['accuracy'] - baseline['accuracy']
        
        elif action == AdaptationAction.ENABLE_DEBATE_MODE:
            # Look for accuracy improvement minus cost increase
            accuracy_gain = new.get('accuracy', 0) - baseline.get('accuracy', 0)
            cost_increase = new.get('cost_per_request', 0) - baseline.get('cost_per_request', 0)
            improvement = accuracy_gain - (cost_increase * 0.1)  # Weight cost less
        
        elif action in [AdaptationAction.SCALE_RESOURCES, AdaptationAction.ENABLE_CACHING]:
            # Look for latency improvement
            if 'avg_latency' in baseline and 'avg_latency' in new:
                improvement = (baseline['avg_latency'] - new['avg_latency']) / baseline['avg_latency']
        
        # Normalize to [-1, 1] range
        return max(-1.0, min(1.0, improvement))
    
    async def adapt_rules_based_on_learning(self):
        """Adapt rules based on learned effectiveness."""
        for rule in self.rules:
            suggestions = await self.learner.suggest_rule_adjustments(rule)
            
            if suggestions.get('increase_thresholds'):
                # Increase thresholds by 10%
                for condition in rule.conditions:
                    if isinstance(condition.threshold, (int, float)):
                        condition.threshold *= 1.1
                        
            if suggestions.get('increase_cooldown'):
                rule.cooldown_minutes = min(rule.cooldown_minutes * 2, 480)  # Max 8 hours
    
    # Action Handlers
    
    async def _handle_swap_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Swap a failing agent with an alternative"""
        agent_type = params['agent_type']
        replacement = params['replacement']
        
        result = await self.orchestrator.swap_agent(agent_type, replacement)
        return {'swapped_agent': agent_type, 'new_agent': replacement, 'result': result}
    
    async def _handle_enable_debate_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable debate mode for improved accuracy"""
        task_types = params.get('task_types', ['reasoning', 'analysis'])
        
        result = await self.orchestrator.enable_debate_mode(task_types)
        return {'enabled_debate_for': task_types, 'result': result}
    
    async def _handle_adjust_routing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust task routing logic"""
        routing_rules = params.get('routing_rules', {})
        
        result = await self.orchestrator.update_routing_rules(routing_rules)
        return {'updated_routing': routing_rules, 'result': result}
    
    async def _handle_scale_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scale orchestrator resources"""
        scale_factor = params.get('scale_factor', 1.5)
        
        result = await self.orchestrator.scale_resources(scale_factor)
        return {'scale_factor': scale_factor, 'result': result}
    
    async def _handle_enable_caching(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable intelligent caching"""
        cache_types = params.get('cache_types', ['embeddings', 'responses'])
        
        result = await self.orchestrator.enable_caching(cache_types)
        return {'enabled_caching': cache_types, 'result': result}
    
    async def _handle_modify_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Modify validation strategy"""
        validation_strategy = params.get('strategy', 'enhanced')
        
        result = await self.orchestrator.update_validation_strategy(validation_strategy)
        return {'validation_strategy': validation_strategy, 'result': result}
    
    async def _handle_update_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent prompts based on performance"""
        prompt_updates = params.get('prompt_updates', {})
        
        result = await self.orchestrator.update_prompts(prompt_updates)
        return {'updated_prompts': prompt_updates, 'result': result}
    
    async def _handle_integrate_capability(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate a new external capability"""
        capability_config = params.get('capability_config', {})
        
        result = await self.orchestrator.integrate_external_capability(capability_config)
        return {'integrated_capability': capability_config, 'result': result}


# Example policy configuration
EXAMPLE_POLICIES = """
policies:
  - name: "math_agent_accuracy_degradation"
    trigger: "performance_degradation"
    conditions:
      - metric: "agents.math.accuracy"
        operator: "<"
        threshold: 0.85
        time_window: "2h"
        min_samples: 10
      - metric: "agents.math.failure_rate"
        operator: ">"
        threshold: 0.15
        time_window: "1h"
    action: "swap_agent"
    parameters:
      agent_type: "math"
      replacement: "enhanced_math_model"
    priority: 8
    cooldown_minutes: 120
    
  - name: "cost_threshold_breach"
    trigger: "cost_threshold"
    conditions:
      - metric: "daily_cost"
        operator: ">"
        threshold: 500.0
      - metric: "cost_per_request"
        operator: ">"
        threshold: 0.50
        time_window: "1h"
    action: "adjust_routing"
    parameters:
      routing_rules:
        prefer_lightweight_models: true
        cost_weight: 0.4
    priority: 9
    
  - name: "high_disagreement_validation"
    trigger: "accuracy_drop"  
    conditions:
      - metric: "validation.disagreement_rate"
        operator: ">"
        threshold: 0.25
        time_window: "30m"
        min_samples: 5
    action: "enable_debate_mode"
    parameters:
      task_types: ["reasoning", "analysis", "creative"]
    priority: 7
    cooldown_minutes: 60
"""

if __name__ == "__main__":
    # Example usage
    async def main():
        # Mock metrics client and orchestrator
        class MockMetricsClient:
            async def get_current_metrics(self):
                return {
                    'agents.math.accuracy': 0.82,
                    'agents.math.failure_rate': 0.18,
                    'daily_cost': 520.0,
                    'cost_per_request': 0.55,
                    'validation.disagreement_rate': 0.28
                }
        
        class MockOrchestrator:
            async def swap_agent(self, agent_type, replacement):
                return f"Swapped {agent_type} with {replacement}"
            
            async def enable_debate_mode(self, task_types):
                return f"Enabled debate mode for {task_types}"
            
            async def update_routing_rules(self, rules):
                return f"Updated routing with {rules}"
        
        # Initialize policy engine
        policy_engine = AdaptivePolicyEngine(
            MockMetricsClient(), 
            MockOrchestrator()
        )
        
        # Save example config and load it
        with open('example_policies.yaml', 'w') as f:
            f.write(EXAMPLE_POLICIES)
        
        await policy_engine.load_policies_from_config('example_policies.yaml')
        
        # Evaluate and execute policies
        triggered_rules = await policy_engine.evaluate_policies()
        
        for rule in triggered_rules:
            print(f"Executing policy: {rule.name}")
            outcome = await policy_engine.execute_adaptation(rule)
            print(f"Outcome: {outcome}")
        
        # Demonstrate learning
        await policy_engine.adapt_rules_based_on_learning()
    
    asyncio.run(main())
"""