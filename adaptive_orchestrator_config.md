# Adaptive Orchestrator Integration Configuration

This guide shows how to integrate the Policy Engine and Absorption API into your Codessian infrastructure for a complete Adaptive Orchestration system.

## System Architecture Integration

```yaml
# config/adaptive_orchestrator.yaml
adaptive_orchestrator:
  # Core system configuration
  core:
    orchestrator_id: "codessian_primary"
    adaptation_enabled: true
    learning_rate: 0.2
    confidence_threshold: 0.75
    
  # Policy Engine Configuration  
  policy_engine:
    config_path: "config/policies.yaml"
    evaluation_interval_seconds: 300  # 5 minutes
    max_concurrent_adaptations: 3
    learning_enabled: true
    rule_adaptation_enabled: true
    
  # Absorption API Configuration
  absorption_api:
    discovery_enabled: true
    discovery_interval_hours: 24
    testing_interval_hours: 6
    integration_threshold: 0.15  # 15% improvement required
    trial_period_days: 7
    max_parallel_tests: 3
    
    # Discovery sources
    discovery_sources:
      model_hubs:
        - "huggingface"
        - "replicate"
      api_directories:
        - "https://api.apis.guru/v2/list.json"
      custom_endpoints: []
    
    # Testing configuration
    testing:
      max_tests_per_capability: 10
      test_timeout_seconds: 30
      baseline_comparison_required: true
      
  # Integration with existing Codessian components
  codessian_integration:
    memory_harvester_engine:
      endpoint: "http://mhe-service:8080"
      store_adaptations: true
      store_test_results: true
      
    temporal_workflows:
      workflow_queue: "adaptive_orchestration"
      activity_timeout_seconds: 300
      
    metrics_collection:
      prometheus_endpoint: "http://prometheus:9090"
      custom_metrics_enabled: true
      
# Policies Configuration
policies:
  # Agent Performance Policies
  - name: "math_agent_performance_degradation"
    trigger: "performance_degradation"
    conditions:
      - metric: "agents.math.accuracy"
        operator: "<"
        threshold: 0.85
        time_window: "2h"
        min_samples: 10
      - metric: "agents.math.error_rate"
        operator: ">"
        threshold: 0.15
        time_window: "1h"
    action: "swap_agent"
    parameters:
      agent_type: "math"
      replacement_strategy: "best_available"
      fallback_agents: ["wolfram_alpha_api", "sympy_agent"]
    priority: 8
    cooldown_minutes: 120
    confidence_threshold: 0.8
    
  - name: "code_generation_failure_pattern"
    trigger: "failure_pattern"
    conditions:
      - metric: "agents.coder.syntax_errors"
        operator: ">"
        threshold: 3
        time_window: "30m"
      - metric: "agents.coder.execution_failures"  
        operator: ">"
        threshold: 2
        time_window: "30m"
    action: "enable_debate_mode"
    parameters:
      task_types: ["code_generation", "debugging"]
      participants: ["primary_coder", "code_critic", "syntax_validator"]
    priority: 7
    cooldown_minutes: 60
    
  # Cost Control Policies  
  - name: "daily_cost_threshold_breach"
    trigger: "cost_threshold"
    conditions:
      - metric: "daily_cost_usd"
        operator: ">"
        threshold: 1000.0
      - metric: "hourly_burn_rate"
        operator: ">"
        threshold: 50.0
        time_window: "1h"
    action: "adjust_routing"
    parameters:
      routing_strategy: "cost_optimized"
      prefer_lightweight_models: true
      cost_weight: 0.6
      quality_weight: 0.4
    priority: 9
    max_executions_per_day: 5
    
  # Quality Assurance Policies
  - name: "validation_disagreement_spike"
    trigger: "accuracy_drop"
    conditions:
      - metric: "validation.disagreement_rate"
        operator: ">"
        threshold: 0.3
        time_window: "20m"
        min_samples: 5
      - metric: "user_satisfaction_score"
        operator: "<"
        threshold: 7.0
        time_window: "1h"
    action: "modify_validation"
    parameters:
      strategy: "enhanced_consensus"
      min_validators: 3
      consensus_threshold: 0.8
    priority: 8
    
  # Resource Scaling Policies
  - name: "latency_spike_response"
    trigger: "latency_spike"
    conditions:
      - metric: "avg_response_time_ms"
        operator: ">"
        threshold: 5000
        time_window: "10m"
      - metric: "queue_length"
        operator: ">"
        threshold: 100
    action: "scale_resources"
    parameters:
      scale_factor: 1.5
      max_instances: 20
      scale_down_delay_minutes: 30
    priority: 6
    cooldown_minutes: 30
    
  # Absorption Integration Policies
  - name: "capability_integration_trigger"
    trigger: "experiment_success"
    conditions:
      - metric: "absorption.trial_performance_improvement"
        operator: ">"
        threshold: 0.2  # 20% improvement
      - metric: "absorption.trial_success_rate"
        operator: ">"
        threshold: 0.9
        time_window: "24h"
    action: "integrate_capability"
    parameters:
      auto_integrate: true
      create_monitoring_policy: true
    priority: 5
    
  - name: "integrated_capability_monitoring"
    trigger: "performance_degradation"
    conditions:
      - metric: "external_capabilities.{capability_id}.success_rate"
        operator: "<"
        threshold: 0.8
        time_window: "2h"
      - metric: "external_capabilities.{capability_id}.cost_efficiency"
        operator: "<"
        threshold: 0.7
    action: "evaluate_capability_removal"
    parameters:
      grace_period_hours: 6
      replacement_search_enabled: true
    priority: 6
```

## Integration Implementation

### 1. Main Orchestrator Integration

```python
# codessian/orchestrator/adaptive_orchestrator.py
from .policy_engine import AdaptivePolicyEngine
from .absorption_api import AbsorptionAPI
from .metrics_client import MetricsClient
import yaml
import asyncio

class CodessianAdaptiveOrchestrator:
    """
    Main Codessian Adaptive Orchestrator that integrates all components
    """
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize core components
        self.metrics_client = MetricsClient(
            self.config['adaptive_orchestrator']['codessian_integration']['metrics_collection']
        )
        
        self.policy_engine = AdaptivePolicyEngine(
            self.metrics_client,
            self  # Pass self as orchestrator
        )
        
        self.absorption_api = AbsorptionAPI(
            self,  # Pass self as orchestrator
            self.metrics_client,
            self.policy_engine
        )
        
        # State management
        self.agents = {}
        self.external_capabilities = {}
        self.active_workflows = {}
        
    async def initialize(self):
        """Initialize the adaptive orchestrator"""
        # Load policies
        await self.policy_engine.load_policies_from_config(
            self.config['adaptive_orchestrator']['policy_engine']['config_path']
        )
        
        # Start absorption system
        await self.absorption_api.start_absorption_loop()
        
        # Start main adaptation loop
        asyncio.create_task(self._main_adaptation_loop())
        
    async def _main_adaptation_loop(self):
        """Main loop that coordinates policy evaluation and execution"""
        interval = self.config['adaptive_orchestrator']['policy_engine']['evaluation_interval_seconds']
        
        while True:
            try:
                # Evaluate policies
                triggered_policies = await self.policy_engine.evaluate_policies()
                
                # Execute adaptations with concurrency limit
                max_concurrent = self.config['adaptive_orchestrator']['policy_engine']['max_concurrent_adaptations']
                semaphore = asyncio.Semaphore(max_concurrent)
                
                async def execute_with_limit(policy):
                    async with semaphore:
                        return await self.policy_engine.execute_adaptation(policy)
                
                if triggered_policies:
                    adaptation_tasks = [execute_with_limit(policy) for policy in triggered_policies]
                    results = await asyncio.gather(*adaptation_tasks, return_exceptions=True)
                    
                    # Log results
                    for policy, result in zip(triggered_policies, results):
                        if isinstance(result, Exception):
                            self.logger.error(f"Adaptation {policy.name} failed: {result}")
                        else:
                            self.logger.info(f"Adaptation {policy.name} completed: {result.get('success', False)}")
                
                # Periodic rule learning and adaptation
                if self.config['adaptive_orchestrator']['policy_engine']['rule_adaptation_enabled']:
                    await self.policy_engine.adapt_rules_based_on_learning()
                
            except Exception as e:
                self.logger.error(f"Error in main adaptation loop: {e}")
            
            await asyncio.sleep(interval)
    
    # Orchestrator methods that policy engine and absorption API will call
    
    async def swap_agent(self, agent_type: str, replacement: str) -> Dict[str, Any]:
        """Swap a failing agent with a replacement"""
        old_agent = self.agents.get(agent_type)
        
        if replacement == "best_available":
            # Find best available agent for this type
            replacement = await self._find_best_agent(agent_type)
        
        # Implement agent swapping logic
        new_agent = await self._create_agent(agent_type, replacement)
        
        if new_agent:
            self.agents[agent_type] = new_agent
            
            # Store change in MHE for learning
            await self._record_agent_change(agent_type, old_agent, new_agent)
            
            return {"success": True, "old_agent": str(old_agent), "new_agent": str(new_agent)}
        
        return {"success": False, "error": "Failed to create replacement agent"}
    
    async def enable_debate_mode(self, task_types: List[str]) -> Dict[str, Any]:
        """Enable debate mode for specified task types"""
        # Update routing to use debate workflows for these task types
        for task_type in task_types:
            self.active_workflows[task_type] = "debate_mode"
        
        return {"success": True, "enabled_for": task_types}
    
    async def integrate_external_capability(self, config: Dict[str, Any]) -> bool:
        """Integrate an external capability"""
        capability_id = config['capability_id']
        
        # Create capability wrapper
        capability = await self._create_capability_wrapper(config)
        
        if capability:
            self.external_capabilities[capability_id] = capability
            
            # Update routing to include new capability
            await self._update_routing_for_capability(capability_id, config['task_types'])
            
            # Record integration in MHE
            await self._record_capability_integration(config)
            
            return True
        
        return False
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the adaptive orchestrator"""
        policy_status = await self.policy_engine.learner.rule_effectiveness
        absorption_status = await self.absorption_api.get_absorption_status()
        
        return {
            "active_agents": len(self.agents),
            "external_capabilities": len(self.external_capabilities),
            "active_workflows": self.active_workflows,
            "policy_effectiveness": policy_status,
            "absorption_system": absorption_status,
            "recent_adaptations": await self._get_recent_adaptations()
        }
```

### 2. Metrics Collection Integration

```python
# codessian/metrics/adaptive_metrics.py
class AdaptiveMetricsCollector:
    """Enhanced metrics collection for adaptive orchestration"""
    
    def __init__(self, prometheus_client, mhe_client):
        self.prometheus = prometheus_client
        self.mhe = mhe_client
        
        # Define custom metrics for adaptation
        self.adaptation_counter = Counter('adaptations_total', 'Total adaptations executed', ['type', 'success'])
        self.capability_performance = Histogram('capability_performance', 'Capability performance metrics', ['capability_id', 'metric_type'])
        self.policy_effectiveness = Gauge('policy_effectiveness', 'Policy effectiveness score', ['policy_name'])
    
    async def collect_adaptive_metrics(self) -> Dict[str, Any]:
        """Collect all metrics relevant to adaptive orchestration"""
        base_metrics = await self.collect_base_metrics()
        
        # Add adaptive-specific metrics
        adaptive_metrics = {
            **base_metrics,
            'agents': await self._collect_agent_metrics(),
            'policies': await self._collect_policy_metrics(), 
            'capabilities': await self._collect_capability_metrics(),
            'absorption': await self._collect_absorption_metrics()
        }
        
        return adaptive_metrics
    
    async def _collect_agent_metrics(self) -> Dict[str, Any]:
        """Collect per-agent performance metrics"""
        # Implementation depends on your agent monitoring setup
        return {
            'math': {'accuracy': 0.87, 'failure_rate': 0.13, 'avg_latency': 1200},
            'coder': {'success_rate': 0.92, 'syntax_errors': 2, 'execution_failures': 1},
            'retriever': {'relevance_score': 0.85, 'recall': 0.78}
        }
    
    async def _collect_policy_metrics(self) -> Dict[str, Any]:
        """Collect policy execution and effectiveness metrics"""
        return {
            'total_evaluations_last_hour': 12,
            'triggered_policies_last_hour': 3,
            'successful_adaptations_last_hour': 2
        }
```

### 3. Temporal Workflow Integration

```python
# codessian/workflows/adaptive_workflows.py
from temporalio import workflow, activity
from datetime import timedelta

@workflow.defn
class AdaptiveOrchestrationWorkflow:
    """Main workflow for adaptive orchestration"""
    
    @workflow.run
    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Standard orchestration with adaptive routing
        
        # 1. Check for active adaptations
        active_adaptations = await workflow.execute_activity(
            check_active_adaptations,
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # 2. Route based on current configuration and adaptations
        routing_config = await workflow.execute_activity(
            get_current_routing_config,
            start_to_close_timeout=timedelta(seconds=5)
        )
        
        # 3. Execute with adapted configuration
        result = await workflow.execute_activity(
            execute_with_adaptive_routing,
            request,
            routing_config,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # 4. Record metrics for future adaptation
        await workflow.execute_activity(
            record_execution_metrics,
            request,
            result,
            routing_config,
            start_to_close_timeout=timedelta(seconds=15)
        )
        
        return result

@activity.defn
async def execute_with_adaptive_routing(request: Dict, config: Dict) -> Dict:
    """Execute request with current adaptive routing configuration"""
    # Your existing orchestration logic, but using adaptive configuration
    pass
```

## Deployment Configuration

### Docker Compose Integration

```yaml
# docker-compose.adaptive.yml
version: '3.8'
services:
  adaptive-orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.adaptive
    environment:
      - CONFIG_PATH=/app/config/adaptive_orchestrator.yaml
      - MHE_ENDPOINT=http://mhe:8080
      - TEMPORAL_HOST=temporal:7233
      - PROMETHEUS_ENDPOINT=http://prometheus:9090
    volumes:
      - ./config:/app/config
    depends_on:
      - mhe
      - temporal
      - prometheus
    
  # Enhanced monitoring for adaptive system
  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./monitoring/grafana/adaptive-dashboards:/var/lib/grafana/dashboards
      - ./monitoring/grafana/adaptive-datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/var/lib/grafana/dashboards/adaptive-orchestrator.json
```

### Kubernetes Deployment

```yaml
# k8s/adaptive-orchestrator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adaptive-orchestrator
spec:
  replicas: 1  # Single instance for coordination
  selector:
    matchLabels:
      app: adaptive-orchestrator
  template:
    metadata:
      labels:
        app: adaptive-orchestrator
    spec:
      containers:
      - name: adaptive-orchestrator
        image: codessian/adaptive-orchestrator:latest
        env:
        - name: CONFIG_PATH
          value: "/app/config/adaptive_orchestrator.yaml"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi" 
            cpu: "1000m"
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: secrets
          mountPath: /app/secrets
      volumes:
      - name: config
        configMap:
          name: adaptive-orchestrator-config
      - name: secrets
        secret:
          secretName: adaptive-orchestrator-secrets
```

## Monitoring and Observability

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Codessian Adaptive Orchestrator",
    "panels": [
      {
        "title": "Adaptation Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(adaptations_total[5m])",
            "legendFormat": "Adaptations per second"
          }
        ]
      },
      {
        "title": "Policy Effectiveness",
        "type": "heatmap",
        "targets": [
          {
            "expr": "policy_effectiveness",
            "legendFormat": "{{policy_name}}"
          }
        ]
      },
      {
        "title": "Capability Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "capability_performance",
            "legendFormat": "{{capability_id}}"
          }
        ]
      },
      {
        "title": "Absorption Pipeline",
        "type": "table",
        "targets": [
          {
            "expr": "absorption_pipeline_status",
            "format": "table"
          }
        ]
      }
    ]
  }
}
```

This comprehensive configuration provides:

1. **Policy-Driven Adaptation** - The system automatically responds to performance degradation, cost spikes, and quality issues
2. **Autonomous Capability Absorption** - Discovers, tests, and integrates new AI capabilities without human intervention
3. **Learning and Evolution** - Policies improve based on outcomes, and the system learns which adaptations work best
4. **Full Observability** - Complete monitoring of the adaptive process with detailed metrics and dashboards

The result is a truly adaptive orchestration system that doesn't just coordinate AI agents, but continuously evolves its coordination strategies to maintain optimal performance while absorbing competitive advantages from the broader AI ecosystem.