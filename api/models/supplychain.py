"""Pydantic models for supply chain API endpoints."""

from pydantic import Field, validator, HttpUrl
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, TimestampedModel
import re


class RiskLevel(str, Enum):
    """Supply chain risk levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ComponentType(str, Enum):
    """Supply chain component types."""
    LIBRARY = "library"
    FRAMEWORK = "framework"
    TOOL = "tool"
    SERVICE = "service"
    CONTAINER = "container"
    BINARY = "binary"
    CONFIGURATION = "configuration"
    DATA = "data"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class LicenseRisk(str, Enum):
    """License risk categories."""
    COPYLEFT_STRONG = "copyleft_strong"  # GPL, AGPL
    COPYLEFT_WEAK = "copyleft_weak"      # LGPL, MPL
    PERMISSIVE = "permissive"            # MIT, Apache, BSD
    PROPRIETARY = "proprietary"          # Commercial licenses
    UNKNOWN = "unknown"                  # Unidentified license
    DUAL = "dual"                        # Dual licensing


class SupplyChainComponent(BaseAPIModel):
    """Supply chain component information."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Component name"
    )
    version: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Component version"
    )
    component_type: ComponentType = Field(
        ...,
        description="Type of component"
    )
    source: Optional[str] = Field(
        None,
        max_length=500,
        description="Source repository or registry"
    )
    homepage: Optional[HttpUrl] = Field(
        None,
        description="Component homepage URL"
    )
    license: Optional[str] = Field(
        None,
        max_length=100,
        description="Component license identifier"
    )
    license_risk: Optional[LicenseRisk] = Field(
        None,
        description="License risk category"
    )
    checksum: Optional[str] = Field(
        None,
        description="Component checksum (SHA256, etc.)"
    )
    size_bytes: Optional[int] = Field(
        None,
        ge=0,
        description="Component size in bytes"
    )
    dependencies: Optional[List[str]] = Field(
        default_factory=list,
        max_items=1000,
        description="List of direct dependencies"
    )
    
    @validator('checksum')
    def validate_checksum(cls, v):
        if v:
            # Support common hash formats
            if re.match(r'^[a-fA-F0-9]{32}$', v):  # MD5
                return v
            elif re.match(r'^[a-fA-F0-9]{40}$', v):  # SHA1
                return v
            elif re.match(r'^[a-fA-F0-9]{64}$', v):  # SHA256
                return v
            elif re.match(r'^[a-fA-F0-9]{128}$', v):  # SHA512
                return v
            else:
                raise ValueError('Invalid checksum format (expected MD5, SHA1, SHA256, or SHA512)')
        return v


class Vulnerability(BaseAPIModel):
    """Vulnerability information."""
    id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Vulnerability identifier (CVE, etc.)"
    )
    severity: VulnerabilitySeverity = Field(
        ...,
        description="Vulnerability severity"
    )
    score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="CVSS or similar vulnerability score"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Vulnerability description"
    )
    published_date: Optional[datetime] = Field(
        None,
        description="Vulnerability publication date"
    )
    fixed_version: Optional[str] = Field(
        None,
        max_length=100,
        description="Version that fixes this vulnerability"
    )
    references: Optional[List[HttpUrl]] = Field(
        default_factory=list,
        max_items=20,
        description="Reference URLs for more information"
    )
    exploitable: Optional[bool] = Field(
        None,
        description="Whether vulnerability is actively exploitable"
    )
    
    @validator('id')
    def validate_vulnerability_id(cls, v):
        # Common vulnerability ID formats
        if re.match(r'^CVE-\d{4}-\d{4,}$', v.upper()):
            return v.upper()
        elif re.match(r'^GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}$', v.lower()):
            return v.lower()
        elif re.match(r'^[A-Z]+-\d{4}-\d+$', v.upper()):
            return v.upper()
        return v  # Allow other formats


class SupplyChainScoreRequest(TimestampedModel):
    """Request model for supply chain scoring."""
    components: List[SupplyChainComponent] = Field(
        ...,
        min_items=1,
        max_items=10000,
        description="List of components to analyze"
    )
    project_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Project name for context"
    )
    project_version: Optional[str] = Field(
        None,
        max_length=100,
        description="Project version"
    )
    environment: Optional[str] = Field(
        None,
        max_length=50,
        description="Target environment (prod, staging, dev)"
    )
    include_transitive: bool = Field(
        default=True,
        description="Include transitive dependency analysis"
    )
    vulnerability_scan: bool = Field(
        default=True,
        description="Perform vulnerability scanning"
    )
    license_analysis: bool = Field(
        default=True,
        description="Perform license risk analysis"
    )
    malware_scan: bool = Field(
        default=True,
        description="Perform malware scanning"
    )
    supply_chain_attacks: bool = Field(
        default=True,
        description="Check for supply chain attack indicators"
    )
    policy_checks: Optional[List[str]] = Field(
        default_factory=list,
        max_items=50,
        description="Custom policy checks to perform"
    )
    baseline_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Baseline score for comparison"
    )
    
    @validator('components')
    def validate_components(cls, v):
        if not v:
            raise ValueError('At least one component must be provided')
        
        # Check for duplicate components
        seen = set()
        for comp in v:
            key = (comp.name, comp.version, comp.component_type)
            if key in seen:
                raise ValueError(f'Duplicate component: {comp.name}@{comp.version}')
            seen.add(key)
        
        return v
    
    @validator('policy_checks')
    def validate_policy_checks(cls, v):
        if v:
            valid_policies = [
                'no_critical_vulns', 'no_high_vulns', 'license_whitelist',
                'license_blacklist', 'no_copyleft', 'no_proprietary',
                'max_age_days', 'min_maintainers', 'verified_publishers',
                'no_deprecated', 'security_audit', 'code_signing'
            ]
            for policy in v:
                if policy not in valid_policies:
                    raise ValueError(f'Invalid policy check: {policy}. Valid options: {valid_policies}')
        return v


class ComponentScore(BaseAPIModel):
    """Individual component score details."""
    component: SupplyChainComponent = Field(..., description="Component information")
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall component score (0-100)"
    )
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    
    # Detailed scoring
    vulnerability_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Vulnerability score"
    )
    license_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="License compliance score"
    )
    maintenance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Maintenance and activity score"
    )
    popularity_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Popularity and adoption score"
    )
    
    # Findings
    vulnerabilities: List[Vulnerability] = Field(
        default_factory=list,
        description="Identified vulnerabilities"
    )
    license_issues: List[str] = Field(
        default_factory=list,
        description="License-related issues"
    )
    policy_violations: List[str] = Field(
        default_factory=list,
        description="Policy violations"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="General warnings"
    )
    
    # Metadata
    last_updated: Optional[datetime] = Field(
        None,
        description="When component was last updated"
    )
    maintainers: Optional[int] = Field(
        None,
        ge=0,
        description="Number of active maintainers"
    )
    downloads: Optional[int] = Field(
        None,
        ge=0,
        description="Download count (if available)"
    )
    age_days: Optional[int] = Field(
        None,
        ge=0,
        description="Age of component in days"
    )


class SupplyChainScoreResponse(BaseAPIModel):
    """Response model for supply chain scoring."""
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall supply chain score (0-100)"
    )
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    
    # Summary statistics
    total_components: int = Field(..., ge=0, description="Total components analyzed")
    critical_issues: int = Field(..., ge=0, description="Number of critical issues")
    high_issues: int = Field(..., ge=0, description="Number of high-severity issues")
    medium_issues: int = Field(..., ge=0, description="Number of medium-severity issues")
    low_issues: int = Field(..., ge=0, description="Number of low-severity issues")
    
    # Detailed scores
    vulnerability_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Aggregate vulnerability score"
    )
    license_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Aggregate license compliance score"
    )
    maintenance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Aggregate maintenance score"
    )
    
    # Component details
    component_scores: List[ComponentScore] = Field(
        ...,
        description="Individual component scores"
    )
    
    # Top issues
    top_vulnerabilities: List[Vulnerability] = Field(
        default_factory=list,
        max_items=20,
        description="Most critical vulnerabilities found"
    )
    policy_violations: List[str] = Field(
        default_factory=list,
        description="Policy violations found"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improvement"
    )
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When analysis was performed"
    )
    analysis_duration_ms: Optional[float] = Field(
        None,
        description="Analysis execution time"
    )
    data_sources: List[str] = Field(
        default_factory=list,
        description="Data sources used for analysis"
    )
    
    # Comparison with baseline
    baseline_comparison: Optional[Dict[str, float]] = Field(
        None,
        description="Comparison with baseline score"
    )
    
    # Risk distribution
    risk_distribution: Dict[RiskLevel, int] = Field(
        default_factory=dict,
        description="Distribution of components by risk level"
    )
    
    # License distribution
    license_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of licenses found"
    )


class SupplyChainMonitorRequest(BaseAPIModel):
    """Request model for continuous supply chain monitoring."""
    project_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Project identifier for monitoring"
    )
    components: List[SupplyChainComponent] = Field(
        ...,
        min_items=1,
        description="Components to monitor"
    )
    monitoring_frequency: str = Field(
        default="daily",
        pattern=r"^(hourly|daily|weekly|monthly)$",
        description="Monitoring frequency"
    )
    alert_thresholds: Optional[Dict[str, float]] = Field(
        None,
        description="Custom alert thresholds"
    )
    notification_channels: Optional[List[str]] = Field(
        default_factory=list,
        description="Notification channels for alerts"
    )
    auto_update_minor: bool = Field(
        default=False,
        description="Auto-update minor versions"
    )
    auto_update_patch: bool = Field(
        default=True,
        description="Auto-update patch versions"
    )


class SupplyChainMonitorResponse(BaseAPIModel):
    """Response model for supply chain monitoring setup."""
    monitor_id: str = Field(..., description="Monitoring session ID")
    project_id: str = Field(..., description="Project being monitored")
    components_count: int = Field(..., ge=0, description="Number of components monitored")
    monitoring_frequency: str = Field(..., description="Monitoring frequency")
    next_scan_at: datetime = Field(..., description="Next scheduled scan")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active", description="Monitoring status")


class SupplyChainReportRequest(BaseAPIModel):
    """Request model for supply chain reports."""
    project_id: Optional[str] = Field(
        None,
        description="Filter by project ID"
    )
    date_from: Optional[datetime] = Field(
        None,
        description="Report start date"
    )
    date_to: Optional[datetime] = Field(
        None,
        description="Report end date"
    )
    report_type: str = Field(
        default="summary",
        pattern=r"^(summary|detailed|compliance|trends|vulnerabilities)$",
        description="Type of report to generate"
    )
    format: str = Field(
        default="json",
        pattern=r"^(json|pdf|csv|html)$",
        description="Report output format"
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include recommendations in report"
    )


class SupplyChainReportResponse(BaseAPIModel):
    """Response model for supply chain reports."""
    report_id: str = Field(..., description="Generated report ID")
    report_type: str = Field(..., description="Report type")
    format: str = Field(..., description="Report format")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    download_url: Optional[HttpUrl] = Field(None, description="Download URL for report")
    expires_at: Optional[datetime] = Field(None, description="When download expires")
    size_bytes: Optional[int] = Field(None, description="Report size in bytes")
    summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Report summary statistics"
    )


class SupplyChainValidateRequest(BaseAPIModel):
    """Request model for supply chain validation."""
    project_id: str = Field(..., description="Project ID to validate")
    component_path: Optional[str] = Field(
        None,
        description="Specific component path to validate"
    )
    validation_type: str = Field(
        default="full",
        pattern=r"^(full|security|license|compliance|dependencies)$",
        description="Type of validation to perform"
    )
    include_transitive: bool = Field(
        default=True,
        description="Include transitive dependencies"
    )
    policy_profile: Optional[str] = Field(
        None,
        description="Policy profile to use for validation"
    )
    fail_on_critical: bool = Field(
        default=True,
        description="Fail validation on critical issues"
    )


class SupplyChainValidateResponse(BaseAPIModel):
    """Response model for supply chain validation."""
    validation_id: str = Field(..., description="Validation session ID")
    project_id: str = Field(..., description="Validated project ID")
    validation_type: str = Field(..., description="Type of validation performed")
    status: str = Field(..., description="Validation status")
    passed: bool = Field(..., description="Whether validation passed")
    issues_found: int = Field(..., ge=0, description="Number of issues found")
    critical_issues: int = Field(..., ge=0, description="Number of critical issues")
    high_issues: int = Field(..., ge=0, description="Number of high severity issues")
    medium_issues: int = Field(..., ge=0, description="Number of medium severity issues")
    low_issues: int = Field(..., ge=0, description="Number of low severity issues")
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validation_duration: Optional[float] = Field(
        None,
        description="Validation duration in seconds"
    )
    report_url: Optional[HttpUrl] = Field(
        None,
        description="URL to detailed validation report"
    )
    recommendations: Optional[List[str]] = Field(
        default_factory=list,
        description="Validation recommendations"
    )


class SupplyChainAuditRequest(BaseAPIModel):
    """Request model for supply chain audit."""
    project_id: str = Field(..., description="Project ID to audit")
    audit_scope: str = Field(
        default="full",
        pattern=r"^(full|security|compliance|licensing|dependencies)$",
        description="Scope of the audit"
    )
    include_historical: bool = Field(
        default=False,
        description="Include historical audit data"
    )
    compliance_frameworks: Optional[List[str]] = Field(
        default_factory=list,
        description="Compliance frameworks to check against"
    )
    audit_depth: str = Field(
        default="standard",
        pattern=r"^(shallow|standard|deep)$",
        description="Depth of audit analysis"
    )


class SupplyChainAuditResponse(BaseAPIModel):
    """Response model for supply chain audit."""
    audit_id: str = Field(..., description="Audit session ID")
    project_id: str = Field(..., description="Audited project ID")
    audit_scope: str = Field(..., description="Scope of audit performed")
    status: str = Field(..., description="Audit status")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Overall compliance score")
    security_score: float = Field(..., ge=0.0, le=100.0, description="Security score")
    license_compliance: float = Field(..., ge=0.0, le=100.0, description="License compliance score")
    findings_count: int = Field(..., ge=0, description="Total number of findings")
    critical_findings: int = Field(..., ge=0, description="Critical findings count")
    audited_at: datetime = Field(default_factory=datetime.utcnow)
    audit_duration: Optional[float] = Field(
        None,
        description="Audit duration in seconds"
    )
    report_url: Optional[HttpUrl] = Field(
        None,
        description="URL to detailed audit report"
    )
    next_audit_recommended: Optional[datetime] = Field(
        None,
        description="Recommended next audit date"
    )