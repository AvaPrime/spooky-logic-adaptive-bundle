import pytest
import yaml
from unittest.mock import MagicMock, mock_open, patch
from codessian.adaptive_orchestrator import CodessianAdaptiveOrchestrator

@pytest.fixture
def mock_config():
    """Provides a mock configuration."""
    return {
        'adaptive_orchestrator': {
            'policy_engine': {
                'config_path': '/fake/path',
                'evaluation_interval_seconds': 60,
                'max_concurrent_adaptations': 5,
            },
            'absorption_api': {
                'discovery_enabled': False,
            },
            'codessian_integration': {
                'metrics_collection': {},
            },
        }
    }

@pytest.fixture
def orchestrator(mock_config):
    """Provides an instance of the CodessianAdaptiveOrchestrator with mocked dependencies."""
    with patch('builtins.open', mock_open(read_data=yaml.dump(mock_config))), \
         patch('codessian.adaptive_orchestrator.AdaptivePolicyEngine') as MockPolicyEngine, \
         patch('codessian.adaptive_orchestrator.AbsorptionAPI') as MockAbsorptionAPI, \
         patch('codessian.adaptive_orchestrator.SimpleMetricsClient') as MockMetricsClient:

        # Instantiate the orchestrator
        orch = CodessianAdaptiveOrchestrator(config_path='dummy_path')
        orch.policy_engine = MockPolicyEngine()
        orch.absorption_api = MockAbsorptionAPI()
        orch.metrics_client = MockMetricsClient()
        return orch

def test_orchestrator_init(orchestrator):
    """Tests the initialization of the orchestrator."""
    assert orchestrator is not None
    assert orchestrator.policy_engine is not None
    assert orchestrator.absorption_api is not None
    assert orchestrator.metrics_client is not None

@pytest.mark.asyncio
async def test_swap_agent(orchestrator):
    """Tests the swap_agent method."""
    result = await orchestrator.swap_agent('test_agent', 'new_impl')
    assert result['success'] is True
    assert orchestrator.agents['test_agent']['impl'] == 'new_impl'

@pytest.mark.asyncio
async def test_enable_debate_mode(orchestrator):
    """Tests the enable_debate_mode method."""
    result = await orchestrator.enable_debate_mode(['task1', 'task2'])
    assert result['success'] is True
    assert orchestrator.active_workflows['task1'] == 'debate_mode'
    assert orchestrator.active_workflows['task2'] == 'debate_mode'

@pytest.mark.asyncio
async def test_update_routing_rules(orchestrator):
    """Tests the update_routing_rules method."""
    rules = {'rule1': 'action1'}
    result = await orchestrator.update_routing_rules(rules)
    assert result['success'] is True
    assert orchestrator.routing_rules['rule1'] == 'action1'

@pytest.mark.asyncio
async def test_scale_resources(orchestrator):
    """Tests the scale_resources method."""
    result = await orchestrator.scale_resources(1.5)
    assert result['success'] is True
    assert result['scale_factor'] == 1.5

@pytest.mark.asyncio
async def test_enable_caching(orchestrator):
    """Tests the enable_caching method."""
    cache_types = ['type1', 'type2']
    result = await orchestrator.enable_caching(cache_types)
    assert result['success'] is True
    assert result['cache'] == cache_types

@pytest.mark.asyncio
async def test_update_validation_strategy(orchestrator):
    """Tests the update_validation_strategy method."""
    result = await orchestrator.update_validation_strategy('new_strategy')
    assert result['success'] is True
    assert orchestrator.active_workflows['validation'] == 'new_strategy'

@pytest.mark.asyncio
async def test_integrate_external_capability(orchestrator):
    """Tests the integrate_external_capability method."""
    capability_config = {'id': 'cap1', 'name': 'Test Capability'}
    result = await orchestrator.integrate_external_capability(capability_config)
    assert result is True
    assert 'cap1' in orchestrator.external_capabilities

@pytest.mark.asyncio
async def test_remove_external_capability(orchestrator):
    """Tests the remove_external_capability method."""
    capability_id = 'cap1'
    orchestrator.external_capabilities[capability_id] = {'name': 'Test Capability'}
    result = await orchestrator.remove_external_capability(capability_id)
    assert result is True
    assert capability_id not in orchestrator.external_capabilities

@pytest.mark.asyncio
async def test_remove_non_existent_capability(orchestrator):
    """Tests removing a capability that does not exist."""
    result = await orchestrator.remove_external_capability('non_existent_cap')
    assert result is False
