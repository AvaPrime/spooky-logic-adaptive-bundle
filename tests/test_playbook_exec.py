import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from orchestrator.playbook_exec import run_playbook

@pytest.mark.asyncio
async def test_run_playbook_with_none_confidence():
    """
    Tests that run_playbook can handle 'None' for confidence scores
    without raising a TypeError.
    """
    playbook_name = "test_playbook"
    goal = "test goal"
    budget = 1.0
    risk = 1

    # Mock playbook
    mock_playbook = {
        'steps': [
            {'solve': 'primary_agent'},
            {'validate': 'validator'}
        ]
    }

    # Mock llm_client.call_llm to return None for confidence
    mock_llm_result = {'text': 'some text', 'confidence': None}

    with patch('orchestrator.playbook_exec.load_playbook', return_value=mock_playbook) as mock_load:
        with patch('orchestrator.clients.llm_client.call_llm', new_callable=AsyncMock, return_value=mock_llm_result) as mock_call_llm:
            # We don't mock mhe_client as it's not called in this playbook
            result = await run_playbook(playbook_name, goal, budget, risk)

    # Assert that the playbook ran to completion
    assert result['status'] == 'Success'
    # Assert that the score was calculated as 0.0
    assert result['score'] == 0.0
    # Assert that load_playbook was called
    mock_load.assert_called_once_with(playbook_name)
    # Assert that llm_client.call_llm was called for both solve and validate
    assert mock_call_llm.call_count == 2
