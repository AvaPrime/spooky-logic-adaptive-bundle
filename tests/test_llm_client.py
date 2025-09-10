import pytest
import unittest.mock
from orchestrator.clients.llm_client import LLMClient

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_config():
    """Provides a mock configuration for the LLMClient."""
    return {
        'llm_providers': {
            'ollama_base_url': 'http://mock-ollama:11434',
            'deepseek_provider_config': {
                'base_url': 'https://api.deepseek.com'
            },
            'provider_map': {
                'navigator': {'provider': 'openai', 'model': 'gpt-4o'},
                'primary_agent': {'provider': 'anthropic', 'model': 'claude-3.5-sonnet'},
                'validator': {'provider': 'ollama', 'model': 'llama3'},
                'deepseek_agent': {'provider': 'deepseek', 'model': 'deepseek-chat'},
                'unsupported': {'provider': 'unsupported_provider', 'model': 'model-x'},
                'default_agent': {'provider': 'openai', 'model': 'gpt-4o-mini'}
            }
        }
    }

@pytest.fixture
def mock_llm_client(mock_config):
    """Mocks the LLMClient and its dependencies."""
    with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data="")) as mock_file, \
         unittest.mock.patch('yaml.safe_load', return_value=mock_config) as mock_yaml, \
         unittest.mock.patch('os.getenv', return_value='fake_key') as mock_getenv:

        client = LLMClient()
        # Mock the actual client calls
        client._call_openai_compatible = unittest.mock.AsyncMock(return_value={"text": "openai_compatible response", "confidence": None})
        client._call_anthropic = unittest.mock.AsyncMock(return_value={"text": "anthropic response", "confidence": None})
        client._call_ollama = unittest.mock.AsyncMock(return_value={"text": "ollama response", "confidence": None})
        return client

async def test_call_openai_provider(mock_llm_client):
    """Tests that a role mapped to openai calls the openai_compatible method."""
    role = 'navigator'
    prompt = 'test prompt'
    result = await mock_llm_client.call_llm(role, prompt)

    mock_llm_client._call_openai_compatible.assert_called_once_with('openai', 'gpt-4o', prompt)
    mock_llm_client._call_anthropic.assert_not_called()
    mock_llm_client._call_ollama.assert_not_called()
    assert result["text"] == "openai_compatible response"

async def test_call_deepseek_provider(mock_llm_client):
    """Tests that a role mapped to deepseek calls the openai_compatible method."""
    role = 'deepseek_agent'
    prompt = 'test prompt'
    result = await mock_llm_client.call_llm(role, prompt)

    mock_llm_client._call_openai_compatible.assert_called_once_with('deepseek', 'deepseek-chat', prompt)
    mock_llm_client._call_anthropic.assert_not_called()
    mock_llm_client._call_ollama.assert_not_called()
    assert result["text"] == "openai_compatible response"

async def test_call_anthropic_provider(mock_llm_client):
    """Tests that a role mapped to anthropic calls the anthropic method."""
    role = 'primary_agent'
    prompt = 'test prompt'
    result = await mock_llm_client.call_llm(role, prompt)

    mock_llm_client._call_anthropic.assert_called_once_with('claude-3.5-sonnet', prompt)
    mock_llm_client._call_openai_compatible.assert_not_called()
    mock_llm_client._call_ollama.assert_not_called()
    assert result["text"] == "anthropic response"

async def test_call_ollama_provider(mock_llm_client):
    """Tests that a role mapped to ollama calls the ollama method."""
    role = 'validator'
    prompt = 'test prompt'
    result = await mock_llm_client.call_llm(role, prompt)

    mock_llm_client._call_ollama.assert_called_once_with('llama3', prompt)
    mock_llm_client._call_openai_compatible.assert_not_called()
    mock_llm_client._call_anthropic.assert_not_called()
    assert result["text"] == "ollama response"

async def test_fallback_to_default_provider(mock_llm_client):
    """Tests that an unmapped role falls back to the default_agent."""
    role = 'unmapped_role'
    prompt = 'test prompt'
    result = await mock_llm_client.call_llm(role, prompt)

    mock_llm_client._call_openai_compatible.assert_called_once_with('openai', 'gpt-4o-mini', prompt)
    mock_llm_client._call_anthropic.assert_not_called()
    mock_llm_client._call_ollama.assert_not_called()
    assert result["text"] == "openai_compatible response"

async def test_unsupported_provider_raises_error(mock_llm_client):
    """Tests that a configured but unsupported provider raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="Provider 'unsupported_provider' is not supported."):
        await mock_llm_client.call_llm('unsupported', 'test prompt')

async def test_no_provider_configured_raises_error(mock_config):
    """Tests that ValueError is raised if a role has no mapping and no default."""
    # Create a config with no default_agent
    del mock_config['llm_providers']['provider_map']['default_agent']

    with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data="")) as mock_file, \
         unittest.mock.patch('yaml.safe_load', return_value=mock_config) as mock_yaml, \
         unittest.mock.patch('os.getenv', return_value='fake_key') as mock_getenv:

        client = LLMClient()
        with pytest.raises(ValueError, match="No LLM provider configured for role 'no_mapping_role' and no default_agent is set."):
            await client.call_llm('no_mapping_role', 'test prompt')
