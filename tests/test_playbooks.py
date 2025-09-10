import pytest
from unittest.mock import mock_open, patch
from orchestrator.playbooks import load_playbook

def test_load_playbook_success():
    """
    Tests that a playbook is loaded and parsed correctly.
    """
    mock_yaml_content = """
    name: Test Playbook
    description: A playbook for testing.
    steps:
      - name: step1
        action: do_something
    """
    with patch("pathlib.Path.read_text", new_callable=mock_open, read_data=mock_yaml_content):
        playbook = load_playbook("test_playbook")
        assert playbook["name"] == "Test Playbook"
        assert len(playbook["steps"]) == 1

def test_load_playbook_file_not_found():
    """
    Tests that a FileNotFoundError is raised when the playbook file does not exist.
    """
    with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            load_playbook("non_existent_playbook")
