import subprocess, shlex
from typing import Dict

class CosignSigner:
    def __init__(self, cosign_bin: str = "cosign", key_ref: str = "cosign.key"):
        self.cosign_bin = cosign_bin
        self.key_ref = key_ref

    def sign_blob(self, artifact_path: str, signature_out: str) -> Dict:
        cmd = f"{self.cosign_bin} sign-blob --key {shlex.quote(self.key_ref)} --output-signature {shlex.quote(signature_out)} {shlex.quote(artifact_path)}"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            return {"ok": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": e.output}
