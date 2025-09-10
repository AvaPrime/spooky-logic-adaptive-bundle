"""Pydantic models for orchestration API endpoints."""

from pydantic import Field, validator
from typing import Dict, Any, Optional
from .base import BaseAPIModel
import os


class OrchestrateRequest(BaseAPIModel):
    """Request model for orchestration endpoint."""
    goal: str = Field(
        ..., 
        min_length=10, 
        max_length=1000, 
        description="The goal to achieve through orchestration"
    )
    budget_usd: float = Field(
        default=float(os.getenv("BUDGET_MAX_USD", "0.25")),
        ge=0.01,
        le=1000.0,
        description="Budget limit in USD"
    )
    risk: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Risk level (0=lowest, 5=highest)"
    )
    priority: Optional[str] = Field(
        default="normal",
        pattern=r"^(low|normal|high|critical)$",
        description="Task priority level"
    )
    timeout_minutes: Optional[int] = Field(
        default=30,
        ge=1,
        le=1440,
        description="Timeout in minutes"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata for the orchestration"
    )
    
    @validator('goal')
    def validate_goal(cls, v):
        # Remove excessive whitespace
        v = ' '.join(v.split())
        if len(v.strip()) < 10:
            raise ValueError('Goal must be at least 10 characters long after trimming whitespace')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v and len(str(v)) > 10000:  # Limit metadata size
            raise ValueError('Metadata too large (max 10KB when serialized)')
        return v


class OrchestrateResponse(BaseAPIModel):
    """Response model for orchestration endpoint."""
    run_id: str = Field(..., description="Unique run identifier")
    playbook: str = Field(..., description="Selected playbook name")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in USD")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")


class AgentManifest(BaseAPIModel):
    """Model for agent registration manifest."""
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Agent name"
    )
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$",
        description="Semantic version (e.g., 1.0.0)"
    )
    capabilities: list[str] = Field(
        ...,
        min_items=1,
        description="List of agent capabilities"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Agent description"
    )
    endpoints: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Agent API endpoints"
    )
    requirements: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent requirements and constraints"
    )
    
    @validator('capabilities')
    def validate_capabilities(cls, v):
        if not v:
            raise ValueError('At least one capability must be specified')
        # Validate each capability format
        for cap in v:
            if not isinstance(cap, str) or len(cap.strip()) == 0:
                raise ValueError('Each capability must be a non-empty string')
        return [cap.strip() for cap in v]


class AgentRegistrationResponse(BaseAPIModel):
    """Response model for agent registration."""
    registered: str = Field(..., description="Registered agent name")
    agent_id: Optional[str] = Field(None, description="Assigned agent ID")
    status: str = Field(default="active", description="Registration status")


class PlaybookTrialRequest(BaseAPIModel):
    """Request model for playbook trial activation."""
    playbook_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Playbook name to enable for trial"
    )
    trial_percentage: Optional[float] = Field(
        default=10.0,
        ge=0.1,
        le=100.0,
        description="Percentage of traffic to route to trial"
    )
    duration_hours: Optional[int] = Field(
        default=24,
        ge=1,
        le=168,  # 1 week max
        description="Trial duration in hours"
    )


class PlaybookTrialResponse(BaseAPIModel):
    """Response model for playbook trial activation."""
    trial_enabled: str = Field(..., description="Playbook name with trial enabled")
    trial_id: Optional[str] = Field(None, description="Trial identifier")
    expires_at: Optional[str] = Field(None, description="Trial expiration timestamp")