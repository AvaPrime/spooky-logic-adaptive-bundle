from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from models.experiments import (
    ExperimentRecordRequest, ExperimentRecordResponse,
    ExperimentSummaryRequest, ExperimentSummaryResponse,
    ExperimentConfigRequest, ExperimentConfigResponse
)
from models.base import ErrorResponse, SuccessResponse

router = APIRouter(prefix="/experiments", tags=["experiments"])

# In-memory storage (replace with database in production)
EXPERIMENTS = []

@router.post("/record", response_model=ExperimentRecordResponse)
async def record_experiment(record: ExperimentRecordRequest):
    """Record an experiment result"""
    try:
        # Find or create experiment
        experiment = None
        for exp in EXPERIMENTS:
            if exp["name"] == record.experiment_name:
                experiment = exp
                break
        
        if not experiment:
            experiment = {
                "name": record.experiment_name,
                "description": record.description or "",
                "arms": [],
                "status": "running",
                "created_at": datetime.utcnow(),
                "results": []
            }
            EXPERIMENTS.append(experiment)
        
        # Record the result
        result_data = {
            "arm": record.arm,
            "outcome": record.outcome,
            "metadata": record.metadata,
            "timestamp": datetime.utcnow(),
            "participant_id": record.participant_id
        }
        
        experiment["results"].append(result_data)
        
        # Update arms if new
        arm_names = [arm["name"] for arm in experiment["arms"]]
        if record.arm not in arm_names:
            experiment["arms"].append({
                "name": record.arm,
                "traffic_allocation": 0.5,  # Default allocation
                "config": {}
            })
        
        return ExperimentRecordResponse(
            record_id=f"rec-{len(experiment['results'])}",
            experiment_name=record.experiment_name,
            status="recorded",
            message="Experiment result recorded successfully",
            arm=record.arm,
            outcome=record.outcome,
            timestamp=result_data["timestamp"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{experiment_name}", response_model=ExperimentSummaryResponse)
async def get_results(experiment_name: str):
    """Get results for a specific experiment"""
    try:
        experiment = None
        for exp in EXPERIMENTS:
            if exp["name"] == experiment_name:
                experiment = exp
                break
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Calculate basic statistics
        arm_stats = {}
        for result in experiment["results"]:
            arm = result["arm"]
            if arm not in arm_stats:
                arm_stats[arm] = {"outcomes": [], "count": 0}
            arm_stats[arm]["outcomes"].append(result["outcome"])
            arm_stats[arm]["count"] += 1
        
        # Calculate means and confidence intervals
        for arm, stats in arm_stats.items():
            outcomes = stats["outcomes"]
            stats["mean"] = sum(outcomes) / len(outcomes) if outcomes else 0
            stats["variance"] = sum((x - stats["mean"]) ** 2 for x in outcomes) / len(outcomes) if len(outcomes) > 1 else 0
            stats["std_dev"] = stats["variance"] ** 0.5
        
        return ExperimentSummaryResponse(
            experiment_name=experiment_name,
            status=experiment["status"],
            total_participants=len(experiment["results"]),
            arms=experiment["arms"],
            results=experiment["results"],
            statistics=arm_stats,
            created_at=experiment["created_at"],
            last_updated=max([r["timestamp"] for r in experiment["results"]], default=experiment["created_at"])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=ExperimentConfigResponse)
async def analyze_experiment(analysis: ExperimentConfigRequest):
    """Perform statistical analysis on experiment results"""
    try:
        experiment = None
        for exp in EXPERIMENTS:
            if exp["name"] == analysis.experiment_name:
                experiment = exp
                break
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Simple statistical analysis
        arm_data = {}
        for result in experiment["results"]:
            arm = result["arm"]
            if arm not in arm_data:
                arm_data[arm] = []
            arm_data[arm].append(result["outcome"])
        
        # Calculate significance (simplified)
        significance_results = {}
        arms = list(arm_data.keys())
        
        for i, arm1 in enumerate(arms):
            for arm2 in arms[i+1:]:
                data1 = arm_data[arm1]
                data2 = arm_data[arm2]
                
                if len(data1) > 1 and len(data2) > 1:
                    mean1 = sum(data1) / len(data1)
                    mean2 = sum(data2) / len(data2)
                    
                    # Simplified t-test approximation
                    var1 = sum((x - mean1) ** 2 for x in data1) / (len(data1) - 1)
                    var2 = sum((x - mean2) ** 2 for x in data2) / (len(data2) - 1)
                    
                    pooled_se = ((var1 / len(data1)) + (var2 / len(data2))) ** 0.5
                    t_stat = abs(mean1 - mean2) / pooled_se if pooled_se > 0 else 0
                    
                    # Rough p-value approximation
                    p_value = max(0.001, min(0.999, 2 * (1 - min(0.999, t_stat / 3))))
                    
                    significance_results[f"{arm1}_vs_{arm2}"] = {
                        "t_statistic": t_stat,
                        "p_value": p_value,
                        "significant": p_value < analysis.significance_level,
                        "effect_size": abs(mean1 - mean2)
                    }
        
        return ExperimentConfigResponse(
            experiment_name=analysis.experiment_name,
            analysis_type=analysis.analysis_type,
            significance_level=analysis.significance_level,
            statistical_power=0.8,  # Default assumption
            sample_size=len(experiment["results"]),
            significance_results=significance_results,
            recommendations=[
                "Continue experiment if not statistically significant",
                "Consider increasing sample size for better power",
                "Monitor for practical significance beyond statistical significance"
            ],
            confidence_intervals={arm: {"lower": min(data), "upper": max(data)} for arm, data in arm_data.items()},
            effect_sizes={arm: sum(data) / len(data) for arm, data in arm_data.items()}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
