"""
Marketplace Client Utilities
============================

This module provides utility functions for interacting with the Codessian
Marketplace. It includes functions for verifying the cryptographic signature
of a manifest file and for securely downloading content.
"""
import hashlib
import json
import requests
import base64
from typing import Dict, Tuple

try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
except ImportError:
    VerifyKey = None

def verify_manifest(manifest: Dict, public_key_hex: str) -> bool:
    """
    Verifies the cryptographic signature of a marketplace manifest.

    This function reconstructs the payload from the manifest (excluding the
    signature itself), decodes the signature, and uses the provided public
    key to verify the payload's integrity and authenticity.

    Args:
        manifest (Dict): The parsed JSON manifest object. The object must
            contain a 'signature' key with a base64-encoded signature.
        public_key_hex (str): The hexadecimal representation of the public
            verification key.

    Returns:
        bool: True if the signature is valid for the given manifest and
            public key, False otherwise.

    Raises:
        RuntimeError: If the PyNaCl library is not installed, as it is
            required for signature verification.
    """
    if not VerifyKey:
        raise RuntimeError("PyNaCl not installed. `pip install pynacl`")

    sig_b64 = manifest["signature"]
    signature_bytes = base64.b64decode(sig_b64)

    verify_key = VerifyKey(bytes.fromhex(public_key_hex))

    # The payload is the JSON-encoded manifest, sorted by key, without the signature.
    payload = json.dumps(
        {k: v for k, v in manifest.items() if k != "signature"},
        sort_keys=True
    ).encode("utf-8")

    try:
        verify_key.verify(payload, signature_bytes)
        return True
    except BadSignatureError:
        return False

def download_and_sha256(url: str) -> Tuple[str, bytes]:
    """
    Downloads a file and simultaneously calculates its SHA256 hash.

    This function ensures that the downloaded content can be verified against
    a known hash for integrity. It fetches the content from the given URL.

    Args:
        url (str): The URL from which to download the file.

    Returns:
        Tuple[str, bytes]: A tuple where the first element is the hex-encoded
        SHA256 hash of the content, and the second element is the raw
        content in bytes.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the
            download, such as a network error or an HTTP error status code.
    """
    r = requests.get(url, timeout=20)
    r.raise_for_status()

    content_hash = hashlib.sha256(r.content).hexdigest()

    return content_hash, r.content
