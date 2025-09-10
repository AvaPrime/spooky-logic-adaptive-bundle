import hashlib, json, requests, base64
from typing import Dict
try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
except Exception:
    VerifyKey = None

def verify_manifest(manifest: Dict, public_key_hex: str) -> bool:
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

def download_and_sha256(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    h = hashlib.sha256(r.content).hexdigest()
    return h, r.content
