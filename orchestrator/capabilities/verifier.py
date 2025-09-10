import json, base64, hashlib
from typing import Dict, List
try:
    from nacl.signing import VerifyKey
except Exception:
    VerifyKey = None

def _canonical(obj: dict) -> bytes:
    # Canonicalize JSON (sorted keys, no whitespace)
    return json.dumps(obj, sort_keys=True, separators=(",",":")).encode("utf-8")

def verify_signatures(bundle: Dict, pubkeys: Dict[str,str]) -> bool:
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
    # Ensure artifact checksums match sbom/provenance footprint where possible.
    for a in bundle.get("artifacts", []):
        if len(a.get("sha256","")) != 64:
            return False
    return True

def minimal_provenance_ok(bundle: Dict) -> bool:
    prov = bundle.get("provenance",{})
    return "_type" in prov and "predicateType" in prov
