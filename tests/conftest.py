"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client."""
    client = TestClient(app)
    yield client


@pytest.fixture
def mock_temporal_client():
    """Mock Temporal client."""
    mock = AsyncMock()
    mock.start_workflow = AsyncMock(return_value=Mock(id="test-workflow-id"))
    mock.get_workflow_handle = AsyncMock()
    return mock


@pytest.fixture
def mock_opa_client():
    """Mock OPA client."""
    mock = Mock()
    mock.evaluate_policy = Mock(return_value={"result": True})
    return mock


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value="Test response")
    mock.get_cost = Mock(return_value=0.01)
    return mock


@pytest.fixture
def mock_mhe_client():
    """Mock MHE client."""
    mock = AsyncMock()
    mock.encrypt = AsyncMock(return_value=b"encrypted_data")
    mock.decrypt = AsyncMock(return_value=b"decrypted_data")
    mock.compute = AsyncMock(return_value={"result": "computed_value"})
    return mock


@pytest.fixture
def sample_submission():
    """Sample submission data for testing."""
    return {
        "prompt": "Test prompt",
        "model": "gpt-3.5-turbo",
        "max_tokens": 100,
        "temperature": 0.7,
        "metadata": {"user_id": "test-user", "session_id": "test-session"}
    }


@pytest.fixture
def sample_policy():
    """Sample policy data for testing."""
    return {
        "name": "test_policy",
        "rules": {
            "allow": True,
            "conditions": ["input.user_id == 'test-user'"]
        },
        "metadata": {"version": "1.0", "author": "test"}
    }