import subprocess, json, shlex
from typing import Dict

class CosignVerifier:
    """A wrapper around the cosign CLI for verifying signatures and attestations.

    This class provides methods for verifying blob signatures and attestations
    using the cosign command-line tool.
    """
    def __init__(self, cosign_bin: str = "cosign"):
        """Initializes the CosignVerifier.

        Args:
            cosign_bin: The path to the cosign binary.
        """
        self.cosign_bin = cosign_bin

    def verify_blob(self, artifact_path: str, signature_path: str, public_key_path: str) -> Dict:
        """Verifies a blob signature.

        Args:
            artifact_path: The path to the artifact to verify.
            signature_path: The path to the signature file.
            public_key_path: The path to the public key file.

        Returns:
            A dictionary containing the verification result.
        """
        cmd = f"{self.cosign_bin} verify-blob --key {shlex.quote(public_key_path)} --signature {shlex.quote(signature_path)} {shlex.quote(artifact_path)} --output json"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            data = json.loads(out or "{}")
            return {"ok": True, "details": data}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": e.output}

    def verify_attestation(self, image_ref: str, public_key_path: str) -> Dict:
        """Verifies an attestation.

        Args:
            image_ref: The image reference to verify.
            public_key_path: The path to the public key file.

        Returns:
            A dictionary containing the verification result.
        """
        cmd = f"{self.cosign_bin} verify-attestation --key {shlex.quote(public_key_path)} {shlex.quote(image_ref)} --output json"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            return {"ok": True, "details": json.loads(out or "{}")}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": e.output}
