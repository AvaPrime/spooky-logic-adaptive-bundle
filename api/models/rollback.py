"""Pydantic models for rollback API endpoints.

This module defines the Pydantic models used for request and response validation
in the rollback API endpoints. These models ensure that the data flowing
in and out of the API conforms to a specific schema.
"""

from pydantic import Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from .base import BaseAPIModel, TimestampedModel


class RollbackTrigger(str, Enum):
    """Enumeration of possible rollback trigger types.

    Attributes:
        ERROR_RATE: Rollback triggered by error rate.
        LATENCY: Rollback triggered by latency.
        THROUGHPUT: Rollback triggered by throughput.
        CUSTOM_METRIC: Rollback triggered by a custom metric.
        MANUAL: Rollback triggered manually.
        HEALTH_CHECK: Rollback triggered by a health check failure.
        DEPENDENCY_FAILURE: Rollback triggered by a dependency failure.
    """
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    CUSTOM_METRIC = "custom_metric"
    MANUAL = "manual"
    HEALTH_CHECK = "health_check"
    DEPENDENCY_FAILURE = "dependency_failure"


class RollbackStatus(str, Enum):
    """Enumeration of possible rollback statuses.

    Attributes:
        INACTIVE: The rollback is inactive.
        MONITORING: The system is monitoring for rollback triggers.
        TRIGGERED: A rollback has been triggered.
        ROLLING_BACK: The system is currently rolling back.
        COMPLETED: The rollback has completed successfully.
        FAILED: The rollback has failed.
        PAUSED: The rollback is paused.
    """
    INACTIVE = "inactive"
    MONITORING = "monitoring"
    TRIGGERED = "triggered"
    ROLLING_BACK = "rolling_back"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class MetricComparison(str, Enum):
    """Enumeration of metric comparison operators.

    Attributes:
        GREATER_THAN: Greater than.
        GREATER_EQUAL: Greater than or equal to.
        LESS_THAN: Less than.
        LESS_EQUAL: Less than or equal to.
        EQUAL: Equal to.
        NOT_EQUAL: Not equal to.
    """
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    EQUAL = "eq"
    NOT_EQUAL = "ne"


class RollbackThreshold(BaseAPIModel):
    """A configuration for a rollback threshold.

    Attributes:
        metric_name: The name of the metric to monitor.
        comparison: The comparison operator for the threshold.
        threshold_value: The threshold value for triggering a rollback.
        duration_seconds: The duration the threshold must be breached.
        sample_size: The minimum number of samples required for evaluation.
        weight: The weight of this threshold in the decision-making process.
        enabled: Whether the threshold is active.
    """
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
    """A configuration for a rollback target.

    Attributes:
        deployment_id: The identifier of the target deployment.
        version: The target version to roll back to.
        environment: The target environment (e.g., prod, staging).
        rollback_strategy: The rollback deployment strategy.
        traffic_percentage: The traffic percentage for a gradual rollback.
        validation_checks: A list of post-rollback validation checks.
    """
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
    """Request model for starting auto-rollback monitoring.

    Attributes:
        deployment_id: The deployment to monitor.
        thresholds: The rollback thresholds to monitor.
        rollback_target: The target configuration for the rollback.
        monitoring_duration: The maximum monitoring duration in seconds.
        cooldown_period: The cooldown period between rollbacks.
        notification_channels: The notification channels for alerts.
        auto_approve: Whether to auto-approve the rollback without human intervention.
        dry_run: Whether to simulate the rollback without actual execution.
        tags: Additional tags for tracking.
    """
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
        """Validate the rollback thresholds.

        Args:
            v: The list of rollback thresholds.

        Returns:
            The validated list of rollback thresholds.

        Raises:
            ValueError: If the thresholds are invalid.
        """
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
        """Validate the notification channels.

        Args:
            v: The list of notification channels.

        Returns:
            The validated list of notification channels.

        Raises:
            ValueError: If any of the notification channels are invalid.
        """
        if v:
            valid_channels = ['email', 'slack', 'webhook', 'sms', 'pagerduty']
            for channel in v:
                if channel not in valid_channels:
                    raise ValueError(f'Invalid notification channel: {channel}. Valid options: {valid_channels}')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate the tags.

        Args:
            v: The tags dictionary.

        Returns:
            The validated tags dictionary.

        Raises:
            ValueError: If the tags are too large.
        """
        if v and len(str(v)) > 2000:  # 2KB limit
            raise ValueError('Tags too large (max 2KB when serialized)')
        return v


class AutoRollbackStartResponse(BaseAPIModel):
    """Response model for starting auto-rollback monitoring.

    Attributes:
        session_id: The ID of the rollback monitoring session.
        deployment_id: The ID of the monitored deployment.
        status: The status of the rollback monitoring.
        monitoring_started_at: The timestamp when monitoring started.
        monitoring_expires_at: The timestamp when monitoring will expire.
        thresholds_count: The number of active thresholds.
        rollback_target: The configured rollback target.
        dry_run: Whether this is a dry run.
    """
    session_id: str = Field(..., description="Rollback monitoring session ID")
    deployment_id: str = Field(..., description="Monitored deployment ID")
    status: RollbackStatus = Field(default=RollbackStatus.MONITORING)
    monitoring_started_at: datetime = Field(default_factory=datetime.utcnow)
    monitoring_expires_at: datetime = Field(..., description="When monitoring will expire")
    thresholds_count: int = Field(..., ge=1, description="Number of active thresholds")
    rollback_target: RollbackTarget = Field(..., description="Configured rollback target")
    dry_run: bool = Field(default=False, description="Whether this is a dry run")


class RollbackStatusRequest(BaseAPIModel):
    """Request model for checking the status of a rollback.

    Attributes:
        session_id: The specific session ID to check (latest if not provided).
        deployment_id: Filter by deployment ID.
        include_metrics: Whether to include current metric values in the response.
        include_history: Whether to include rollback history in the response.
    """
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
    """A snapshot of a metric at a specific point in time.

    Attributes:
        metric_name: The name of the metric.
        current_value: The current value of the metric.
        threshold_value: The configured threshold for the metric.
        comparison: The comparison operator for the threshold.
        is_breached: Whether the threshold is currently breached.
        breach_duration: How long the threshold has been breached in seconds.
        sample_count: The number of samples collected.
        last_updated: The timestamp of the last metric update.
    """
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
    """A record of a rollback event.

    Attributes:
        event_type: The type of the rollback event.
        timestamp: The timestamp of the event.
        message: A description of the event.
        details: Additional details about the event.
        triggered_by: What triggered this event.
    """
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
    """Response model for the status of a rollback.

    Attributes:
        session_id: The ID of the rollback session.
        deployment_id: The monitored deployment.
        status: The current rollback status.
        started_at: The timestamp when monitoring started.
        expires_at: The timestamp when monitoring expires.
        last_check_at: The timestamp of the last health check.
        active_thresholds: The number of active thresholds.
        breached_thresholds: The number of breached thresholds.
        current_metrics: The current metric snapshots.
        rollback_target: The configured rollback target.
        rollback_triggered_at: The timestamp when the rollback was triggered.
        rollback_completed_at: The timestamp when the rollback completed.
        rollback_progress: The rollback progress percentage.
        events: A list of recent rollback events.
        error_message: An error message if the rollback failed.
        dry_run: Whether this was a dry run.
        next_check_in: The number of seconds until the next health check.
    """
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
    """Request model for a rollback tick/heartbeat.

    Attributes:
        session_id: The ID of the rollback session to tick.
        force_check: Whether to force an immediate threshold check.
        update_metrics: Manual metric updates.
    """
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
    """Response model for a rollback tick.

    Attributes:
        session_id: The ID of the rollback session.
        status: The current status after the tick.
        checks_performed: The number of checks performed.
        thresholds_evaluated: The number of thresholds evaluated.
        breaches_detected: The number of new breaches detected.
        actions_taken: A list of actions taken during this tick.
        next_tick_in: The number of seconds until the next automatic tick.
        tick_duration_ms: The time taken for this tick operation in milliseconds.
    """
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
    """Request model for rollback control operations.

    Attributes:
        session_id: The ID of the rollback session to control.
        action: The control action to perform.
        reason: The reason for the control action.
        force: Whether to force the action even if it is not in the appropriate state.
    """
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
    """Response model for rollback control operations.

    Attributes:
        session_id: The ID of the rollback session.
        action: The action that was performed.
        previous_status: The status before the action.
        current_status: The status after the action.
        success: Whether the action was successful.
        message: A result message.
        timestamp: The timestamp of the operation.
    """
    session_id: str = Field(..., description="Rollback session ID")
    action: str = Field(..., description="Action that was performed")
    previous_status: RollbackStatus = Field(..., description="Status before action")
    current_status: RollbackStatus = Field(..., description="Status after action")
    success: bool = Field(..., description="Whether action was successful")
    message: str = Field(..., description="Result message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)