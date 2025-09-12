"""Pydantic models for marketplace API endpoints.

This module defines the Pydantic models used for request and response validation
in the marketplace API endpoints. These models ensure that the data flowing
in and out of the API conforms to a specific schema.
"""

from pydantic import Field, validator, HttpUrl
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, TimestampedModel
import re


class InstallationStatus(str, Enum):
    """Enumeration of possible installation statuses.

    Attributes:
        PENDING: The installation is pending.
        DOWNLOADING: The package is being downloaded.
        VERIFYING: The package is being verified.
        INSTALLING: The package is being installed.
        COMPLETED: The installation is complete.
        FAILED: The installation has failed.
        ROLLED_BACK: The installation has been rolled back.
    """
    PENDING = "pending"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class CapabilityCategory(str, Enum):
    """Enumeration of capability categories.

    Attributes:
        AI_MODEL: An AI model.
        DATA_PROCESSOR: A data processor.
        SECURITY_TOOL: A security tool.
        MONITORING: A monitoring tool.
        INTEGRATION: An integration with an external service.
        WORKFLOW: A workflow or playbook.
        UTILITY: A utility or helper tool.
    """
    AI_MODEL = "ai_model"
    DATA_PROCESSOR = "data_processor"
    SECURITY_TOOL = "security_tool"
    MONITORING = "monitoring"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"
    UTILITY = "utility"


class MarketplaceManifest(BaseAPIModel):
    """A manifest for a capability in the marketplace.

    This model defines the structure of a capability manifest, which contains
    all the necessary information to describe, install, and use a capability.

    Attributes:
        id: The unique identifier of the capability.
        name: The human-readable name of the capability.
        version: The semantic version of the capability.
        description: A detailed description of the capability.
        category: The category of the capability.
        author: The author or publisher of the capability.
        license: The license identifier of the capability.
        playbook_url: The URL to download the capability playbook.
        sha256: The SHA256 hash of the playbook file.
        signature: The digital signature of the manifest.
        homepage: The URL of the capability's homepage.
        documentation: The URL of the capability's documentation.
        repository: The URL of the capability's source code repository.
        tags: A list of tags for discovery.
        requirements: The system requirements and dependencies.
        configuration: The default configuration parameters.
        pricing: The pricing information.
        support_contact: The support contact information.
    """
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
        """Validate the description.

        Args:
            v: The description string.

        Returns:
            The validated description string.

        Raises:
            ValueError: If the description is too short.
        """
        # Clean whitespace
        v = ' '.join(v.split())
        if len(v) < 20:
            raise ValueError('Description must be at least 20 characters after cleaning whitespace')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate the tags.

        Args:
            v: The list of tags.

        Returns:
            The validated list of tags.
        """
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
        """Validate the requirements.

        Args:
            v: The requirements dictionary.

        Returns:
            The validated requirements dictionary.

        Raises:
            ValueError: If the requirements are too large.
        """
        if v and len(str(v)) > 10000:  # 10KB limit
            raise ValueError('Requirements too large (max 10KB when serialized)')
        return v
    
    @validator('configuration')
    def validate_configuration(cls, v):
        """Validate the configuration.

        Args:
            v: The configuration dictionary.

        Returns:
            The validated configuration dictionary.

        Raises:
            ValueError: If the configuration is too large.
        """
        if v and len(str(v)) > 20000:  # 20KB limit
            raise ValueError('Configuration too large (max 20KB when serialized)')
        return v


class MarketplaceInstallRequest(TimestampedModel):
    """Request model for installing a capability from the marketplace.

    Attributes:
        manifest: The manifest of the capability to install.
        public_key_hex: The public key for signature verification.
        dest_dir: The destination directory for the installation.
        installation_options: Installation-specific options.
        force_reinstall: Whether to force reinstallation if the capability already exists.
        verify_dependencies: Whether to verify all dependencies before installation.
        sandbox_mode: Whether to install in sandbox mode for testing.
    """
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
        """Validate the public key.

        Args:
            v: The public key in hex format.

        Returns:
            The validated public key.

        Raises:
            ValueError: If the public key is invalid.
        """
        # Remove whitespace and validate hex format
        v = v.replace(' ', '').replace('\n', '')
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('Public key must be in hexadecimal format')
        if len(v) < 64:
            raise ValueError('Public key too short (minimum 64 hex characters)')
        return v
    
    @validator('dest_dir')
    def validate_dest_dir(cls, v):
        """Validate the destination directory.

        Args:
            v: The destination directory path.

        Returns:
            The validated destination directory path.

        Raises:
            ValueError: If the destination directory path is invalid.
        """
        if v:
            # Basic path validation
            if '..' in v or v.startswith('/'):
                raise ValueError('Invalid destination directory path')
            # Normalize path separators
            v = v.replace('\\', '/').strip('/')
        return v
    
    @validator('installation_options')
    def validate_installation_options(cls, v):
        """Validate the installation options.

        Args:
            v: The installation options dictionary.

        Returns:
            The validated installation options dictionary.

        Raises:
            ValueError: If the installation options are too large.
        """
        if v and len(str(v)) > 5000:  # 5KB limit
            raise ValueError('Installation options too large (max 5KB when serialized)')
        return v


class MarketplaceInstallResponse(BaseAPIModel):
    """Response model for installing a capability from the marketplace.

    Attributes:
        installed: The path to the installed file.
        installation_id: The ID for tracking the installation.
        capability_id: The ID of the installed capability.
        version: The version of the installed capability.
        status: The status of the installation.
        verification_results: The results of the verification checks.
        installation_time: The timestamp of the installation.
        file_size_bytes: The size of the installed file in bytes.
        checksum_verified: Whether the checksum was verified.
    """
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
    """Request model for searching the marketplace.

    Attributes:
        query: The search query string.
        category: Filter by category.
        tags: Filter by tags.
        author: Filter by author.
        license: Filter by license.
        min_version: The minimum version requirement.
        verified_only: Whether to only return verified capabilities.
        page: The page number for pagination.
        size: The page size for pagination.
        sort_by: The field to sort the results by.
        sort_order: The sort order (asc or desc).
    """
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
        """Validate the search tags.

        Args:
            v: The list of search tags.

        Returns:
            The validated list of search tags.
        """
        if v:
            return [tag.strip().lower() for tag in v if tag.strip()]
        return []


class MarketplaceSearchResponse(BaseAPIModel):
    """Response model for searching the marketplace.

    Attributes:
        capabilities: A list of matching capabilities.
        total: The total number of matches.
        page: The current page number.
        size: The page size.
        has_next: Whether there are more pages.
        facets: Search facets for filtering.
        search_time_ms: The search execution time in milliseconds.
    """
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
    """Extended capability details for the marketplace.

    Attributes:
        downloads: The number of downloads.
        rating: The average rating.
        review_count: The number of reviews.
        created_at: The timestamp when the capability was created.
        updated_at: The timestamp when the capability was last updated.
        verified: Whether the capability is verified.
        featured: Whether the capability is featured.
        compatibility: The platform compatibility information.
        changelog: The version changelog.
        screenshots: A list of screenshot URLs.
    """
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
    """Request model for uninstalling a capability.

    Attributes:
        capability_id: The ID of the capability to uninstall.
        version: The specific version to uninstall (latest if not specified).
        remove_data: Whether to remove associated data.
        force: Whether to force uninstallation even if the capability is in use.
    """
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
    """Response model for uninstalling a capability.

    Attributes:
        uninstalled: The ID of the uninstalled capability.
        version: The version of the uninstalled capability.
        files_removed: A list of removed files.
        data_removed: Whether data was removed.
        uninstall_time: The timestamp of the uninstallation.
    """
    uninstalled: str = Field(..., description="Uninstalled capability ID")
    version: str = Field(..., description="Uninstalled version")
    files_removed: List[str] = Field(
        default_factory=list,
        description="List of removed files"
    )
    data_removed: bool = Field(default=False, description="Whether data was removed")
    uninstall_time: datetime = Field(default_factory=datetime.utcnow)


class MarketplaceListResponse(BaseAPIModel):
    """Response model for listing packages in the marketplace.

    Attributes:
        packages: A list of available packages.
        total_count: The total number of packages.
        categories: A list of available categories.
        packages_by_category: The packages grouped by category.
    """
    packages: List[Dict[str, Any]] = Field(..., description="List of available packages")
    total_count: int = Field(..., ge=0, description="Total number of packages")
    categories: List[str] = Field(default_factory=list, description="Available categories")
    packages_by_category: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Packages grouped by category"
    )


class MarketplaceStatusRequest(BaseAPIModel):
    """Request model for checking the status of a marketplace installation.

    Attributes:
        installation_id: The ID of the installation to check.
    """
    installation_id: str = Field(..., description="Installation ID to check")


class MarketplaceStatusResponse(BaseAPIModel):
    """Response model for the status of a marketplace installation.

    Attributes:
        installation_id: The ID of the installation.
        status: The current installation status.
        progress: The installation progress percentage.
        message: A status message.
        error: An error message if the installation failed.
        started_at: The timestamp when the installation started.
        completed_at: The timestamp when the installation completed.
    """
    installation_id: str = Field(..., description="Installation ID")
    status: InstallationStatus = Field(..., description="Current installation status")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="Installation progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Installation start time")
    completed_at: Optional[datetime] = Field(None, description="Installation completion time")