import subprocess, shlex
from typing import Dict

class CosignSigner:
    """A wrapper around the cosign CLI for signing artifacts.

    This class provides a method for signing blobs using the cosign
    command-line tool.
    """
    def __init__(self, cosign_bin: str = "cosign", key_ref: str = "cosign.key"):
        """Initializes the CosignSigner.

        Args:
            cosign_bin: The path to the cosign binary.
            key_ref: The path to the private key file.
        """
        self.cosign_bin = cosign_bin
        self.key_ref = key_ref

    def sign_blob(self, artifact_path: str, signature_out: str) -> Dict:
        """Signs a blob.

        Args:
            artifact_path: The path to the artifact to sign.
            signature_out: The path to write the signature to.

        Returns:
            A dictionary containing the signing result.
        """
        cmd = f"{self.cosign_bin} sign-blob --key {shlex.quote(self.key_ref)} --output-signature {shlex.quote(signature_out)} {shlex.quote(artifact_path)}"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            return {"ok": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": e.output}
