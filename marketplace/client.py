import hashlib, json, requests, base64
from typing import Dict, Tuple
try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
except Exception:
    VerifyKey = None

def verify_manifest(manifest: Dict, public_key_hex: str) -> bool:
    """
    Verifies the signature of a marketplace manifest.

    Args:
        manifest (Dict): The manifest to verify.
        public_key_hex (str): The public key to use for verification.

    Returns:
        bool: True if the signature is valid, False otherwise.

    Raises:
        RuntimeError: If PyNaCl is not installed.
    """
    if not VerifyKey:
        raise RuntimeError("PyNaCl not installed. pip install pynacl")
    sig_b64 = manifest["signature"]
    sig = base64.b64decode(sig_b64)
    pk = VerifyKey(bytes.fromhex(public_key_hex))
    payload = json.dumps({k:v for k,v in manifest.items() if k != "signature"}, sort_keys=True).encode("utf-8")
    try:
        pk.verify(payload, sig)
        return True
    except BadSignatureError:
        return False

def download_and_sha256(url: str) -> Tuple[str, bytes]:
    """
    Downloads a file from a URL and calculates its SHA256 hash.

    Args:
        url (str): The URL to download the file from.

    Returns:
        Tuple[str, bytes]: A tuple containing the SHA256 hash and the content of the file.
    """
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    h = hashlib.sha256(r.content).hexdigest()
    return h, r.content
