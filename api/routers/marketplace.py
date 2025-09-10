from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import yaml, os, hashlib, json

from marketplace.client import verify_manifest, download_and_sha256

router = APIRouter(prefix="/market", tags=["marketplace"])

class InstallReq(BaseModel):
    manifest: dict
    public_key_hex: str
    dest_dir: Optional[str] = "playbooks/market"

@router.post("/install")
def install(req: InstallReq):
    man = req.manifest
    if not verify_manifest(man, req.public_key_hex):
        raise HTTPException(400, "signature verification failed")
    sha, content = download_and_sha256(man["playbook_url"])
    if sha != man["sha256"]:
        raise HTTPException(400, "sha256 mismatch")
    os.makedirs(req.dest_dir, exist_ok=True)
    fname = os.path.join(req.dest_dir, f"{man['id']}_{man['version']}.yaml")
    with open(fname, "wb") as f:
        f.write(content)
    return {"installed": fname}
