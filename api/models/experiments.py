"""Pydantic models for experiments API endpoints.

This module defines the Pydantic models used for request and response validation
in the experiments API endpoints. These models ensure that the data flowing
in and out of the API conforms to a specific schema.
"""

from pydantic import Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, MetricsModel, TimestampedModel


class ExperimentArm(str, Enum):
    """Enumeration of standard experiment arms.

    Attributes:
        CONTROL: The control group.
        VARIANT: The variant group.
        CONTROL_SINGLE_PASS: A specific control group for single-pass experiments.
        VARIANT_DEBATE_TOOLS: A specific variant group for debate tools experiments.
    """
    CONTROL = "control"
    VARIANT = "variant"
    CONTROL_SINGLE_PASS = "control_single_pass"
    VARIANT_DEBATE_TOOLS = "variant_debate_tools"


class ExperimentStatus(str, Enum):
    """Enumeration of possible experiment statuses.

    Attributes:
        DRAFT: The experiment is a draft.
        ACTIVE: The experiment is active.
        PAUSED: The experiment is paused.
        COMPLETED: The experiment is completed.
        CANCELLED: The experiment is cancelled.
    """
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentRecordRequest(MetricsModel, TimestampedModel):
    """Request model for recording an experiment result.

    Attributes:
        experiment: The identifier of the experiment.
        arm: The identifier of the experiment arm.
        session_id: The session identifier for grouping related records.
        user_id: The user identifier.
        metadata: Additional experiment metadata.
        tags: Experiment tags for categorization.
    """
    experiment: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9._-]+$",
        description="Experiment identifier"
    )
    arm: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Experiment arm identifier"
    )
    session_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Session identifier for grouping related records"
    )
    user_id: Optional[str] = Field(
        None,
        max_length=100,
        description="User identifier"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional experiment metadata"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Experiment tags for categorization"
    )
    
    @validator('arm')
    def validate_arm(cls, v):
        """Validate the experiment arm.

        Args:
            v: The experiment arm.

        Returns:
            The validated experiment arm.

        Raises:
            ValueError: If the arm is empty.
        """
        # Allow standard arms or custom arms
        v = v.strip().lower()
        if not v:
            raise ValueError('Arm cannot be empty')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate the metadata.

        Args:
            v: The metadata.

        Returns:
            The validated metadata.

        Raises:
            ValueError: If the metadata is too large.
        """
        if v and len(str(v)) > 2000:  # Limit metadata size
            raise ValueError('Metadata too large (max 2KB when serialized)')
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
            # Clean and validate tags
            cleaned_tags = []
            for tag in v:
                if isinstance(tag, str) and tag.strip():
                    cleaned_tags.append(tag.strip().lower())
            return cleaned_tags[:10]  # Limit to 10 tags
        return []


class ExperimentRecordResponse(BaseAPIModel):
    """Response model for recording an experiment result.

    Attributes:
        ok: Whether the recording was successful.
        experiment: The identifier of the experiment.
        record_id: The identifier of the recorded result.
        total_records: The total number of records for this experiment.
    """
    ok: bool = Field(True)
    experiment: str = Field(..., description="Experiment identifier")
    record_id: Optional[str] = Field(None, description="Record identifier")
    total_records: Optional[int] = Field(None, description="Total records for this experiment")


class ExperimentSummaryRequest(BaseAPIModel):
    """Request model for retrieving an experiment summary.

    Attributes:
        experiment: The identifier of the experiment.
        arm_a: The first arm to compare.
        arm_b: The second arm to compare.
        start_date: The start date for filtering results.
        end_date: The end date for filtering results.
        min_samples: The minimum number of samples required for statistical significance.
        confidence_level: The confidence level for statistical tests.
    """
    experiment: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Experiment identifier"
    )
    arm_a: str = Field(
        default="control_single_pass",
        min_length=1,
        max_length=50,
        description="First arm to compare"
    )
    arm_b: str = Field(
        default="variant_debate_tools",
        min_length=1,
        max_length=50,
        description="Second arm to compare"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Filter results from this date"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="Filter results until this date"
    )
    min_samples: Optional[int] = Field(
        default=10,
        ge=1,
        le=10000,
        description="Minimum samples required for statistical significance"
    )
    confidence_level: Optional[float] = Field(
        default=0.95,
        ge=0.8,
        le=0.99,
        description="Confidence level for statistical tests"
    )
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate the date range.

        Args:
            v: The end date.
            values: The other values in the model.

        Returns:
            The validated end date.

        Raises:
            ValueError: If the end date is before the start date.
        """
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
        return v


class ExperimentSummaryResponse(BaseAPIModel):
    """Response model for an experiment summary.

    Attributes:
        ready: Whether the summary is ready (i.e., enough data).
        experiment: The identifier of the experiment.
        arm_a: The first arm.
        arm_b: The second arm.
        samples_a: The number of samples for arm A.
        samples_b: The number of samples for arm B.
        score_a: The average score for arm A.
        score_b: The average score for arm B.
        score_improvement: The score improvement of B over A.
        cost_a: The average cost for arm A.
        cost_b: The average cost for arm B.
        cost_improvement: The cost improvement of B over A.
        latency_a: The average latency for arm A.
        latency_b: The average latency for arm B.
        latency_improvement: The latency improvement of B over A.
        score_p_value: The p-value for the score difference.
        cost_p_value: The p-value for the cost difference.
        latency_p_value: The p-value for the latency difference.
        statistically_significant: Whether the results are statistically significant.
        confidence_interval: The confidence intervals for the metrics.
        recommendation: The recommendation based on the results.
        winner: The winning arm if the results are significant.
        analysis_date: The date of the analysis.
        data_quality_score: The data quality assessment score.
    """
    ready: bool = Field(..., description="Whether summary is ready (enough data)")
    experiment: str = Field(..., description="Experiment identifier")
    arm_a: str = Field(..., description="First arm")
    arm_b: str = Field(..., description="Second arm")
    
    # Sample counts
    samples_a: Optional[int] = Field(None, description="Samples for arm A")
    samples_b: Optional[int] = Field(None, description="Samples for arm B")
    
    # Performance metrics
    score_a: Optional[float] = Field(None, description="Average score for arm A")
    score_b: Optional[float] = Field(None, description="Average score for arm B")
    score_improvement: Optional[float] = Field(None, description="Score improvement (B vs A)")
    
    cost_a: Optional[float] = Field(None, description="Average cost for arm A")
    cost_b: Optional[float] = Field(None, description="Average cost for arm B")
    cost_improvement: Optional[float] = Field(None, description="Cost improvement (B vs A)")
    
    latency_a: Optional[float] = Field(None, description="Average latency for arm A")
    latency_b: Optional[float] = Field(None, description="Average latency for arm B")
    latency_improvement: Optional[float] = Field(None, description="Latency improvement (B vs A)")
    
    # Statistical significance
    score_p_value: Optional[float] = Field(None, description="P-value for score difference")
    cost_p_value: Optional[float] = Field(None, description="P-value for cost difference")
    latency_p_value: Optional[float] = Field(None, description="P-value for latency difference")
    
    statistically_significant: Optional[bool] = Field(None, description="Overall statistical significance")
    confidence_interval: Optional[Dict[str, List[float]]] = Field(None, description="Confidence intervals")
    
    # Recommendations
    recommendation: Optional[str] = Field(None, description="Recommendation based on results")
    winner: Optional[str] = Field(None, description="Winning arm if significant")
    
    # Metadata
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Data quality assessment")


class ExperimentConfigRequest(BaseAPIModel):
    """Request model for configuring an experiment.

    Attributes:
        experiment: The identifier of the experiment.
        description: The description of the experiment.
        arms: The list of experiment arms.
        traffic_allocation: The traffic allocation per arm.
        success_metrics: The primary success metrics.
        minimum_sample_size: The minimum sample size per arm.
        max_duration_days: The maximum duration of the experiment in days.
    """
    experiment: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9._-]+$",
        description="Experiment identifier"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Experiment description"
    )
    arms: List[str] = Field(
        ...,
        min_items=2,
        max_items=10,
        description="List of experiment arms"
    )
    traffic_allocation: Optional[Dict[str, float]] = Field(
        None,
        description="Traffic allocation per arm (must sum to 1.0)"
    )
    success_metrics: List[str] = Field(
        default=["score", "cost", "latency_ms"],
        description="Primary success metrics"
    )
    minimum_sample_size: Optional[int] = Field(
        default=100,
        ge=10,
        le=100000,
        description="Minimum sample size per arm"
    )
    max_duration_days: Optional[int] = Field(
        default=30,
        ge=1,
        le=365,
        description="Maximum experiment duration"
    )
    
    @validator('arms')
    def validate_arms(cls, v):
        """Validate the experiment arms.

        Args:
            v: The list of experiment arms.

        Returns:
            The validated list of experiment arms.

        Raises:
            ValueError: If the arms are not unique.
        """
        if len(set(v)) != len(v):
            raise ValueError('Experiment arms must be unique')
        return v
    
    @validator('traffic_allocation')
    def validate_traffic_allocation(cls, v, values):
        """Validate the traffic allocation.

        Args:
            v: The traffic allocation dictionary.
            values: The other values in the model.

        Returns:
            The validated traffic allocation dictionary.

        Raises:
            ValueError: If the traffic allocation is invalid.
        """
        if v:
            if 'arms' in values:
                # Check that all arms have allocation
                for arm in values['arms']:
                    if arm not in v:
                        raise ValueError(f'Missing traffic allocation for arm: {arm}')
            
            # Check that allocations sum to 1.0 (with small tolerance)
            total = sum(v.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError(f'Traffic allocations must sum to 1.0, got {total}')
            
            # Check that all allocations are positive
            for arm, allocation in v.items():
                if allocation <= 0:
                    raise ValueError(f'Traffic allocation for {arm} must be positive')
        
        return v


class ExperimentConfigResponse(BaseAPIModel):
    """Response model for configuring an experiment.

    Attributes:
        experiment: The identifier of the experiment.
        status: The configuration status.
        config_id: The identifier of the configuration.
        message: The status message.
        arms_configured: The list of successfully configured arms.
        created_at: The timestamp of the configuration.
    """
    experiment: str = Field(..., description="Experiment identifier")
    status: str = Field(..., description="Configuration status")
    config_id: Optional[str] = Field(None, description="Configuration identifier")
    message: str = Field(..., description="Status message")
    arms_configured: List[str] = Field(default_factory=list, description="Successfully configured arms")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Configuration timestamp")