"""Pydantic models for marketplace API endpoints."""

from pydantic import Field, validator, HttpUrl
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, TimestampedModel
import re


class InstallationStatus(str, Enum):
    """Installation status values."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class CapabilityCategory(str, Enum):
    """Capability categories."""
    AI_MODEL = "ai_model"
    DATA_PROCESSOR = "data_processor"
    SECURITY_TOOL = "security_tool"
    MONITORING = "monitoring"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"
    UTILITY = "utility"


class MarketplaceManifest(BaseAPIModel):
    """Marketplace capability manifest model."""
    id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9._-]+$",
        description="Unique capability identifier"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable capability name"
    )
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$",
        description="Semantic version (e.g., 1.0.0 or 1.0.0-beta.1)"
    )
    description: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="Detailed capability description"
    )
    category: CapabilityCategory = Field(
        ...,
        description="Capability category"
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Capability author/publisher"
    )
    license: str = Field(
        ...,
        max_length=50,
        description="License identifier (e.g., MIT, Apache-2.0)"
    )
    playbook_url: HttpUrl = Field(
        ...,
        description="URL to download the capability playbook"
    )
    sha256: str = Field(
        ...,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="SHA256 hash of the playbook file"
    )
    signature: str = Field(
        ...,
        description="Digital signature of the manifest"
    )
    
    # Optional fields
    homepage: Optional[HttpUrl] = Field(None, description="Capability homepage URL")
    documentation: Optional[HttpUrl] = Field(None, description="Documentation URL")
    repository: Optional[HttpUrl] = Field(None, description="Source code repository URL")
    tags: Optional[List[str]] = Field(
        default_factory=list,
        max_items=20,
        description="Capability tags for discovery"
    )
    requirements: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="System requirements and dependencies"
    )
    configuration: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Default configuration parameters"
    )
    pricing: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Pricing information"
    )
    support_contact: Optional[str] = Field(
        None,
        max_length=200,
        description="Support contact information"
    )
    
    @validator('description')
    def validate_description(cls, v):
        # Clean whitespace
        v = ' '.join(v.split())
        if len(v) < 20:
            raise ValueError('Description must be at least 20 characters after cleaning whitespace')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            cleaned_tags = []
            for tag in v:
                if isinstance(tag, str) and tag.strip():
                    # Validate tag format
                    clean_tag = tag.strip().lower()
                    if re.match(r'^[a-z0-9-_]+$', clean_tag):
                        cleaned_tags.append(clean_tag)
            return cleaned_tags[:20]  # Limit to 20 tags
        return []
    
    @validator('requirements')
    def validate_requirements(cls, v):
        if v and len(str(v)) > 10000:  # 10KB limit
            raise ValueError('Requirements too large (max 10KB when serialized)')
        return v
    
    @validator('configuration')
    def validate_configuration(cls, v):
        if v and len(str(v)) > 20000:  # 20KB limit
            raise ValueError('Configuration too large (max 20KB when serialized)')
        return v


class MarketplaceInstallRequest(TimestampedModel):
    """Request model for marketplace installation."""
    manifest: MarketplaceManifest = Field(
        ...,
        description="Capability manifest to install"
    )
    public_key_hex: str = Field(
        ...,
        min_length=64,
        description="Public key for signature verification (hex format)"
    )
    dest_dir: Optional[str] = Field(
        default="playbooks/market",
        max_length=500,
        description="Destination directory for installation"
    )
    installation_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Installation-specific options"
    )
    force_reinstall: bool = Field(
        default=False,
        description="Force reinstallation if already exists"
    )
    verify_dependencies: bool = Field(
        default=True,
        description="Verify all dependencies before installation"
    )
    sandbox_mode: bool = Field(
        default=False,
        description="Install in sandbox mode for testing"
    )
    
    @validator('public_key_hex')
    def validate_public_key(cls, v):
        # Remove whitespace and validate hex format
        v = v.replace(' ', '').replace('\n', '')
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('Public key must be in hexadecimal format')
        if len(v) < 64:
            raise ValueError('Public key too short (minimum 64 hex characters)')
        return v
    
    @validator('dest_dir')
    def validate_dest_dir(cls, v):
        if v:
            # Basic path validation
            if '..' in v or v.startswith('/'):
                raise ValueError('Invalid destination directory path')
            # Normalize path separators
            v = v.replace('\\', '/').strip('/')
        return v
    
    @validator('installation_options')
    def validate_installation_options(cls, v):
        if v and len(str(v)) > 5000:  # 5KB limit
            raise ValueError('Installation options too large (max 5KB when serialized)')
        return v


class MarketplaceInstallResponse(BaseAPIModel):
    """Response model for marketplace installation."""
    installed: str = Field(..., description="Installed file path")
    installation_id: Optional[str] = Field(None, description="Installation tracking ID")
    capability_id: str = Field(..., description="Installed capability ID")
    version: str = Field(..., description="Installed version")
    status: InstallationStatus = Field(default=InstallationStatus.COMPLETED)
    verification_results: Optional[Dict[str, bool]] = Field(
        None,
        description="Verification check results"
    )
    installation_time: datetime = Field(default_factory=datetime.utcnow)
    file_size_bytes: Optional[int] = Field(None, description="Size of installed file")
    checksum_verified: bool = Field(default=True, description="Whether checksum was verified")


class MarketplaceSearchRequest(BaseAPIModel):
    """Request model for marketplace search."""
    query: Optional[str] = Field(
        None,
        max_length=200,
        description="Search query string"
    )
    category: Optional[CapabilityCategory] = Field(
        None,
        description="Filter by category"
    )
    tags: Optional[List[str]] = Field(
        None,
        max_items=10,
        description="Filter by tags"
    )
    author: Optional[str] = Field(
        None,
        max_length=100,
        description="Filter by author"
    )
    license: Optional[str] = Field(
        None,
        max_length=50,
        description="Filter by license"
    )
    min_version: Optional[str] = Field(
        None,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Minimum version requirement"
    )
    verified_only: bool = Field(
        default=True,
        description="Only return verified capabilities"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(
        default="popularity",
        pattern=r"^(name|author|version|created_at|updated_at|popularity|rating)$",
        description="Sort field"
    )
    sort_order: Optional[str] = Field(
        default="desc",
        pattern=r"^(asc|desc)$",
        description="Sort order"
    )
    
    @validator('tags')
    def validate_search_tags(cls, v):
        if v:
            return [tag.strip().lower() for tag in v if tag.strip()]
        return []


class MarketplaceSearchResponse(BaseAPIModel):
    """Response model for marketplace search."""
    capabilities: List[Dict[str, Any]] = Field(
        ...,
        description="List of matching capabilities"
    )
    total: int = Field(..., ge=0, description="Total number of matches")
    page: int = Field(..., ge=1, description="Current page")
    size: int = Field(..., ge=1, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    facets: Optional[Dict[str, Dict[str, int]]] = Field(
        None,
        description="Search facets for filtering"
    )
    search_time_ms: Optional[float] = Field(None, description="Search execution time")


class MarketplaceCapabilityDetails(MarketplaceManifest):
    """Extended capability details for marketplace."""
    downloads: int = Field(default=0, ge=0, description="Download count")
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Average rating")
    review_count: int = Field(default=0, ge=0, description="Number of reviews")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    verified: bool = Field(default=False, description="Whether capability is verified")
    featured: bool = Field(default=False, description="Whether capability is featured")
    compatibility: Optional[Dict[str, Any]] = Field(
        None,
        description="Platform compatibility information"
    )
    changelog: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Version changelog"
    )
    screenshots: Optional[List[HttpUrl]] = Field(
        None,
        max_items=10,
        description="Screenshot URLs"
    )


class MarketplaceUninstallRequest(BaseAPIModel):
    """Request model for capability uninstallation."""
    capability_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Capability ID to uninstall"
    )
    version: Optional[str] = Field(
        None,
        description="Specific version to uninstall (latest if not specified)"
    )
    remove_data: bool = Field(
        default=False,
        description="Whether to remove associated data"
    )
    force: bool = Field(
        default=False,
        description="Force uninstallation even if in use"
    )


class MarketplaceUninstallResponse(BaseAPIModel):
    """Response model for capability uninstallation."""
    uninstalled: str = Field(..., description="Uninstalled capability ID")
    version: str = Field(..., description="Uninstalled version")
    files_removed: List[str] = Field(
        default_factory=list,
        description="List of removed files"
    )
    data_removed: bool = Field(default=False, description="Whether data was removed")
    uninstall_time: datetime = Field(default_factory=datetime.utcnow)