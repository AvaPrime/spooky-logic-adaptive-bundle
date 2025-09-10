import yaml, pathlib

def load_playbook(name: str) -> dict:
    path = pathlib.Path(__file__).parent.parent.parent / "playbooks" / f"{name}.yaml"
    return yaml.safe_load(path.read_text())
