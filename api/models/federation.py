"""Pydantic models for federation API endpoints.

This module defines the Pydantic models used for request and response validation
in the federation API endpoints. These models ensure that the data flowing
in and out of the API conforms to a specific schema.
"""

from pydantic import Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .base import BaseAPIModel, TenantModel, MetricsModel, TimestampedModel


class ClusterStatus(str, Enum):
    """Enumeration of possible cluster statuses.

    Attributes:
        ACTIVE: The cluster is active.
        INACTIVE: The cluster is inactive.
        DEGRADED: The cluster is in a degraded state.
        MAINTENANCE: The cluster is under maintenance.
        QUARANTINED: The cluster is quarantined.
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    QUARANTINED = "quarantined"


class DriftSeverity(str, Enum):
    """Enumeration of drift detection severity levels.

    Attributes:
        LOW: Low severity drift.
        MEDIUM: Medium severity drift.
        HIGH: High severity drift.
        CRITICAL: Critical severity drift.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FederatedSampleRequest(TenantModel, MetricsModel, TimestampedModel):
    """Request model for ingesting a federated learning sample.

    Attributes:
        cluster_id: The identifier of the cluster.
        arm: The identifier of the experiment arm.
        ts: The timestamp of the sample (Unix timestamp).
        experiment_id: The associated experiment identifier.
        session_id: The session identifier.
        user_id: The user identifier (anonymized).
        model_version: The model version used.
        features: The feature values for this sample.
        metadata: Additional sample metadata.
    """
    cluster_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9._-]+$",
        description="Cluster identifier"
    )
    arm: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Experiment arm identifier"
    )
    ts: float = Field(
        ...,
        description="Timestamp of the sample (Unix timestamp)"
    )
    experiment_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Associated experiment identifier"
    )
    session_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Session identifier"
    )
    user_id: Optional[str] = Field(
        None,
        max_length=100,
        description="User identifier (anonymized)"
    )
    model_version: Optional[str] = Field(
        None,
        max_length=50,
        description="Model version used"
    )
    features: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Feature values for this sample"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional sample metadata"
    )
    
    @validator('ts')
    def validate_timestamp(cls, v):
        """Validate the timestamp.

        Args:
            v: The timestamp.

        Returns:
            The validated timestamp.

        Raises:
            ValueError: If the timestamp is too far in the past or future.
        """
        # Check if timestamp is reasonable (not too far in past/future)
        now = datetime.utcnow().timestamp()
        if v < now - 86400 * 365:  # More than 1 year ago
            raise ValueError('Timestamp too far in the past')
        if v > now + 3600:  # More than 1 hour in future
            raise ValueError('Timestamp too far in the future')
        return v
    
    @validator('features')
    def validate_features(cls, v):
        """Validate the features.

        Args:
            v: The features dictionary.

        Returns:
            The validated features dictionary.

        Raises:
            ValueError: If the features are invalid.
        """
        if v:
            # Validate feature values
            for feature_name, feature_value in v.items():
                if not isinstance(feature_value, (int, float)):
                    raise ValueError(f'Feature {feature_name} must be numeric')
                if abs(feature_value) > 1e10:  # Reasonable bounds
                    raise ValueError(f'Feature {feature_name} value too large')
            
            # Limit number of features
            if len(v) > 100:
                raise ValueError('Too many features (max 100)')
        
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
        if v and len(str(v)) > 5000:  # 5KB limit
            raise ValueError('Metadata too large (max 5KB when serialized)')
        return v


class FederatedSampleResponse(BaseAPIModel):
    """Response model for ingesting a federated learning sample.

    Attributes:
        ok: Whether the ingestion was successful.
        sample_id: The identifier of the ingested sample.
        cluster_id: The identifier of the cluster.
        ingested_at: The timestamp of the ingestion.
    """
    ok: bool = Field(True)
    sample_id: Optional[str] = Field(None, description="Sample identifier")
    cluster_id: str = Field(..., description="Cluster identifier")
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class FederatedSummaryRequest(TenantModel):
    """Request model for retrieving a federated learning summary.

    Attributes:
        arm_a: The first arm to compare.
        arm_b: The second arm to compare.
        time_window_hours: The time window for analysis in hours.
        min_samples_per_cluster: The minimum samples required per cluster.
        include_clusters: A list of specific clusters to include.
        exclude_clusters: A list of clusters to exclude from the analysis.
        aggregation_method: The method for aggregating cluster results.
    """
    arm_a: str = Field(
        default="control",
        min_length=1,
        max_length=50,
        description="First arm to compare"
    )
    arm_b: str = Field(
        default="variant",
        min_length=1,
        max_length=50,
        description="Second arm to compare"
    )
    time_window_hours: Optional[int] = Field(
        default=24,
        ge=1,
        le=8760,  # 1 year
        description="Time window for analysis in hours"
    )
    min_samples_per_cluster: Optional[int] = Field(
        default=10,
        ge=1,
        le=10000,
        description="Minimum samples required per cluster"
    )
    include_clusters: Optional[List[str]] = Field(
        None,
        description="Specific clusters to include"
    )
    exclude_clusters: Optional[List[str]] = Field(
        None,
        description="Clusters to exclude from analysis"
    )
    aggregation_method: Optional[str] = Field(
        default="weighted_average",
        pattern=r"^(simple_average|weighted_average|median|federated_learning)$",
        description="Method for aggregating cluster results"
    )
    
    @validator('include_clusters', 'exclude_clusters')
    def validate_cluster_lists(cls, v):
        """Validate the cluster lists.

        Args:
            v: The list of cluster IDs.

        Returns:
            The validated list of cluster IDs.

        Raises:
            ValueError: If any of the cluster IDs are invalid.
        """
        if v:
            # Validate cluster ID format
            for cluster_id in v:
                if not isinstance(cluster_id, str) or not cluster_id.strip():
                    raise ValueError('Cluster IDs must be non-empty strings')
            return [c.strip() for c in v]
        return v


class FederatedSummaryResponse(BaseAPIModel):
    """Response model for a federated learning summary.

    Attributes:
        tenant: The identifier of the tenant.
        arm_a: The first arm.
        arm_b: The second arm.
        global_score_a: The global average score for arm A.
        global_score_b: The global average score for arm B.
        global_cost_a: The global average cost for arm A.
        global_cost_b: The global average cost for arm B.
        global_latency_a: The global average latency for arm A.
        global_latency_b: The global average latency for arm B.
        cluster_results: The per-cluster results breakdown.
        total_samples: The total number of samples across all clusters.
        participating_clusters: The number of participating clusters.
        confidence_interval: The confidence intervals for the metrics.
        statistical_significance: The statistical significance per metric.
        recommendation: The overall recommendation.
        data_quality_score: The data quality assessment score.
        analysis_window: The analysis time window.
        generated_at: The timestamp when the summary was generated.
    """
    tenant: str = Field(..., description="Tenant identifier")
    arm_a: str = Field(..., description="First arm")
    arm_b: str = Field(..., description="Second arm")
    
    # Global aggregated metrics
    global_score_a: Optional[float] = Field(None, description="Global average score for arm A")
    global_score_b: Optional[float] = Field(None, description="Global average score for arm B")
    global_cost_a: Optional[float] = Field(None, description="Global average cost for arm A")
    global_cost_b: Optional[float] = Field(None, description="Global average cost for arm B")
    global_latency_a: Optional[float] = Field(None, description="Global average latency for arm A")
    global_latency_b: Optional[float] = Field(None, description="Global average latency for arm B")
    
    # Cluster-level breakdown
    cluster_results: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Per-cluster results breakdown"
    )
    
    # Statistical analysis
    total_samples: int = Field(..., ge=0, description="Total samples across all clusters")
    participating_clusters: int = Field(..., ge=0, description="Number of participating clusters")
    confidence_interval: Optional[Dict[str, List[float]]] = Field(
        None,
        description="Confidence intervals for metrics"
    )
    statistical_significance: Optional[Dict[str, bool]] = Field(
        None,
        description="Statistical significance per metric"
    )
    
    # Recommendations
    recommendation: Optional[str] = Field(None, description="Overall recommendation")
    data_quality_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Data quality assessment"
    )
    
    # Metadata
    analysis_window: Dict[str, datetime] = Field(..., description="Analysis time window")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DriftDetectionRequest(TenantModel):
    """Request model for detecting data drift.

    Attributes:
        arm: The experiment arm to analyze for drift.
        baseline_window_hours: The baseline window in hours.
        detection_window_hours: The recent window for drift detection.
        sensitivity: The drift detection sensitivity.
        metrics_to_check: The metrics to check for drift.
        cluster_filter: A list of specific clusters to analyze.
    """
    arm: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Experiment arm to analyze for drift"
    )
    baseline_window_hours: Optional[int] = Field(
        default=168,  # 1 week
        ge=1,
        le=8760,
        description="Baseline window in hours"
    )
    detection_window_hours: Optional[int] = Field(
        default=24,
        ge=1,
        le=168,
        description="Recent window for drift detection"
    )
    sensitivity: Optional[str] = Field(
        default="medium",
        pattern=r"^(low|medium|high)$",
        description="Drift detection sensitivity"
    )
    metrics_to_check: Optional[List[str]] = Field(
        default=["score", "cost", "latency_ms"],
        description="Metrics to check for drift"
    )
    cluster_filter: Optional[List[str]] = Field(
        None,
        description="Specific clusters to analyze"
    )
    
    @validator('metrics_to_check')
    def validate_metrics(cls, v):
        """Validate the metrics to check.

        Args:
            v: The list of metrics to check.

        Returns:
            The validated list of metrics to check.

        Raises:
            ValueError: If any of the metrics are invalid.
        """
        valid_metrics = ['score', 'cost', 'latency_ms', 'error_rate', 'throughput']
        for metric in v:
            if metric not in valid_metrics:
                raise ValueError(f'Invalid metric: {metric}. Valid options: {valid_metrics}')
        return v


class DriftDetectionResponse(BaseAPIModel):
    """Response model for data drift detection.

    Attributes:
        tenant: The identifier of the tenant.
        arm: The analyzed arm.
        drift_detected: Whether drift was detected.
        overall_severity: The overall drift severity.
        cluster_drift: The drift analysis per cluster.
        metric_drift: The drift analysis per metric.
        baseline_period: The baseline time period.
        detection_period: The detection time period.
        total_samples_baseline: The number of samples in the baseline period.
        total_samples_detection: The number of samples in the detection period.
        recommendations: Recommendations based on the drift analysis.
        affected_clusters: A list of clusters showing significant drift.
        analysis_method: The drift detection method used.
        confidence_level: The statistical confidence level.
        generated_at: The timestamp when the detection was performed.
    """
    tenant: str = Field(..., description="Tenant identifier")
    arm: str = Field(..., description="Analyzed arm")
    drift_detected: bool = Field(..., description="Whether drift was detected")
    overall_severity: Optional[DriftSeverity] = Field(None, description="Overall drift severity")
    
    # Per-cluster drift analysis
    cluster_drift: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Drift analysis per cluster"
    )
    
    # Per-metric drift analysis
    metric_drift: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Drift analysis per metric"
    )
    
    # Statistical details
    baseline_period: Dict[str, datetime] = Field(..., description="Baseline time period")
    detection_period: Dict[str, datetime] = Field(..., description="Detection time period")
    total_samples_baseline: int = Field(..., ge=0, description="Samples in baseline period")
    total_samples_detection: int = Field(..., ge=0, description="Samples in detection period")
    
    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations based on drift analysis"
    )
    affected_clusters: List[str] = Field(
        default_factory=list,
        description="Clusters showing significant drift"
    )
    
    # Metadata
    analysis_method: str = Field(..., description="Drift detection method used")
    confidence_level: float = Field(..., description="Statistical confidence level")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ClusterHealthRequest(BaseAPIModel):
    """Request model for checking cluster health.

    Attributes:
        cluster_ids: A list of specific cluster IDs to check (all if not specified).
        health_window_hours: The time window for the health assessment in hours.
        include_inactive: Whether to include inactive clusters in the results.
    """
    cluster_ids: Optional[List[str]] = Field(
        None,
        max_items=100,
        description="Specific clusters to check (all if not specified)"
    )
    health_window_hours: Optional[int] = Field(
        default=1,
        ge=1,
        le=168,
        description="Time window for health assessment"
    )
    include_inactive: bool = Field(
        default=False,
        description="Include inactive clusters in results"
    )


class ClusterHealthResponse(BaseAPIModel):
    """Response model for cluster health check.

    Attributes:
        cluster_health: The health status per cluster.
        overall_health: The overall federation health.
        active_clusters: The number of active clusters.
        total_clusters: The total number of clusters.
        health_score: The overall health score.
        issues: A list of identified health issues.
        generated_at: The timestamp when the health check was performed.
    """
    cluster_health: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Health status per cluster"
    )
    overall_health: str = Field(..., description="Overall federation health")
    active_clusters: int = Field(..., ge=0, description="Number of active clusters")
    total_clusters: int = Field(..., ge=0, description="Total number of clusters")
    health_score: float = Field(..., ge=0.0, le=1.0, description="Overall health score")
    issues: List[str] = Field(default_factory=list, description="Identified health issues")
    generated_at: datetime = Field(default_factory=datetime.utcnow)