from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime

from models.capabilities import (
    CapabilityVerificationRequest, CapabilityVerificationResponse,
    CapabilityQuarantineRequest, CapabilityQuarantineResponse,
    CapabilityPromotionCheckRequest, CapabilityPromotionCheckResponse,
    CapabilityStatsRequest, CapabilityStatsResponse
)
from models.base import ErrorResponse, SuccessResponse

router = APIRouter(prefix="/capabilities", tags=["capabilities"])

# In-memory storage (replace with database in production)
CAPABILITIES = []

@router.post("/verify", response_model=CapabilityVerificationResponse)
async def verify_capability(request: CapabilityVerificationRequest):
    """Verify a capability bundle.

    This endpoint simulates the verification of a capability bundle. It checks for the
    presence of public keys and simulates signature verification.

    Args:
        request (CapabilityVerificationRequest): The request body containing the capability
            bundle and public keys to verify.

    Returns:
        CapabilityVerificationResponse: The response containing the verification status
            and details.
    """
    try:
        # Find or create capability record
        capability = None
        for cap in CAPABILITIES:
            if cap["bundle"] == request.bundle:
                capability = cap
                break
        
        if not capability:
            capability = {
                "bundle": request.bundle,
                "status": "pending",
                "created_at": datetime.utcnow(),
                "verification_history": [],
                "quarantine_status": "active"
            }
            CAPABILITIES.append(capability)
        
        # Simulate verification process
        verification_passed = True
        verification_details = []
        
        # Check public keys
        if not request.pubkeys or len(request.pubkeys) == 0:
            verification_passed = False
            verification_details.append("No public keys provided")
        else:
            verification_details.append(f"Verified {len(request.pubkeys)} public keys")
        
        # Simulate signature verification
        if verification_passed:
            verification_details.append("Signature verification passed")
            verification_details.append("Artifact integrity check passed")
            verification_details.append("Provenance requirements met")
        
        # Update capability status
        verification_record = {
            "timestamp": datetime.utcnow(),
            "status": "verified" if verification_passed else "failed",
            "details": verification_details,
            "pubkeys_count": len(request.pubkeys)
        }
        
        capability["verification_history"].append(verification_record)
        capability["status"] = "verified" if verification_passed else "failed"
        
        return CapabilityVerificationResponse(
            verification_id=f"verify-{len(capability['verification_history'])}",
            bundle=request.bundle,
            status="verified" if verification_passed else "failed",
            verified=verification_passed,
            message="Capability verification completed",
            verification_details=verification_details,
            pubkeys_verified=len(request.pubkeys),
            timestamp=verification_record["timestamp"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quarantine", response_model=CapabilityQuarantineResponse)
async def quarantine_capability(request: CapabilityQuarantineRequest):
    """Quarantine a capability bundle.

    This endpoint quarantines a capability bundle, marking it as unavailable for use.

    Args:
        request (CapabilityQuarantineRequest): The request body containing the capability
            bundle to quarantine and the reason.

    Returns:
        CapabilityQuarantineResponse: The response containing the quarantine status.
    """
    try:
        # Find capability
        capability = None
        for cap in CAPABILITIES:
            if cap["bundle"] == request.bundle:
                capability = cap
                break
        
        if not capability:
            capability = {
                "bundle": request.bundle,
                "status": "quarantined",
                "created_at": datetime.utcnow(),
                "verification_history": [],
                "quarantine_status": "quarantined"
            }
            CAPABILITIES.append(capability)
        
        # Update quarantine status
        capability["quarantine_status"] = "quarantined"
        capability["quarantine_reason"] = request.reason
        capability["quarantine_timestamp"] = datetime.utcnow()
        capability["status"] = "quarantined"
        
        return CapabilityQuarantineResponse(
            quarantine_id=f"quar-{len([c for c in CAPABILITIES if c.get('quarantine_status') == 'quarantined'])}",
            bundle=request.bundle,
            status="quarantined",
            message="Capability successfully quarantined",
            reason=request.reason,
            quarantined_at=capability["quarantine_timestamp"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/promotion-check", response_model=CapabilityPromotionCheckResponse)
async def check_promotion_readiness(request: CapabilityPromotionCheckRequest):
    """Check if a capability is ready for promotion from quarantine.

    This endpoint checks if a quarantined capability meets the criteria for promotion.

    Args:
        request (CapabilityPromotionCheckRequest): The request body containing the
            capability ID and promotion criteria.

    Returns:
        CapabilityPromotionCheckResponse: The response containing the promotion
            readiness status.
    """
    try:
        # Find capability
        capability = None
        for cap in CAPABILITIES:
            if cap.get("capability_id") == request.capability_id:
                capability = cap
                break
        
        if not capability:
            raise HTTPException(status_code=404, detail="Capability not found")
        
        # Simulate promotion readiness check
        ready = capability.get("quarantine_status") != "quarantined" or \
               (capability.get("sample_count", 0) >= request.min_samples and 
                capability.get("success_rate", 0.0) >= request.min_success_rate)
        
        return CapabilityPromotionCheckResponse(
            ready=ready,
            capability_id=request.capability_id,
            current_success_rate=capability.get("success_rate", 0.95),
            sample_count=capability.get("sample_count", 150),
            time_in_quarantine=capability.get("quarantine_hours", 48),
            blocking_issues=[] if ready else ["Insufficient samples"],
            recommendations=["Continue monitoring"] if ready else ["Increase sample size"],
            next_check_at=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stats", response_model=CapabilityStatsResponse)
async def get_capability_stats(request: CapabilityStatsRequest):
    """Get statistics for capabilities.

    This endpoint returns statistics about the capabilities in the system.

    Args:
        request (CapabilityStatsRequest): The request body containing the filters for
            the statistics.

    Returns:
        CapabilityStatsResponse: The response containing the capability statistics.
    """
    try:
        # Filter capabilities based on request
        filtered_caps = CAPABILITIES
        if request.capability_ids:
            filtered_caps = [cap for cap in CAPABILITIES 
                           if cap.get("capability_id") in request.capability_ids]
        
        if not request.include_quarantined:
            filtered_caps = [cap for cap in filtered_caps 
                           if cap.get("quarantine_status") != "quarantined"]
        
        # Generate statistics
        total_count = len(filtered_caps)
        verified_count = len([cap for cap in filtered_caps if cap.get("status") == "verified"])
        quarantined_count = len([cap for cap in filtered_caps if cap.get("quarantine_status") == "quarantined"])
        
        stats = {
            "total_capabilities": total_count,
            "verified_capabilities": verified_count,
            "quarantined_capabilities": quarantined_count,
            "success_rate": verified_count / total_count if total_count > 0 else 0.0
        }
        
        summary = {
            "health_score": 0.85,
            "avg_verification_time": 120.5,
            "most_common_issues": ["signature_mismatch", "missing_dependencies"]
        }
        
        time_range = {
            "start": datetime.utcnow(),
            "end": datetime.utcnow()
        }
        
        return CapabilityStatsResponse(
            stats=stats,
            summary=summary,
            time_range=time_range,
            generated_at=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
