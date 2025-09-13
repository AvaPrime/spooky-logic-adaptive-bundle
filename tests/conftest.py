"""
Pytest Configuration and Shared Fixtures
=========================================

This file (`conftest.py`) is a special pytest file that allows defining
fixtures, hooks, and plugins that are shared across multiple test files.
The fixtures defined here provide reusable setup and teardown logic for
tests, such as creating mock clients, setting up a test database, and
providing sample data.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from orchestrator.main import app
from orchestrator.database import Base, get_db
from orchestrator.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """
    Creates a new asyncio event loop for the entire test session.

    This fixture ensures that asynchronous tests run in a clean event loop,
    preventing interference between test runs.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """
    Provides a `Settings` object with a test-specific configuration.

    This fixture returns a configuration that points to in-memory services
    and uses dummy API keys, ensuring that tests are isolated and do not
    depend on external services or secrets.
    """
    return Settings(
        database_url="sqlite:///:memory:",
        temporal_host="localhost",
        temporal_port=7233,
        opa_url="http://localhost:8181",
        prometheus_pushgateway_url="http://localhost:9091",
        budget_max_usd=1.0,
        openai_api_key="test-key",
        anthropic_api_key="test-key",
        mhe_service_url="http://localhost:8000"
    )


@pytest.fixture
def test_db_engine():
    """
    Creates an in-memory SQLite database engine for testing.

    This fixture sets up a fresh, in-memory database for each test function,
    ensuring a clean state and preventing data leakage between tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """
    Creates and yields a new database session for a test.

    This fixture provides a transactional scope around a test function.
    The session is closed automatically after the test completes.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(test_db_session):
    """
    Creates a FastAPI `TestClient` with the database dependency overridden.

    This fixture allows for making requests to the FastAPI application in tests
    without needing a running server. It overrides the `get_db` dependency

    to use the isolated, in-memory test database session.
    """
    def override_get_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_temporal_client():
    """
    Provides a mock `AsyncMock` for the Temporal client.

    This allows testing of components that interact with Temporal without
    requiring a live Temporal server. It returns a pre-configured mock
    for `start_workflow`.
    """
    mock = AsyncMock()
    mock.start_workflow = AsyncMock(return_value=Mock(id="test-workflow-id"))
    mock.get_workflow_handle = AsyncMock()
    return mock


@pytest.fixture
def mock_opa_client():
    """
    Provides a mock `Mock` for the OPA (Open Policy Agent) client.

    This fixture simulates the OPA client, allowing for predictable policy
    evaluation results in tests.
    """
    mock = Mock()
    mock.evaluate_policy = Mock(return_value={"result": True})
    return mock


@pytest.fixture
def mock_llm_client():
    """
    Provides a mock `AsyncMock` for a generic LLM client.

    This fixture is used to test interactions with Large Language Models
    without making actual API calls, providing controlled responses and cost data.
    """
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value="Test response")
    mock.get_cost = Mock(return_value=0.01)
    return mock


@pytest.fixture
def mock_mhe_client():
    """
    Provides a mock `AsyncMock` for the MHE (Multi-Party Homomorphic
    Encryption) client.

    This allows for testing secure computation logic without a live MHE service.
    """
    mock = AsyncMock()
    mock.encrypt = AsyncMock(return_value=b"encrypted_data")
    mock.decrypt = AsyncMock(return_value=b"decrypted_data")
    mock.compute = AsyncMock(return_value={"result": "computed_value"})
    return mock


@pytest.fixture
def sample_submission():
    """
    Provides a sample submission dictionary for use in tests.

    This fixture offers a consistent, valid data structure for tests that
    require submission data.
    """
    return {
        "prompt": "Test prompt",
        "model": "gpt-3.5-turbo",
        "max_tokens": 100,
        "temperature": 0.7,
        "metadata": {"user_id": "test-user", "session_id": "test-session"}
    }


@pytest.fixture
def sample_policy():
    """
    Provides a sample policy dictionary for use in tests.

    This fixture offers a consistent, valid data structure for tests that
    involve policy evaluation.
    """
    return {
        "name": "test_policy",
        "rules": {
            "allow": True,
            "conditions": ["input.user_id == 'test-user'"]
        },
        "metadata": {"version": "1.0", "author": "test"}
    }