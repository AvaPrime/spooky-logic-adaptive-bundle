from fastapi import APIRouter, HTTPException
from ..models.supplychain import (
    SupplyChainScoreRequest, SupplyChainScoreResponse,
    SupplyChainValidateRequest, SupplyChainValidateResponse,
    SupplyChainAuditRequest, SupplyChainAuditResponse,
    SupplyChainReportRequest, SupplyChainReportResponse
)
from ..models.base import ErrorResponse
from datetime import datetime
import uuid

router = APIRouter(prefix="/supplychain", tags=["supplychain"])

# In-memory storage for supply chain data
SUPPLY_CHAIN_AUDITS = {}
SUPPLY_CHAIN_REPORTS = {}

@router.post("/score", response_model=SupplyChainScoreResponse)
async def calculate_supply_chain_score(request: SupplyChainScoreRequest):
    """Calculate supply chain security score"""
    try:
        # Calculate base score based on security checks
        base_score = 0
        
        # SBOM check (20 points)
        if request.sbom_present:
            base_score += 20
        
        # Provenance check (25 points)
        if request.provenance_verified:
            base_score += 25
        
        # Code signing check (20 points)
        if request.code_signed:
            base_score += 20
        
        # Transparency log check (15 points)
        if request.transparency_log_verified:
            base_score += 15
        
        # Vulnerability severity adjustment (20 points max)
        vuln_score = 20
        if request.max_vulnerability_severity == "critical":
            vuln_score = 0
        elif request.max_vulnerability_severity == "high":
            vuln_score = 5
        elif request.max_vulnerability_severity == "medium":
            vuln_score = 10
        elif request.max_vulnerability_severity == "low":
            vuln_score = 15
        elif request.max_vulnerability_severity == "none":
            vuln_score = 20
        
        base_score += vuln_score
        
        # Determine trust tier
        if base_score >= 90:
            trust_tier = "platinum"
        elif base_score >= 75:
            trust_tier = "gold"
        elif base_score >= 60:
            trust_tier = "silver"
        elif base_score >= 40:
            trust_tier = "bronze"
        else:
            trust_tier = "untrusted"
        
        # Calculate risk level
        if base_score >= 80:
            risk_level = "low"
        elif base_score >= 60:
            risk_level = "medium"
        elif base_score >= 40:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        return SupplyChainScoreResponse(
            component_id=request.component_id,
            security_score=base_score,
            trust_tier=trust_tier,
            risk_level=risk_level,
            sbom_score=20 if request.sbom_present else 0,
            provenance_score=25 if request.provenance_verified else 0,
            signing_score=20 if request.code_signed else 0,
            transparency_score=15 if request.transparency_log_verified else 0,
            vulnerability_score=vuln_score,
            recommendations=[
                "Enable SBOM generation" if not request.sbom_present else None,
                "Implement provenance verification" if not request.provenance_verified else None,
                "Add code signing" if not request.code_signed else None,
                "Use transparency logs" if not request.transparency_log_verified else None,
                "Address vulnerabilities" if request.max_vulnerability_severity in ["critical", "high"] else None
            ],
            calculated_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate", response_model=SupplyChainValidateResponse)
async def validate_supply_chain(request: SupplyChainValidateRequest):
    """Validate supply chain integrity"""
    try:
        validation_results = []
        overall_valid = True
        
        # Validate each component
        for component in request.components:
            component_valid = True
            issues = []
            
            # Check SBOM
            if not component.get("sbom_hash"):
                issues.append("Missing SBOM hash")
                component_valid = False
            
            # Check signatures
            if not component.get("signature"):
                issues.append("Missing component signature")
                component_valid = False
            
            # Check provenance
            if not component.get("provenance_uri"):
                issues.append("Missing provenance information")
                component_valid = False
            
            validation_results.append({
                "component_id": component.get("id", "unknown"),
                "valid": component_valid,
                "issues": issues
            })
            
            if not component_valid:
                overall_valid = False
        
        # Generate validation report
        validation_id = str(uuid.uuid4())
        
        return SupplyChainValidateResponse(
            validation_id=validation_id,
            overall_valid=overall_valid,
            component_results=validation_results,
            total_components=len(request.components),
            valid_components=sum(1 for r in validation_results if r["valid"]),
            validation_timestamp=datetime.utcnow(),
            chain_integrity_score=sum(1 for r in validation_results if r["valid"]) / len(request.components) * 100 if request.components else 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audit", response_model=SupplyChainAuditResponse)
async def start_supply_chain_audit(request: SupplyChainAuditRequest):
    """Start a comprehensive supply chain audit"""
    try:
        audit_id = str(uuid.uuid4())
        
        # Create audit record
        audit_record = {
            "audit_id": audit_id,
            "target_component": request.target_component,
            "audit_scope": request.audit_scope,
            "include_dependencies": request.include_dependencies,
            "status": "in_progress",
            "started_at": datetime.utcnow(),
            "findings": [],
            "progress_percentage": 0
        }
        
        SUPPLY_CHAIN_AUDITS[audit_id] = audit_record
        
        # Simulate audit findings
        findings = [
            {
                "severity": "medium",
                "category": "dependency",
                "description": "Outdated dependency detected",
                "component": "example-lib@1.0.0",
                "recommendation": "Update to latest version"
            },
            {
                "severity": "low",
                "category": "licensing",
                "description": "License compatibility check needed",
                "component": "another-lib@2.1.0",
                "recommendation": "Verify license compatibility"
            }
        ]
        
        return SupplyChainAuditResponse(
            audit_id=audit_id,
            status="started",
            target_component=request.target_component,
            estimated_duration_minutes=30,
            audit_scope=request.audit_scope,
            include_dependencies=request.include_dependencies,
            started_at=audit_record["started_at"],
            preliminary_findings=findings[:1]  # Return first finding as preliminary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report", response_model=SupplyChainReportResponse)
async def generate_supply_chain_report(request: SupplyChainReportRequest):
    """Generate a supply chain security report"""
    try:
        report_id = str(uuid.uuid4())
        
        # Generate report data
        report_data = {
            "report_id": report_id,
            "report_type": request.report_type,
            "components": request.components,
            "generated_at": datetime.utcnow(),
            "summary": {
                "total_components": len(request.components),
                "secure_components": len(request.components) - 2,  # Simulate some issues
                "critical_issues": 0,
                "high_issues": 1,
                "medium_issues": 2,
                "low_issues": 3
            }
        }
        
        SUPPLY_CHAIN_REPORTS[report_id] = report_data
        
        # Generate download URL (simulated)
        download_url = f"/supplychain/reports/{report_id}/download"
        
        return SupplyChainReportResponse(
            report_id=report_id,
            report_type=request.report_type,
            status="completed",
            download_url=download_url,
            generated_at=report_data["generated_at"],
            expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59),  # End of day
            summary=report_data["summary"],
            format=request.format
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
