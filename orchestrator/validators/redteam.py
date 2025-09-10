from __future__ import annotations
import re
from typing import Dict, List

INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s*prompt",
    r"exfiltrate|leak|steal",
    r"disable\s+safety|jailbreak",
]

def redteam_scan(text:str) -> Dict[str, float | List[str]]:
    """
    Scans text for prompt injection patterns.

    Args:
        text (str): The text to scan.

    Returns:
        Dict[str, float | List[str]]: A dictionary containing the risk score and a list of matched patterns.
    """
    findings = []
    score = 0.0
    for pat in INJECTION_PATTERNS:
        if re.search(pat, text, re.I):
            findings.append(pat)
            score += 0.25
    return {"risk_score": min(1.0, score), "matches": findings}
