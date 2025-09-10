"""Pydantic models for governance API endpoints."""

from pydantic import Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, TenantModel, CapabilityModel, TimestampedModel


class GovernanceAction(str, Enum):
    """Valid governance actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SUSPEND = "suspend"
    ACTIVATE = "activate"
    CONFIGURE = "configure"


class ProposalStatus(str, Enum):
    """Proposal status values."""
    DRAFT = "draft"
    ACTIVE = "active"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class ProposalRequest(TenantModel, CapabilityModel, TimestampedModel):
    """Request model for creating governance proposals."""
    action: GovernanceAction = Field(..., description="Action to be taken")
    rationale: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="Detailed rationale for the proposal"
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Proposal title"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Action-specific parameters"
    )
    priority: Optional[str] = Field(
        default="normal",
        pattern=r"^(low|normal|high|critical)$",
        description="Proposal priority"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Proposal expiration timestamp"
    )
    required_approvals: Optional[int] = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of approvals required"
    )
    
    @validator('rationale')
    def validate_rationale(cls, v):
        # Clean up whitespace
        v = ' '.join(v.split())
        if len(v) < 20:
            raise ValueError('Rationale must be at least 20 characters after cleaning whitespace')
        return v
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Expiration date must be in the future')
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v):
        if v and len(str(v)) > 5000:  # Limit parameter size
            raise ValueError('Parameters too large (max 5KB when serialized)')
        return v


class ProposalResponse(BaseAPIModel):
    """Response model for proposal creation."""
    ok: bool = Field(True)
    proposal: Dict[str, Any] = Field(..., description="Created proposal details")
    proposal_id: Optional[int] = Field(None, description="Proposal ID")


class VoteRequest(BaseAPIModel):
    """Request model for voting on proposals."""
    proposal_id: int = Field(..., ge=1, description="Proposal ID to vote on")
    voter: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9._@-]+$",
        description="Voter identifier"
    )
    approve: bool = Field(..., description="Vote approval (true) or rejection (false)")
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional vote comment"
    )
    weight: Optional[float] = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Vote weight (for weighted voting systems)"
    )
    
    @validator('comment')
    def validate_comment(cls, v):
        if v:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class VoteResponse(BaseAPIModel):
    """Response model for voting."""
    ok: bool = Field(True)
    proposal: Dict[str, Any] = Field(..., description="Updated proposal with vote")
    vote_count: Optional[int] = Field(None, description="Total vote count")
    approval_count: Optional[int] = Field(None, description="Approval vote count")


class ProposalListQuery(BaseAPIModel):
    """Query parameters for listing proposals."""
    tenant: Optional[str] = Field(None, description="Filter by tenant")
    status: Optional[ProposalStatus] = Field(None, description="Filter by status")
    capability_id: Optional[str] = Field(None, description="Filter by capability")
    action: Optional[GovernanceAction] = Field(None, description="Filter by action")
    voter: Optional[str] = Field(None, description="Filter by voter participation")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(
        default="created_at",
        pattern=r"^(created_at|updated_at|expires_at|priority)$",
        description="Sort field"
    )
    sort_order: Optional[str] = Field(
        default="desc",
        pattern=r"^(asc|desc)$",
        description="Sort order"
    )


class ProposalListResponse(BaseAPIModel):
    """Response model for proposal listing."""
    proposals: List[Dict[str, Any]] = Field(..., description="List of proposals")
    total: int = Field(..., ge=0, description="Total number of proposals")
    page: int = Field(..., ge=1, description="Current page")
    size: int = Field(..., ge=1, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


class ProposalExecutionRequest(BaseAPIModel):
    """Request model for executing approved proposals."""
    proposal_id: int = Field(..., ge=1, description="Proposal ID to execute")
    executor: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Executor identifier"
    )
    dry_run: bool = Field(
        default=False,
        description="Whether to perform a dry run"
    )
    execution_parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional execution parameters"
    )


class ProposalExecutionResponse(BaseAPIModel):
    """Response model for proposal execution."""
    ok: bool = Field(..., description="Execution success")
    proposal_id: int = Field(..., description="Executed proposal ID")
    execution_id: Optional[str] = Field(None, description="Execution tracking ID")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    errors: Optional[List[str]] = Field(None, description="Execution errors if any")