"""Pydantic models for orchestration API endpoints.

This module defines the Pydantic models used for request and response validation
in the orchestration API endpoints. These models ensure that the data flowing
in and out of the API conforms to a specific schema.
"""

from pydantic import Field, validator
from typing import Dict, Any, Optional
from .base import BaseAPIModel
import os


class OrchestrateRequest(BaseAPIModel):
    """Request model for the orchestration endpoint.

    Attributes:
        goal: The goal to achieve through orchestration.
        budget_usd: The budget limit in USD.
        risk: The risk level (0=lowest, 5=highest).
        priority: The priority level of the task.
        timeout_minutes: The timeout in minutes.
        metadata: Additional metadata for the orchestration.
    """
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
        """Validate the goal.

        Args:
            v: The goal string.

        Returns:
            The validated goal string.

        Raises:
            ValueError: If the goal is too short.
        """
        # Remove excessive whitespace
        v = ' '.join(v.split())
        if len(v.strip()) < 10:
            raise ValueError('Goal must be at least 10 characters long after trimming whitespace')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate the metadata.

        Args:
            v: The metadata dictionary.

        Returns:
            The validated metadata dictionary.

        Raises:
            ValueError: If the metadata is too large.
        """
        if v and len(str(v)) > 10000:  # Limit metadata size
            raise ValueError('Metadata too large (max 10KB when serialized)')
        return v


class OrchestrateResponse(BaseAPIModel):
    """Response model for the orchestration endpoint.

    Attributes:
        run_id: The unique identifier for the run.
        playbook: The name of the selected playbook.
        estimated_cost: The estimated cost in USD.
        estimated_duration: The estimated duration in minutes.
    """
    run_id: str = Field(..., description="Unique run identifier")
    playbook: str = Field(..., description="Selected playbook name")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in USD")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")


class AgentManifest(BaseAPIModel):
    """Model for an agent registration manifest.

    Attributes:
        name: The name of the agent.
        version: The semantic version of the agent.
        capabilities: A list of the agent's capabilities.
        description: A description of the agent.
        endpoints: The API endpoints of the agent.
        requirements: The requirements and constraints of the agent.
    """
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
        """Validate the capabilities.

        Args:
            v: The list of capabilities.

        Returns:
            The validated list of capabilities.

        Raises:
            ValueError: If the list is empty or contains invalid capabilities.
        """
        if not v:
            raise ValueError('At least one capability must be specified')
        # Validate each capability format
        for cap in v:
            if not isinstance(cap, str) or len(cap.strip()) == 0:
                raise ValueError('Each capability must be a non-empty string')
        return [cap.strip() for cap in v]


class AgentRegistrationResponse(BaseAPIModel):
    """Response model for agent registration.

    Attributes:
        registered: The name of the registered agent.
        agent_id: The assigned agent ID.
        status: The registration status.
    """
    registered: str = Field(..., description="Registered agent name")
    agent_id: Optional[str] = Field(None, description="Assigned agent ID")
    status: str = Field(default="active", description="Registration status")


class PlaybookTrialRequest(BaseAPIModel):
    """Request model for activating a playbook trial.

    Attributes:
        playbook_name: The name of the playbook to enable for trial.
        trial_percentage: The percentage of traffic to route to the trial.
        duration_hours: The duration of the trial in hours.
    """
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
    """Response model for activating a playbook trial.

    Attributes:
        trial_enabled: The name of the playbook with the trial enabled.
        trial_id: The identifier of the trial.
        expires_at: The timestamp when the trial expires.
    """
    trial_enabled: str = Field(..., description="Playbook name with trial enabled")
    trial_id: Optional[str] = Field(None, description="Trial identifier")
    expires_at: Optional[str] = Field(None, description="Trial expiration timestamp")