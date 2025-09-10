import random, yaml, pathlib

class Router:
    """A simple router for selecting playbooks and candidates."""
    _trial_flags = set()
    _external_tools = []
    @staticmethod
    def _overlay():
        """
        Loads the router overlay from a YAML file.

        Returns:
            dict: The router overlay.
        """
        y = (pathlib.Path(__file__).parent.parent / "router_overlay.yml").read_text()
        return yaml.safe_load(y)

    @classmethod
    def select_playbook(cls, risk: int) -> str:
        """
        Selects a playbook based on the risk level.

        Args:
            risk (int): The risk level of the task.

        Returns:
            str: The name of the selected playbook.
        """
        # Simple rule: low risk -> control, else variant if trial enabled
        if "variant_debate_tools" in cls._trial_flags or risk >= 3:
            return "variant_debate_tools"
        return "control_single_pass"

    @classmethod
    def enable_trial(cls, name: str):
        """
        Enables a trial for a given playbook.

        Args:
            name (str): The name of the playbook to enable a trial for.
        """
        cls._trial_flags.add(name)

    @classmethod
    def register_external_tool(cls, manifest: dict):
        """
        Registers an external tool.

        Args:
            manifest (dict): The manifest of the tool to register.
        """
        cls._external_tools.append(manifest)

    @classmethod
    def choose_candidate(cls, role: str) -> str:
        """
        Chooses a candidate for a given role.

        Args:
            role (str): The role to choose a candidate for.

        Returns:
            str: The name of the chosen candidate.
        """
        overlay = cls._overlay()
        candidates = overlay.get("roles", {}).get(role, {}).get("candidates", [])
        return random.choice(candidates) if candidates else "gpt4o_mini"
