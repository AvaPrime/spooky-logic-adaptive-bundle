"""Pydantic models for capabilities API endpoints.

This module defines the Pydantic models used for request and response validation
in the capabilities API endpoints. These models ensure that the data flowing
in and out of the API conforms to a specific schema.
"""

from pydantic import Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, CapabilityModel, TimestampedModel


class VerificationStatus(str, Enum):
    """Enumeration of possible verification statuses for a capability.

    Attributes:
        PENDING: The verification is pending.
        VERIFIED: The capability has been successfully verified.
        FAILED: The verification has failed.
        EXPIRED: The verification has expired.
    """
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class QuarantineReason(str, Enum):
    """Enumeration of standard reasons for quarantining a capability.

    Attributes:
        SECURITY_VULNERABILITY: The capability has a security vulnerability.
        PERFORMANCE_DEGRADATION: The capability causes performance degradation.
        COMPLIANCE_VIOLATION: The capability violates a compliance policy.
        SUSPICIOUS_BEHAVIOR: The capability exhibits suspicious behavior.
        FAILED_VERIFICATION: The capability failed the verification process.
        USER_REPORT: The capability was reported by a user.
        AUTOMATED_DETECTION: The capability was flagged by an automated system.
    """
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    FAILED_VERIFICATION = "failed_verification"
    USER_REPORT = "user_report"
    AUTOMATED_DETECTION = "automated_detection"


class CapabilityVerificationRequest(BaseAPIModel):
    """Request model for verifying a capability.

    Attributes:
        bundle: The capability bundle to verify.
        pubkeys: The public keys for signature verification.
        verification_level: The strictness level of the verification.
        skip_checks: A list of verification checks to skip.
        additional_metadata: Additional metadata for the verification process.
    """
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
        """Validate the capability bundle.

        Args:
            v: The capability bundle.

        Returns:
            The validated capability bundle.

        Raises:
            ValueError: If the bundle is empty, missing required fields, or too large.
        """
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
        """Validate the public keys.

        Args:
            v: The public keys.

        Returns:
            The validated public keys.

        Raises:
            ValueError: If any of the public keys are invalid.
        """
        for key_id, pubkey in v.items():
            if not isinstance(pubkey, str) or len(pubkey.strip()) == 0:
                raise ValueError(f'Invalid public key for {key_id}')
            # Basic hex validation for public keys
            if not all(c in '0123456789abcdefABCDEF' for c in pubkey.replace(' ', '')):
                raise ValueError(f'Public key for {key_id} must be hexadecimal')
        return v
    
    @validator('skip_checks')
    def validate_skip_checks(cls, v):
        """Validate the checks to skip.

        Args:
            v: The list of checks to skip.

        Returns:
            The validated list of checks to skip.

        Raises:
            ValueError: If any of the checks to skip are invalid.
        """
        valid_checks = ['signature', 'sbom', 'provenance', 'vulnerability', 'license']
        for check in v:
            if check not in valid_checks:
                raise ValueError(f'Invalid check to skip: {check}. Valid options: {valid_checks}')
        return v


class CapabilityVerificationResponse(BaseAPIModel):
    """Response model for capability verification.

    Attributes:
        ok: Overall verification success.
        sig_ok: Signature verification result.
        sbom_ok: SBOM verification result.
        prov_ok: Provenance verification result.
        verification_id: Verification session ID.
        details: Detailed verification results.
        warnings: Verification warnings.
        timestamp: The timestamp of the verification.
    """
    ok: bool = Field(..., description="Overall verification success")
    sig_ok: bool = Field(..., description="Signature verification result")
    sbom_ok: bool = Field(..., description="SBOM verification result")
    prov_ok: bool = Field(..., description="Provenance verification result")
    verification_id: Optional[str] = Field(None, description="Verification session ID")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed verification results")
    warnings: Optional[List[str]] = Field(None, description="Verification warnings")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CapabilityQuarantineRequest(CapabilityModel, TimestampedModel):
    """Request model for quarantining a capability.

    Attributes:
        reason: The detailed reason for the quarantine.
        reason_category: The categorized reason for the quarantine.
        canary_rate: The canary traffic rate for the quarantined capability.
        severity: The severity level of the quarantine.
        auto_promote_threshold: The success rate threshold for auto-promotion.
        max_quarantine_duration: The maximum duration of the quarantine in hours.
        reporter: The entity reporting the issue.
        evidence: Supporting evidence for the quarantine.
    """
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
        """Validate the reason for quarantine.

        Args:
            v: The reason for quarantine.

        Returns:
            The validated reason for quarantine.

        Raises:
            ValueError: If the reason is less than 10 characters.
        """
        v = ' '.join(v.split())  # Clean whitespace
        if len(v) < 10:
            raise ValueError('Reason must be at least 10 characters after cleaning whitespace')
        return v
    
    @validator('evidence')
    def validate_evidence(cls, v):
        """Validate the evidence for quarantine.

        Args:
            v: The evidence for quarantine.

        Returns:
            The validated evidence for quarantine.

        Raises:
            ValueError: If the evidence is too large.
        """
        if v and len(str(v)) > 10000:  # 10KB limit
            raise ValueError('Evidence too large (max 10KB when serialized)')
        return v


class CapabilityQuarantineResponse(BaseAPIModel):
    """Response model for capability quarantine.

    Attributes:
        quarantined: The ID of the quarantined capability.
        canary_rate: The applied canary rate.
        quarantine_id: The ID of the quarantine session.
        estimated_promotion_date: The estimated date of promotion.
        monitoring_endpoints: The monitoring endpoints for the quarantined capability.
    """
    quarantined: str = Field(..., description="Quarantined capability ID")
    canary_rate: float = Field(..., description="Applied canary rate")
    quarantine_id: Optional[str] = Field(None, description="Quarantine session ID")
    estimated_promotion_date: Optional[datetime] = Field(None, description="Estimated promotion date")
    monitoring_endpoints: Optional[List[str]] = Field(None, description="Monitoring endpoints")


class QuarantineListResponse(BaseAPIModel):
    """Response model for listing quarantined capabilities.

    Attributes:
        quarantined_capabilities: A list of quarantined capabilities.
        total_count: The total number of quarantined capabilities.
        active_count: The number of active quarantines.
        pending_promotion: The number of capabilities pending promotion.
    """
    quarantined_capabilities: List[Dict[str, Any]] = Field(
        ...,
        description="List of quarantined capabilities"
    )
    total_count: int = Field(..., ge=0, description="Total quarantined capabilities")
    active_count: int = Field(..., ge=0, description="Active quarantines")
    pending_promotion: int = Field(..., ge=0, description="Capabilities pending promotion")


class CapabilityPromotionCheckRequest(CapabilityModel):
    """Request model for checking the promotion readiness of a capability.

    Attributes:
        min_samples: The minimum number of samples required for promotion.
        min_success_rate: The minimum success rate required for promotion.
        check_duration_hours: The duration to check for promotion readiness.
    """
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
    """Response model for the promotion readiness check of a capability.

    Attributes:
        ready: Whether the capability is ready for promotion.
        capability_id: The ID of the capability.
        current_success_rate: The current success rate of the capability.
        sample_count: The number of samples analyzed.
        time_in_quarantine: The number of hours the capability has been in quarantine.
        blocking_issues: A list of issues preventing promotion.
        recommendations: A list of recommendations for improvement.
        next_check_at: The next automated check time.
    """
    ready: bool = Field(..., description="Whether capability is ready for promotion")
    capability_id: str = Field(..., description="Capability ID")
    current_success_rate: Optional[float] = Field(None, description="Current success rate")
    sample_count: Optional[int] = Field(None, description="Number of samples analyzed")
    time_in_quarantine: Optional[int] = Field(None, description="Hours in quarantine")
    blocking_issues: Optional[List[str]] = Field(None, description="Issues preventing promotion")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations for improvement")
    next_check_at: Optional[datetime] = Field(None, description="Next automated check time")


class CapabilityStatsRequest(BaseAPIModel):
    """Request model for capability statistics.

    Attributes:
        capability_ids: A list of specific capability IDs to get statistics for.
        time_range_hours: The time range for the statistics in hours.
        include_quarantined: Whether to include quarantined capabilities in the statistics.
        group_by: The field to group the statistics by.
    """
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
    """Response model for capability statistics.

    Attributes:
        stats: The capability statistics.
        summary: The summary statistics.
        time_range: The time range for the statistics.
        generated_at: The timestamp when the statistics were generated.
    """
    stats: Dict[str, Any] = Field(..., description="Capability statistics")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    time_range: Dict[str, datetime] = Field(..., description="Time range for stats")
    generated_at: datetime = Field(default_factory=datetime.utcnow)