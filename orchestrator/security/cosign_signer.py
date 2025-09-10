import subprocess, shlex
from typing import Dict

class CosignSigner:
    """A wrapper around the cosign CLI for signing artifacts."""
    def __init__(self, cosign_bin: str = "cosign", key_ref: str = "cosign.key"):
        """
        Initializes the CosignSigner.

        Args:
            cosign_bin (str, optional): The path to the cosign binary. Defaults to "cosign".
            key_ref (str, optional): The path to the private key file. Defaults to "cosign.key".
        """
        self.cosign_bin = cosign_bin
        self.key_ref = key_ref

    def sign_blob(self, artifact_path: str, signature_out: str) -> Dict:
        """
        Signs a blob.

        Args:
            artifact_path (str): The path to the artifact to sign.
            signature_out (str): The path to write the signature to.

        Returns:
            Dict: A dictionary containing the signing result.
        """
        cmd = f"{self.cosign_bin} sign-blob --key {shlex.quote(self.key_ref)} --output-signature {shlex.quote(signature_out)} {shlex.quote(artifact_path)}"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
            return {"ok": True, "output": out}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "error": e.output}
