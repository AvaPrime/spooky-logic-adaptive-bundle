from __future__ import annotations
import re
from typing import Dict

INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s*prompt",
    r"exfiltrate|leak|steal",
    r"disable\s+safety|jailbreak",
]

def redteam_scan(text:str) -> Dict[str, float]:
    findings = []
    score = 0.0
    for pat in INJECTION_PATTERNS:
        if re.search(pat, text, re.I):
            findings.append(pat)
            score += 0.25
    return {"risk_score": min(1.0, score), "matches": findings}
