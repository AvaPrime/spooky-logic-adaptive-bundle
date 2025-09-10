from typing import Dict

def supply_chain_score(sbom_ok: bool, provenance_ok: bool, cosign_ok: bool, rekor_ok: bool, max_vuln_severity: str) -> float:
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
    if score >= 0.85: return "A"
    if score >= 0.70: return "B"
    if score >= 0.50: return "C"
    return "D"
