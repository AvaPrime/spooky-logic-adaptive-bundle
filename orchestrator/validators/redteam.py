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
    """Scans text for prompt injection patterns.

    This function uses a list of regular expressions to scan for common prompt
    injection patterns in the given text.

    Args:
        text: The text to scan.

    Returns:
        A dictionary containing the risk score and a list of matched patterns.
        The risk score is a float between 0.0 and 1.0, where a higher score
        indicates a higher risk of prompt injection. The list of matched
        patterns contains the regular expressions that were found in the text.
    """
    findings = []
    score = 0.0
    for pat in INJECTION_PATTERNS:
        if re.search(pat, text, re.I):
            findings.append(pat)
            score += 0.25
    return {"risk_score": min(1.0, score), "matches": findings}
