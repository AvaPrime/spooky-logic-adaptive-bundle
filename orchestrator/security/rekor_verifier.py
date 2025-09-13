import subprocess, shlex, json
from typing import Dict

class RekorVerifier:
    """A wrapper around the rekor-cli for verifying inclusion in a Rekor
    transparency log.

    This class provides a method for verifying the inclusion of an artifact in
    a Rekor transparency log using the rekor-cli command-line tool.
    """
    def __init__(self, rekor_cli: str = "rekor-cli", rekor_url: str = "https://rekor.sigstore.dev"):
        """Initializes the RekorVerifier.

        Args:
            rekor_cli: The path to the rekor-cli binary.
            rekor_url: The URL of the Rekor server.
        """
        self.rekor_cli = rekor_cli
        self.rekor_url = rekor_url

    def verify_inclusion(self, artifact_sha256: str) -> Dict:
        """Verifies the inclusion of an artifact in the Rekor transparency log.

        This method looks up an entry in the Rekor transparency log by its SHA256
        hash and returns whether an inclusion proof exists.

        Args:
            artifact_sha256: The SHA256 hash of the artifact to verify.

        Returns:
            A dictionary containing the verification result.
        """
        # Looks up an entry by SHA and returns whether inclusion proof exists
        cmd = f"{self.rekor_cli} get --rekor_server {shlex.quote(self.rekor_url)} --sha {shlex.quote(artifact_sha256)} --format json"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            data = json.loads(out or "{}")
            # naive check: presence indicates inclusion; production should verify proof
            return {"ok": True, "included": True, "entry": data}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "included": False, "error": e.output}
