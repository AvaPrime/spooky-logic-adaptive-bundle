"""Pydantic models for rollback API endpoints."""

from pydantic import Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from .base import BaseAPIModel, TimestampedModel


class RollbackTrigger(str, Enum):
    """Rollback trigger types."""
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    CUSTOM_METRIC = "custom_metric"
    MANUAL = "manual"
    HEALTH_CHECK = "health_check"
    DEPENDENCY_FAILURE = "dependency_failure"


class RollbackStatus(str, Enum):
    """Rollback status values."""
    INACTIVE = "inactive"
    MONITORING = "monitoring"
    TRIGGERED = "triggered"
    ROLLING_BACK = "rolling_back"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class MetricComparison(str, Enum):
    """Metric comparison operators."""
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    EQUAL = "eq"
    NOT_EQUAL = "ne"


class RollbackThreshold(BaseAPIModel):
    """Rollback threshold configuration."""
    metric_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the metric to monitor"
    )
    comparison: MetricComparison = Field(
        ...,
        description="Comparison operator for threshold"
    )
    threshold_value: float = Field(
        ...,
        description="Threshold value for triggering rollback"
    )
    duration_seconds: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="Duration threshold must be breached (10s-1h)"
    )
    sample_size: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Minimum samples required for evaluation"
    )
    weight: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Weight of this threshold in decision making"
    )
    enabled: bool = Field(default=True, description="Whether threshold is active")


class RollbackTarget(BaseAPIModel):
    """Rollback target configuration."""
    deployment_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Target deployment identifier"
    )
    version: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Target version to rollback to"
    )
    environment: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Target environment (e.g., prod, staging)"
    )
    rollback_strategy: str = Field(
        default="blue_green",
        pattern=r"^(blue_green|canary|rolling|immediate)$",
        description="Rollback deployment strategy"
    )
    traffic_percentage: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Traffic percentage for gradual rollback"
    )
    validation_checks: Optional[List[str]] = Field(
        default_factory=list,
        max_items=20,
        description="Post-rollback validation checks"
    )


class AutoRollbackStartRequest(TimestampedModel):
    """Request model for starting auto-rollback monitoring."""
    deployment_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Deployment to monitor"
    )
    thresholds: List[RollbackThreshold] = Field(
        ...,
        min_items=1,
        max_items=20,
        description="Rollback thresholds to monitor"
    )
    rollback_target: RollbackTarget = Field(
        ...,
        description="Target configuration for rollback"
    )
    monitoring_duration: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="Maximum monitoring duration in seconds (5m-24h)"
    )
    cooldown_period: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Cooldown period between rollbacks (1m-1h)"
    )
    notification_channels: Optional[List[str]] = Field(
        default_factory=list,
        max_items=10,
        description="Notification channels for alerts"
    )
    auto_approve: bool = Field(
        default=False,
        description="Whether to auto-approve rollback without human intervention"
    )
    dry_run: bool = Field(
        default=False,
        description="Simulate rollback without actual execution"
    )
    tags: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Additional tags for tracking"
    )
    
    @validator('thresholds')
    def validate_thresholds(cls, v):
        if not v:
            raise ValueError('At least one threshold must be specified')
        
        # Check for duplicate metric names
        metric_names = [t.metric_name for t in v]
        if len(metric_names) != len(set(metric_names)):
            raise ValueError('Duplicate metric names in thresholds')
        
        # Validate threshold values make sense
        for threshold in v:
            if threshold.metric_name in ['error_rate', 'success_rate'] and threshold.threshold_value > 1.0:
                raise ValueError(f'Rate metrics should be between 0.0 and 1.0, got {threshold.threshold_value}')
        
        return v
    
    @validator('notification_channels')
    def validate_notification_channels(cls, v):
        if v:
            valid_channels = ['email', 'slack', 'webhook', 'sms', 'pagerduty']
            for channel in v:
                if channel not in valid_channels:
                    raise ValueError(f'Invalid notification channel: {channel}. Valid options: {valid_channels}')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v and len(str(v)) > 2000:  # 2KB limit
            raise ValueError('Tags too large (max 2KB when serialized)')
        return v


class AutoRollbackStartResponse(BaseAPIModel):
    """Response model for auto-rollback start."""
    session_id: str = Field(..., description="Rollback monitoring session ID")
    deployment_id: str = Field(..., description="Monitored deployment ID")
    status: RollbackStatus = Field(default=RollbackStatus.MONITORING)
    monitoring_started_at: datetime = Field(default_factory=datetime.utcnow)
    monitoring_expires_at: datetime = Field(..., description="When monitoring will expire")
    thresholds_count: int = Field(..., ge=1, description="Number of active thresholds")
    rollback_target: RollbackTarget = Field(..., description="Configured rollback target")
    dry_run: bool = Field(default=False, description="Whether this is a dry run")


class RollbackStatusRequest(BaseAPIModel):
    """Request model for rollback status check."""
    session_id: Optional[str] = Field(
        None,
        description="Specific session ID to check (latest if not provided)"
    )
    deployment_id: Optional[str] = Field(
        None,
        description="Filter by deployment ID"
    )
    include_metrics: bool = Field(
        default=True,
        description="Include current metric values in response"
    )
    include_history: bool = Field(
        default=False,
        description="Include rollback history"
    )


class MetricSnapshot(BaseAPIModel):
    """Current metric snapshot."""
    metric_name: str = Field(..., description="Metric name")
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Configured threshold")
    comparison: MetricComparison = Field(..., description="Comparison operator")
    is_breached: bool = Field(..., description="Whether threshold is currently breached")
    breach_duration: Optional[int] = Field(
        None,
        description="How long threshold has been breached (seconds)"
    )
    sample_count: int = Field(..., ge=0, description="Number of samples collected")
    last_updated: datetime = Field(..., description="Last metric update time")


class RollbackEvent(BaseAPIModel):
    """Rollback event record."""
    event_type: str = Field(
        ...,
        pattern=r"^(started|threshold_breached|triggered|completed|failed|paused|resumed)$",
        description="Type of rollback event"
    )
    timestamp: datetime = Field(..., description="Event timestamp")
    message: str = Field(..., max_length=500, description="Event description")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional event details"
    )
    triggered_by: Optional[str] = Field(
        None,
        description="What triggered this event"
    )


class RollbackStatusResponse(BaseAPIModel):
    """Response model for rollback status."""
    session_id: str = Field(..., description="Rollback session ID")
    deployment_id: str = Field(..., description="Monitored deployment")
    status: RollbackStatus = Field(..., description="Current rollback status")
    started_at: datetime = Field(..., description="When monitoring started")
    expires_at: Optional[datetime] = Field(None, description="When monitoring expires")
    last_check_at: datetime = Field(..., description="Last health check time")
    
    # Threshold and metric information
    active_thresholds: int = Field(..., ge=0, description="Number of active thresholds")
    breached_thresholds: int = Field(..., ge=0, description="Number of breached thresholds")
    current_metrics: Optional[List[MetricSnapshot]] = Field(
        None,
        description="Current metric snapshots"
    )
    
    # Rollback information
    rollback_target: Optional[RollbackTarget] = Field(
        None,
        description="Configured rollback target"
    )
    rollback_triggered_at: Optional[datetime] = Field(
        None,
        description="When rollback was triggered"
    )
    rollback_completed_at: Optional[datetime] = Field(
        None,
        description="When rollback completed"
    )
    rollback_progress: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Rollback progress percentage"
    )
    
    # Additional information
    events: Optional[List[RollbackEvent]] = Field(
        None,
        description="Recent rollback events"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if rollback failed"
    )
    dry_run: bool = Field(default=False, description="Whether this was a dry run")
    next_check_in: Optional[int] = Field(
        None,
        description="Seconds until next health check"
    )


class RollbackTickRequest(BaseAPIModel):
    """Request model for rollback tick/heartbeat."""
    session_id: str = Field(
        ...,
        description="Rollback session ID to tick"
    )
    force_check: bool = Field(
        default=False,
        description="Force immediate threshold check"
    )
    update_metrics: Optional[Dict[str, float]] = Field(
        None,
        description="Manual metric updates"
    )


class RollbackTickResponse(BaseAPIModel):
    """Response model for rollback tick."""
    session_id: str = Field(..., description="Rollback session ID")
    status: RollbackStatus = Field(..., description="Current status after tick")
    checks_performed: int = Field(..., ge=0, description="Number of checks performed")
    thresholds_evaluated: int = Field(..., ge=0, description="Thresholds evaluated")
    breaches_detected: int = Field(..., ge=0, description="New breaches detected")
    actions_taken: List[str] = Field(
        default_factory=list,
        description="Actions taken during this tick"
    )
    next_tick_in: Optional[int] = Field(
        None,
        description="Seconds until next automatic tick"
    )
    tick_duration_ms: Optional[float] = Field(
        None,
        description="Time taken for this tick operation"
    )


class RollbackControlRequest(BaseAPIModel):
    """Request model for rollback control operations."""
    session_id: str = Field(
        ...,
        description="Rollback session ID to control"
    )
    action: str = Field(
        ...,
        pattern=r"^(pause|resume|stop|approve|reject)$",
        description="Control action to perform"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for the control action"
    )
    force: bool = Field(
        default=False,
        description="Force action even if not in appropriate state"
    )


class RollbackControlResponse(BaseAPIModel):
    """Response model for rollback control operations."""
    session_id: str = Field(..., description="Rollback session ID")
    action: str = Field(..., description="Action that was performed")
    previous_status: RollbackStatus = Field(..., description="Status before action")
    current_status: RollbackStatus = Field(..., description="Status after action")
    success: bool = Field(..., description="Whether action was successful")
    message: str = Field(..., description="Result message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)