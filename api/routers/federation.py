from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime
from models.federation import (
    FederatedSampleRequest, FederatedSampleResponse,
    FederatedSummaryRequest, FederatedSummaryResponse,
    DriftDetectionRequest, DriftDetectionResponse,
    ClusterHealthRequest, ClusterHealthResponse
)
from models.base import ErrorResponse, SuccessResponse

router = APIRouter(prefix="/federation", tags=["federation"])

# In-memory storage (replace with database in production)
CLUSTERS = {}
SAMPLES = []

@router.post("/sample", response_model=FederatedSampleResponse)
async def submit_sample(request: FederatedSampleRequest):
    """Submit a federated learning sample.

    This endpoint allows a client to submit a sample for federated learning.
    The sample is associated with a cluster, and the cluster's statistics
    are updated.

    Args:
        request (FederatedSampleRequest): The request body containing the federated
            learning sample.

    Returns:
        FederatedSampleResponse: The response containing the status of the sample
            submission.
    """
    try:
        # Initialize cluster if not exists
        if request.cluster_id not in CLUSTERS:
            CLUSTERS[request.cluster_id] = {
                "id": request.cluster_id,
                "status": "active",
                "created_at": datetime.utcnow(),
                "last_update": datetime.utcnow(),
                "sample_count": 0,
                "participants": set()
            }
        
        cluster = CLUSTERS[request.cluster_id]
        
        # Add sample
        sample_data = {
            "sample_id": f"sample-{len(SAMPLES) + 1}",
            "cluster_id": request.cluster_id,
            "features": request.features,
            "metadata": request.metadata,
            "timestamp": datetime.utcnow(),
            "participant_id": request.metadata.get("participant_id", "unknown")
        }
        
        SAMPLES.append(sample_data)
        
        # Update cluster stats
        cluster["sample_count"] += 1
        cluster["last_update"] = datetime.utcnow()
        cluster["participants"].add(sample_data["participant_id"])
        
        return FederatedSampleResponse(
            sample_id=sample_data["sample_id"],
            cluster_id=request.cluster_id,
            status="accepted",
            message="Sample successfully submitted to federated learning",
            timestamp=sample_data["timestamp"],
            cluster_sample_count=cluster["sample_count"],
            participant_count=len(cluster["participants"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary", response_model=FederatedSummaryResponse)
async def get_federated_summary(request: FederatedSummaryRequest):
    """Get federated learning summary for a cluster.

    This endpoint returns a summary of the federated learning process for a
    given cluster, including aggregated features and convergence metrics.

    Args:
        request (FederatedSummaryRequest): The request body containing the cluster
            ID and aggregation method.

    Returns:
        FederatedSummaryResponse: The response containing the federated learning
            summary.
    """
    try:
        if request.cluster_id not in CLUSTERS:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        cluster = CLUSTERS[request.cluster_id]
        cluster_samples = [s for s in SAMPLES if s["cluster_id"] == request.cluster_id]
        
        if not cluster_samples:
            raise HTTPException(status_code=404, detail="No samples found for cluster")
        
        # Calculate aggregated features
        all_features = [s["features"] for s in cluster_samples]
        if not all_features:
            aggregated_features = []
        else:
            feature_count = len(all_features[0])
            aggregated_features = []
            
            for i in range(feature_count):
                feature_values = [features[i] for features in all_features if i < len(features)]
                if request.aggregation_method == "mean":
                    aggregated_features.append(sum(feature_values) / len(feature_values))
                elif request.aggregation_method == "median":
                    sorted_values = sorted(feature_values)
                    n = len(sorted_values)
                    if n % 2 == 0:
                        aggregated_features.append((sorted_values[n//2-1] + sorted_values[n//2]) / 2)
                    else:
                        aggregated_features.append(sorted_values[n//2])
                else:  # sum
                    aggregated_features.append(sum(feature_values))
        
        # Calculate convergence metrics
        convergence_metrics = {
            "rounds_completed": len(cluster_samples),
            "convergence_rate": min(1.0, len(cluster_samples) / 100),  # Simplified
            "stability_score": 0.85,  # Mock value
            "participant_consistency": len(cluster["participants"]) / max(1, cluster["sample_count"])
        }
        
        return FederatedSummaryResponse(
            cluster_id=request.cluster_id,
            aggregation_method=request.aggregation_method,
            total_samples=len(cluster_samples),
            participant_count=len(cluster["participants"]),
            aggregated_features=aggregated_features,
            convergence_metrics=convergence_metrics,
            last_updated=cluster["last_update"],
            summary_timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drift-detection", response_model=DriftDetectionResponse)
async def detect_drift(request: DriftDetectionRequest):
    """Detect data drift in federated learning.

    This endpoint detects data drift in a federated learning cluster by
    comparing recent samples to older samples.

    Args:
        request (DriftDetectionRequest): The request body containing the cluster
            ID and drift detection parameters.

    Returns:
        DriftDetectionResponse: The response containing the drift detection
            results.
    """
    try:
        if request.cluster_id not in CLUSTERS:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        cluster_samples = [s for s in SAMPLES if s["cluster_id"] == request.cluster_id]
        
        if len(cluster_samples) < 2:
            return DriftDetectionResponse(
                cluster_id=request.cluster_id,
                drift_detected=False,
                drift_severity="none",
                drift_score=0.0,
                affected_features=[],
                detection_timestamp=datetime.utcnow(),
                recommendations=["Collect more samples for drift detection"]
            )
        
        # Simple drift detection based on feature variance
        recent_samples = cluster_samples[-10:]  # Last 10 samples
        older_samples = cluster_samples[:-10] if len(cluster_samples) > 10 else []
        
        drift_detected = False
        drift_score = 0.0
        affected_features = []
        
        if older_samples:
            # Compare feature distributions
            for i in range(len(recent_samples[0]["features"])):
                recent_values = [s["features"][i] for s in recent_samples if i < len(s["features"])]
                older_values = [s["features"][i] for s in older_samples if i < len(s["features"])]
                
                if recent_values and older_values:
                    recent_mean = sum(recent_values) / len(recent_values)
                    older_mean = sum(older_values) / len(older_values)
                    
                    # Simple drift score based on mean difference
                    feature_drift = abs(recent_mean - older_mean) / (abs(older_mean) + 1e-6)
                    
                    if feature_drift > request.threshold:
                        drift_detected = True
                        affected_features.append(i)
                        drift_score = max(drift_score, feature_drift)
        
        # Determine severity
        if drift_score > 0.5:
            severity = "high"
        elif drift_score > 0.2:
            severity = "medium"
        elif drift_score > 0.1:
            severity = "low"
        else:
            severity = "none"
        
        recommendations = []
        if drift_detected:
            recommendations.extend([
                "Consider retraining the federated model",
                "Investigate data quality in affected participants",
                "Implement adaptive learning rates"
            ])
        else:
            recommendations.append("No immediate action required")
        
        return DriftDetectionResponse(
            cluster_id=request.cluster_id,
            drift_detected=drift_detected,
            drift_severity=severity,
            drift_score=drift_score,
            affected_features=affected_features,
            detection_timestamp=datetime.utcnow(),
            recommendations=recommendations
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/health", response_model=ClusterHealthResponse)
async def check_cluster_health(request: ClusterHealthRequest):
    """Check the health of a federated learning cluster.

    This endpoint checks the health of a federated learning cluster by
    examining its activity and participation rate.

    Args:
        request (ClusterHealthRequest): The request body containing the cluster
            ID to check.

    Returns:
        ClusterHealthResponse: The response containing the cluster health status.
    """
    try:
        if request.cluster_id not in CLUSTERS:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        cluster = CLUSTERS[request.cluster_id]
        cluster_samples = [s for s in SAMPLES if s["cluster_id"] == request.cluster_id]
        
        # Calculate health metrics
        current_time = datetime.utcnow()
        time_since_update = (current_time - cluster["last_update"]).total_seconds()
        
        # Determine cluster status
        if time_since_update > 3600:  # 1 hour
            status = "inactive"
        elif len(cluster["participants"]) < 2:
            status = "insufficient_participants"
        elif cluster["sample_count"] < 10:
            status = "warming_up"
        else:
            status = "healthy"
        
        # Calculate participation rate
        recent_samples = [s for s in cluster_samples if (current_time - s["timestamp"]).total_seconds() < 3600]
        participation_rate = len(set(s["participant_id"] for s in recent_samples)) / max(1, len(cluster["participants"]))
        
        health_metrics = {
            "uptime_hours": (current_time - cluster["created_at"]).total_seconds() / 3600,
            "participation_rate": participation_rate,
            "sample_frequency": len(recent_samples) / max(1, time_since_update / 3600),
            "data_quality_score": 0.9,  # Mock value
            "network_stability": 0.95  # Mock value
        }
        
        return ClusterHealthResponse(
            cluster_id=request.cluster_id,
            status=status,
            participant_count=len(cluster["participants"]),
            active_participants=len(set(s["participant_id"] for s in recent_samples)),
            total_samples=cluster["sample_count"],
            last_activity=cluster["last_update"],
            health_metrics=health_metrics,
            health_timestamp=current_time
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
