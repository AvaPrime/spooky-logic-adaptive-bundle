from typing import Dict

def supply_chain_score(sbom_ok: bool, provenance_ok: bool, cosign_ok: bool, rekor_ok: bool, max_vuln_severity: str) -> float:
    """
    Calculates the supply chain score for a capability.

    Args:
        sbom_ok (bool): Whether the SBOM is valid.
        provenance_ok (bool): Whether the provenance is valid.
        cosign_ok (bool): Whether the cosign signature is valid.
        rekor_ok (bool): Whether the rekor entry is valid.
        max_vuln_severity (str): The maximum vulnerability severity.

    Returns:
        float: The calculated supply chain score.
    """
    # naive scoring: each OK adds points, severity subtracts
    score = 0.0
    score += 0.25 if sbom_ok else 0.0
    score += 0.25 if provenance_ok else 0.0
    score += 0.25 if cosign_ok else 0.0
    score += 0.15 if rekor_ok else 0.0
    sev_penalty = {"NONE":0.0,"LOW":0.05,"MEDIUM":0.10,"HIGH":0.20,"CRITICAL":0.35}.get(max_vuln_severity.upper(),0.20)
    score = max(0.0, min(1.0, score - sev_penalty))
    return round(score, 3)

def trust_tier(score: float) -> str:
    """
    Determines the trust tier for a given score.

    Args:
        score (float): The score to determine the trust tier for.

    Returns:
        str: The trust tier.
    """
    if score >= 0.85: return "A"
    if score >= 0.70: return "B"
    if score >= 0.50: return "C"
    return "D"
