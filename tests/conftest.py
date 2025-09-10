import unittest.mock

# This patch will be started by pytest_configure and stopped by pytest_unconfigure.
mock_env_patch = unittest.mock.patch('os.getenv')

def pytest_configure(config):
    """
    Hook called by pytest before test collection.
    This is the ideal place to start mocks that need to be active
    during the import/collection phase.
    """
    mock_getenv = mock_env_patch.start()
    mock_getenv.side_effect = lambda key, default=None: {
        "OPENAI_API_KEY": "fake-openai-key",
        "ANTHROPIC_API_KEY": "fake-anthropic-key",
        "OLLAMA_BASE_URL": "http://fake-ollama:11434"
    }.get(key, default)

def pytest_unconfigure(config):
    """
    Hook called by pytest after the test session finishes.
    """
    mock_env_patch.stop()
