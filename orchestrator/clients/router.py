import random, yaml, pathlib

class Router:
    _trial_flags = set()
    _external_tools = []
    @staticmethod
    def _overlay():
        y = (pathlib.Path(__file__).parent.parent / "router_overlay.yml").read_text()
        return yaml.safe_load(y)

    @classmethod
    def select_playbook(cls, risk: int) -> str:
        # Simple rule: low risk -> control, else variant if trial enabled
        if "variant_debate_tools" in cls._trial_flags or risk >= 3:
            return "variant_debate_tools"
        return "control_single_pass"

    @classmethod
    def enable_trial(cls, name: str):
        cls._trial_flags.add(name)

    @classmethod
    def register_external_tool(cls, manifest: dict):
        cls._external_tools.append(manifest)

    @classmethod
    def choose_candidate(cls, role: str) -> str:
        overlay = cls._overlay()
        candidates = overlay.get("roles", {}).get(role, {}).get("candidates", [])
        return random.choice(candidates) if candidates else "gpt4o_mini"
