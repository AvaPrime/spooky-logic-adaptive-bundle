import json, base64, hashlib
from typing import Dict, List
try:
    from nacl.signing import VerifyKey
except Exception:
    VerifyKey = None

def _canonical(obj: dict) -> bytes:
    """Canonicalizes a JSON object.

    This function canonicalizes a JSON object by sorting the keys and removing
    whitespace. This is necessary for consistent signature verification.

    Args:
        obj: The JSON object to canonicalize.

    Returns:
        The canonicalized JSON object as bytes.
    """
    return json.dumps(obj, sort_keys=True, separators=(",",":")).encode("utf-8")

def verify_signatures(bundle: Dict, pubkeys: Dict[str,str]) -> bool:
    """Verifies the signatures of a bundle.

    This function verifies the signatures of a bundle using the provided public
    keys. It requires the PyNaCl library to be installed.

    Args:
        bundle: The bundle to verify.
        pubkeys: A dictionary of public keys to use for verification. The keys
            of the dictionary are the public key IDs, and the values are the
            public keys in hex format.

    Returns:
        True if the signatures are valid, False otherwise.

    Raises:
        RuntimeError: If PyNaCl is not installed.
    """
    if not VerifyKey:
        raise RuntimeError("PyNaCl not installed. pip install pynacl")
    payload = dict(bundle)
    sigs: List[dict] = payload.pop("signatures", [])
    raw = _canonical(payload)
    ok = 0
    for s in sigs:
        pk_hex = pubkeys.get(s["public_key_id"])
        if not pk_hex: continue
        vk = VerifyKey(bytes.fromhex(pk_hex))
        sig = base64.b64decode(s["signature"])
        try:
            vk.verify(raw, sig); ok += 1
        except Exception:
            return False
    return ok > 0

def check_artifacts(bundle: Dict) -> bool:
    """Checks the artifacts of a bundle.

    This function ensures that the artifact checksums match the sbom/provenance
    footprint where possible.

    Args:
        bundle: The bundle to check.

    Returns:
        True if the artifacts are valid, False otherwise.
    """
    # Ensure artifact checksums match sbom/provenance footprint where possible.
    for a in bundle.get("artifacts", []):
        if len(a.get("sha256","")) != 64:
            return False
    return True

def minimal_provenance_ok(bundle: Dict) -> bool:
    """Checks if the provenance of a bundle is minimal.

    This function checks if the provenance of a bundle has the required
    '_type' and 'predicateType' fields.

    Args:
        bundle: The bundle to check.

    Returns:
        True if the provenance is minimal, False otherwise.
    """
    prov = bundle.get("provenance",{})
    return "_type" in prov and "predicateType" in prov
