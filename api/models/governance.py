"""Pydantic models for governance API endpoints.

This module defines the Pydantic models used for request and response validation
in the governance API endpoints. These models ensure that the data flowing
in and out of the API conforms to a specific schema.
"""

from pydantic import Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, TenantModel, CapabilityModel, TimestampedModel


class GovernanceAction(str, Enum):
    """Enumeration of valid governance actions.

    Attributes:
        CREATE: Create a new resource.
        UPDATE: Update an existing resource.
        DELETE: Delete a resource.
        SUSPEND: Suspend a resource.
        ACTIVATE: Activate a resource.
        CONFIGURE: Configure a resource.
    """
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SUSPEND = "suspend"
    ACTIVATE = "activate"
    CONFIGURE = "configure"


class ProposalStatus(str, Enum):
    """Enumeration of possible proposal statuses.

    Attributes:
        DRAFT: The proposal is a draft.
        ACTIVE: The proposal is active and open for voting.
        APPROVED: The proposal has been approved.
        REJECTED: The proposal has been rejected.
        EXECUTED: The proposal has been executed.
        EXPIRED: The proposal has expired.
    """
    DRAFT = "draft"
    ACTIVE = "active"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class ProposalRequest(TenantModel, CapabilityModel, TimestampedModel):
    """Request model for creating a governance proposal.

    Attributes:
        action: The action to be taken if the proposal is approved.
        rationale: A detailed rationale for the proposal.
        title: The title of the proposal.
        parameters: Action-specific parameters.
        priority: The priority of the proposal.
        expires_at: The timestamp when the proposal expires.
        required_approvals: The number of approvals required for the proposal to pass.
    """
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
        """Validate the rationale.

        Args:
            v: The rationale string.

        Returns:
            The validated rationale string.

        Raises:
            ValueError: If the rationale is too short.
        """
        # Clean up whitespace
        v = ' '.join(v.split())
        if len(v) < 20:
            raise ValueError('Rationale must be at least 20 characters after cleaning whitespace')
        return v
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        """Validate the expiration timestamp.

        Args:
            v: The expiration timestamp.

        Returns:
            The validated expiration timestamp.

        Raises:
            ValueError: If the expiration timestamp is in the past.
        """
        if v and v <= datetime.utcnow():
            raise ValueError('Expiration date must be in the future')
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate the parameters.

        Args:
            v: The parameters dictionary.

        Returns:
            The validated parameters dictionary.

        Raises:
            ValueError: If the parameters are too large.
        """
        if v and len(str(v)) > 5000:  # Limit parameter size
            raise ValueError('Parameters too large (max 5KB when serialized)')
        return v


class ProposalResponse(BaseAPIModel):
    """Response model for creating a governance proposal.

    Attributes:
        ok: Whether the proposal creation was successful.
        proposal: The details of the created proposal.
        proposal_id: The ID of the created proposal.
    """
    ok: bool = Field(True)
    proposal: Dict[str, Any] = Field(..., description="Created proposal details")
    proposal_id: Optional[int] = Field(None, description="Proposal ID")


class VoteRequest(BaseAPIModel):
    """Request model for casting a vote on a proposal.

    Attributes:
        proposal_id: The ID of the proposal to vote on.
        voter: The identifier of the voter.
        approve: Whether the vote is for approval or rejection.
        comment: An optional comment for the vote.
        weight: The weight of the vote (for weighted voting systems).
    """
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
        """Validate the vote comment.

        Args:
            v: The vote comment.

        Returns:
            The validated vote comment.
        """
        if v:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class VoteResponse(BaseAPIModel):
    """Response model for casting a vote.

    Attributes:
        ok: Whether the vote was successful.
        proposal: The updated proposal with the new vote.
        vote_count: The total number of votes on the proposal.
        approval_count: The number of approval votes on the proposal.
    """
    ok: bool = Field(True)
    proposal: Dict[str, Any] = Field(..., description="Updated proposal with vote")
    vote_count: Optional[int] = Field(None, description="Total vote count")
    approval_count: Optional[int] = Field(None, description="Approval vote count")


class ProposalListQuery(BaseAPIModel):
    """Query parameters for listing proposals.

    Attributes:
        tenant: Filter by tenant.
        status: Filter by proposal status.
        capability_id: Filter by capability ID.
        action: Filter by governance action.
        voter: Filter by voter participation.
        page: The page number for pagination.
        size: The page size for pagination.
        sort_by: The field to sort the results by.
        sort_order: The sort order (asc or desc).
    """
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
    """Response model for listing proposals.

    Attributes:
        proposals: A list of proposals.
        total: The total number of proposals.
        page: The current page number.
        size: The page size.
        has_next: Whether there are more pages.
    """
    proposals: List[Dict[str, Any]] = Field(..., description="List of proposals")
    total: int = Field(..., ge=0, description="Total number of proposals")
    page: int = Field(..., ge=1, description="Current page")
    size: int = Field(..., ge=1, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


class ProposalExecutionRequest(BaseAPIModel):
    """Request model for executing an approved proposal.

    Attributes:
        proposal_id: The ID of the proposal to execute.
        executor: The identifier of the executor.
        dry_run: Whether to perform a dry run without actually executing the proposal.
        execution_parameters: Additional parameters for the execution.
    """
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
    """Response model for executing a proposal.

    Attributes:
        ok: Whether the execution was successful.
        proposal_id: The ID of the executed proposal.
        execution_id: The ID for tracking the execution.
        result: The result of the execution.
        errors: A list of errors if the execution failed.
    """
    ok: bool = Field(..., description="Execution success")
    proposal_id: int = Field(..., description="Executed proposal ID")
    execution_id: Optional[str] = Field(None, description="Execution tracking ID")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    errors: Optional[List[str]] = Field(None, description="Execution errors if any")


class GovernanceBoardResponse(BaseAPIModel):
    """Response model for the governance board overview.

    Attributes:
        proposals: A list of all proposals.
        total_proposals: The total number of proposals.
        active_proposals: The number of active proposals.
        completed_proposals: The number of completed proposals.
    """
    proposals: List[Dict[str, Any]] = Field(..., description="List of all proposals")
    total_proposals: int = Field(..., ge=0, description="Total number of proposals")
    active_proposals: int = Field(..., ge=0, description="Number of active proposals")
    completed_proposals: int = Field(..., ge=0, description="Number of completed proposals")


class ProposalDetailsResponse(BaseAPIModel):
    """Response model for detailed proposal information.

    Attributes:
        proposal: The detailed information of the proposal.
        votes: A list of votes on this proposal.
        vote_summary: A summary of the vote counts.
        can_vote: Whether the current user can vote on this proposal.
        can_execute: Whether the proposal can be executed.
    """
    proposal: Dict[str, Any] = Field(..., description="Detailed proposal information")
    votes: List[Dict[str, Any]] = Field(default_factory=list, description="List of votes on this proposal")
    vote_summary: Dict[str, int] = Field(default_factory=dict, description="Vote count summary")
    can_vote: bool = Field(True, description="Whether current user can vote")
    can_execute: bool = Field(False, description="Whether proposal can be executed")