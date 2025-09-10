import subprocess, json, shlex
from typing import Dict

class CosignVerifier:
    def __init__(self, cosign_bin: str = "cosign"):
        self.cosign_bin = cosign_bin

    def verify_blob(self, artifact_path: str, signature_path: str, public_key_path: str) -> Dict:
        cmd = f"{self.cosign_bin} verify-blob --key {shlex.quote(public_key_path)} --signature {shlex.quote(signature_path)} {shlex.quote(artifact_path)} --output json"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            data = json.loads(out or "{}")
            return {"ok": True, "details": data}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": e.output}

    def verify_attestation(self, image_ref: str, public_key_path: str) -> Dict:
        cmd = f"{self.cosign_bin} verify-attestation --key {shlex.quote(public_key_path)} {shlex.quote(image_ref)} --output json"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            return {"ok": True, "details": json.loads(out or "{}")}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": e.output}
