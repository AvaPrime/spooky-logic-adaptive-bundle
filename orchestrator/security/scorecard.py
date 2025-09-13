from typing import Dict

def supply_chain_score(sbom_ok: bool, provenance_ok: bool, cosign_ok: bool, rekor_ok: bool, max_vuln_severity: str) -> float:
    """Calculates the supply chain score for a capability.

    This function calculates a supply chain score based on a number of factors,
    including the validity of the SBOM, provenance, cosign signature, and Rekor
    entry, as well as the maximum vulnerability severity.

    Args:
        sbom_ok: Whether the SBOM is valid.
        provenance_ok: Whether the provenance is valid.
        cosign_ok: Whether the cosign signature is valid.
        rekor_ok: Whether the Rekor entry is valid.
        max_vuln_severity: The maximum vulnerability severity.

    Returns:
        The calculated supply chain score.
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
    """Determines the trust tier for a given score.

    Args:
        score: The score to determine the trust tier for.

    Returns:
        The trust tier, which is one of "A", "B", "C", or "D".
    """
    if score >= 0.85: return "A"
    if score >= 0.70: return "B"
    if score >= 0.50: return "C"
    return "D"
