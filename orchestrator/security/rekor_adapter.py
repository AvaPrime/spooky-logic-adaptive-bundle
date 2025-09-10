import subprocess, json, shlex
from typing import Dict

class RekorVerifier:
    def __init__(self, rekor_cli: str = "rekor-cli", rekor_url: str = "https://rekor.sigstore.dev"):
        self.rekor_cli = rekor_cli
        self.rekor_url = rekor_url

    def verify_inclusion(self, artifact_sha256: str) -> Dict:
        # Looks up an entry by SHA and returns whether inclusion proof exists
        cmd = f"{self.rekor_cli} get --rekor_server {shlex.quote(self.rekor_url)} --sha {shlex.quote(artifact_sha256)} --format json"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            data = json.loads(out or "{}")
            # naive check: presence indicates inclusion; production should verify proof
            return {"ok": True, "included": True, "entry": data}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "included": False, "error": e.output}
