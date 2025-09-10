"""Pytest configuration and shared fixtures."""

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
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test configuration settings."""
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
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """Create test database session."""
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
    """Create test client with dependency overrides."""
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