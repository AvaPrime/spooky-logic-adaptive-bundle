import pytest
from unittest.mock import AsyncMock, patch
from orchestrator.playbook_exec import run_playbook

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_clients():
    """Mocks the LLM and MHE clients."""
    with patch('orchestrator.playbook_exec.llm_client', new_callable=AsyncMock) as mock_llm, \
         patch('orchestrator.playbook_exec.mhe_client', new_callable=AsyncMock) as mock_mhe:

        mock_llm.call_llm.side_effect = [
            {"text": "interpreted_goal", "confidence": 0.9},  # route
            {"text": "solution", "confidence": 0.8},          # solve
            {"text": "critique", "confidence": 0.7},          # validate
        ]
        mock_mhe.hybrid_search.return_value = {"context": "retrieved_context"}

        yield mock_llm, mock_mhe

@pytest.fixture
def mock_playbook():
    """Provides a mock playbook."""
    return {
        'steps': [
            {'route': 'navigator'},
            {'retrieve': 'mhe.hybrid_search'},
            {'solve': 'primary_agent'},
            {'validate': 'validator'},
            {'decide': 'accept_if(conf>=0.5)'},
        ]
    }

async def test_run_playbook_success(mock_clients, mock_playbook):
    """Tests a successful run of a playbook."""
    with patch('orchestrator.playbook_exec.load_playbook', return_value=mock_playbook):
        result = await run_playbook('test_playbook', 'test_goal', 1.0, 1)

        assert result['status'] == 'Success'
        assert result['answer'] == 'solution'
        assert result['score'] > 0

async def test_run_playbook_rejected(mock_clients, mock_playbook):
    """Tests a playbook run that is rejected by the decide step."""
    mock_playbook['steps'][4] = {'decide': 'accept_if(conf>=0.9)'} # Set a high threshold

    with patch('orchestrator.playbook_exec.load_playbook', return_value=mock_playbook):
        result = await run_playbook('test_playbook', 'test_goal', 1.0, 1)

        assert result['status'] == 'Rejected'
        assert 'rejected due to low confidence score' in result['answer']
