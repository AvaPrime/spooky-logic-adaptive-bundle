"""Pydantic models for capabilities API endpoints."""

from pydantic import Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, CapabilityModel, TimestampedModel


class VerificationStatus(str, Enum):
    """Verification status values."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class QuarantineReason(str, Enum):
    """Standard quarantine reasons."""
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    FAILED_VERIFICATION = "failed_verification"
    USER_REPORT = "user_report"
    AUTOMATED_DETECTION = "automated_detection"


class CapabilityVerificationRequest(BaseAPIModel):
    """Request model for capability verification."""
    bundle: Dict[str, Any] = Field(
        ...,
        description="Capability bundle to verify"
    )
    pubkeys: Dict[str, str] = Field(
        ...,
        min_items=1,
        description="Public keys for signature verification"
    )
    verification_level: Optional[str] = Field(
        default="standard",
        pattern=r"^(basic|standard|strict|paranoid)$",
        description="Verification strictness level"
    )
    skip_checks: Optional[List[str]] = Field(
        default_factory=list,
        description="Verification checks to skip"
    )
    additional_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional verification metadata"
    )
    
    @validator('bundle')
    def validate_bundle(cls, v):
        if not v:
            raise ValueError('Bundle cannot be empty')
        
        # Check for required bundle fields
        required_fields = ['name', 'version', 'capabilities']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Bundle missing required field: {field}')
        
        # Validate bundle size
        if len(str(v)) > 1000000:  # 1MB limit
            raise ValueError('Bundle too large (max 1MB when serialized)')
        
        return v
    
    @validator('pubkeys')
    def validate_pubkeys(cls, v):
        for key_id, pubkey in v.items():
            if not isinstance(pubkey, str) or len(pubkey.strip()) == 0:
                raise ValueError(f'Invalid public key for {key_id}')
            # Basic hex validation for public keys
            if not all(c in '0123456789abcdefABCDEF' for c in pubkey.replace(' ', '')):
                raise ValueError(f'Public key for {key_id} must be hexadecimal')
        return v
    
    @validator('skip_checks')
    def validate_skip_checks(cls, v):
        valid_checks = ['signature', 'sbom', 'provenance', 'vulnerability', 'license']
        for check in v:
            if check not in valid_checks:
                raise ValueError(f'Invalid check to skip: {check}. Valid options: {valid_checks}')
        return v


class CapabilityVerificationResponse(BaseAPIModel):
    """Response model for capability verification."""
    ok: bool = Field(..., description="Overall verification success")
    sig_ok: bool = Field(..., description="Signature verification result")
    sbom_ok: bool = Field(..., description="SBOM verification result")
    prov_ok: bool = Field(..., description="Provenance verification result")
    verification_id: Optional[str] = Field(None, description="Verification session ID")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed verification results")
    warnings: Optional[List[str]] = Field(None, description="Verification warnings")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CapabilityQuarantineRequest(CapabilityModel, TimestampedModel):
    """Request model for capability quarantine."""
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Detailed reason for quarantine"
    )
    reason_category: Optional[QuarantineReason] = Field(
        None,
        description="Categorized reason for quarantine"
    )
    canary_rate: float = Field(
        default=0.02,
        ge=0.001,
        le=1.0,
        description="Canary traffic rate (0.001 to 1.0)"
    )
    severity: Optional[str] = Field(
        default="medium",
        pattern=r"^(low|medium|high|critical)$",
        description="Quarantine severity level"
    )
    auto_promote_threshold: Optional[float] = Field(
        default=0.95,
        ge=0.5,
        le=1.0,
        description="Success rate threshold for auto-promotion"
    )
    max_quarantine_duration: Optional[int] = Field(
        default=168,  # 1 week
        ge=1,
        le=8760,  # 1 year
        description="Maximum quarantine duration in hours"
    )
    reporter: Optional[str] = Field(
        None,
        max_length=100,
        description="Entity reporting the issue"
    )
    evidence: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Supporting evidence for quarantine"
    )
    
    @validator('reason')
    def validate_reason(cls, v):
        v = ' '.join(v.split())  # Clean whitespace
        if len(v) < 10:
            raise ValueError('Reason must be at least 10 characters after cleaning whitespace')
        return v
    
    @validator('evidence')
    def validate_evidence(cls, v):
        if v and len(str(v)) > 10000:  # 10KB limit
            raise ValueError('Evidence too large (max 10KB when serialized)')
        return v


class CapabilityQuarantineResponse(BaseAPIModel):
    """Response model for capability quarantine."""
    quarantined: str = Field(..., description="Quarantined capability ID")
    canary_rate: float = Field(..., description="Applied canary rate")
    quarantine_id: Optional[str] = Field(None, description="Quarantine session ID")
    estimated_promotion_date: Optional[datetime] = Field(None, description="Estimated promotion date")
    monitoring_endpoints: Optional[List[str]] = Field(None, description="Monitoring endpoints")


class QuarantineListResponse(BaseAPIModel):
    """Response model for quarantine listing."""
    quarantined_capabilities: List[Dict[str, Any]] = Field(
        ...,
        description="List of quarantined capabilities"
    )
    total_count: int = Field(..., ge=0, description="Total quarantined capabilities")
    active_count: int = Field(..., ge=0, description="Active quarantines")
    pending_promotion: int = Field(..., ge=0, description="Capabilities pending promotion")


class CapabilityPromotionCheckRequest(CapabilityModel):
    """Request model for checking promotion readiness."""
    min_samples: Optional[int] = Field(
        default=100,
        ge=10,
        le=10000,
        description="Minimum samples required for promotion"
    )
    min_success_rate: Optional[float] = Field(
        default=0.95,
        ge=0.5,
        le=1.0,
        description="Minimum success rate for promotion"
    )
    check_duration_hours: Optional[int] = Field(
        default=24,
        ge=1,
        le=168,
        description="Duration to check for promotion readiness"
    )


class CapabilityPromotionCheckResponse(BaseAPIModel):
    """Response model for promotion readiness check."""
    ready: bool = Field(..., description="Whether capability is ready for promotion")
    capability_id: str = Field(..., description="Capability ID")
    current_success_rate: Optional[float] = Field(None, description="Current success rate")
    sample_count: Optional[int] = Field(None, description="Number of samples analyzed")
    time_in_quarantine: Optional[int] = Field(None, description="Hours in quarantine")
    blocking_issues: Optional[List[str]] = Field(None, description="Issues preventing promotion")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations for improvement")
    next_check_at: Optional[datetime] = Field(None, description="Next automated check time")


class CapabilityStatsRequest(BaseAPIModel):
    """Request model for capability statistics."""
    capability_ids: Optional[List[str]] = Field(
        None,
        max_items=50,
        description="Specific capabilities to get stats for"
    )
    time_range_hours: Optional[int] = Field(
        default=24,
        ge=1,
        le=8760,
        description="Time range for statistics"
    )
    include_quarantined: bool = Field(
        default=True,
        description="Include quarantined capabilities in stats"
    )
    group_by: Optional[str] = Field(
        default="capability",
        pattern=r"^(capability|tenant|category|status)$",
        description="Grouping for statistics"
    )


class CapabilityStatsResponse(BaseAPIModel):
    """Response model for capability statistics."""
    stats: Dict[str, Any] = Field(..., description="Capability statistics")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    time_range: Dict[str, datetime] = Field(..., description="Time range for stats")
    generated_at: datetime = Field(default_factory=datetime.utcnow)