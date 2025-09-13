from fastapi import APIRouter, HTTPException
from models.rollback import (
    AutoRollbackStartRequest as RollbackStartRequest, 
    AutoRollbackStartResponse as RollbackStartResponse,
    RollbackStatusRequest, RollbackStatusResponse,
    RollbackControlRequest as RollbackExecuteRequest, 
    RollbackControlResponse as RollbackExecuteResponse
)
from models.base import ErrorResponse
from datetime import datetime
import uuid

router = APIRouter(prefix="/rollback", tags=["rollback"])

# In-memory storage for rollback plans
ROLLBACK_PLANS = {}

@router.post("/start", response_model=RollbackStartResponse)
async def start_rollback(request: RollbackStartRequest):
    """Start a rollback plan for a capability.

    This endpoint initiates a rollback plan for a specified capability. It
    generates a unique plan ID and creates a series of stages for the rollback
    process.

    Args:
        request (RollbackStartRequest): The request body containing the details
            of the rollback to start.

    Returns:
        RollbackStartResponse: The response containing the details of the started
            rollback plan.
    """
    try:
        # Generate rollback plan ID
        plan_id = str(uuid.uuid4())
        
        # Create rollback stages based on capability type
        stages = [
            "backup_current_state",
            "disable_capability",
            "restore_previous_version",
            "verify_rollback",
            "cleanup_resources"
        ]
        
        # Store rollback plan
        rollback_plan = {
            "plan_id": plan_id,
            "capability_id": request.capability_id,
            "reason": request.reason,
            "stages": stages,
            "current_stage": 0,
            "status": "active",
            "created_at": datetime.utcnow(),
            "interval_sec": request.interval_sec,
            "auto_execute": request.auto_execute,
            "backup_retention_hours": request.backup_retention_hours
        }
        
        ROLLBACK_PLANS[plan_id] = rollback_plan
        
        return RollbackStartResponse(
            plan_id=plan_id,
            capability_id=request.capability_id,
            status="started",
            stages=stages,
            current_stage=stages[0],
            interval_sec=request.interval_sec,
            auto_execute=request.auto_execute,
            estimated_duration_minutes=len(stages) * (request.interval_sec / 60),
            created_at=rollback_plan["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/status", response_model=RollbackStatusResponse)
async def get_rollback_status(request: RollbackStatusRequest):
    """Get the status of a rollback plan.

    This endpoint returns the current status of a rollback plan, including its
    progress and current stage.

    Args:
        request (RollbackStatusRequest): The request body containing the plan ID
            or capability ID to query.

    Returns:
        RollbackStatusResponse: The response containing the status of the
            rollback plan.
    """
    try:
        # Find rollback plan
        rollback_plan = None
        
        if request.plan_id:
            rollback_plan = ROLLBACK_PLANS.get(request.plan_id)
        elif request.capability_id:
            # Find by capability ID (get most recent)
            for plan_id, plan in ROLLBACK_PLANS.items():
                if plan["capability_id"] == request.capability_id:
                    if not rollback_plan or plan["created_at"] > rollback_plan["created_at"]:
                        rollback_plan = plan
        
        if not rollback_plan:
            raise HTTPException(status_code=404, detail="Rollback plan not found")
        
        # Calculate progress
        current_stage_index = rollback_plan["current_stage"]
        total_stages = len(rollback_plan["stages"])
        progress_percentage = (current_stage_index / total_stages) * 100 if total_stages > 0 else 0
        
        # Determine if rollback is active
        is_active = rollback_plan["status"] in ["active", "running"]
        
        return RollbackStatusResponse(
            plan_id=rollback_plan["plan_id"],
            capability_id=rollback_plan["capability_id"],
            status=rollback_plan["status"],
            current_stage=rollback_plan["stages"][current_stage_index] if current_stage_index < len(rollback_plan["stages"]) else "completed",
            total_stages=total_stages,
            completed_stages=current_stage_index,
            progress_percentage=progress_percentage,
            is_active=is_active,
            created_at=rollback_plan["created_at"],
            last_updated=rollback_plan.get("last_updated", rollback_plan["created_at"]),
            estimated_completion=None  # Could calculate based on interval and remaining stages
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=RollbackExecuteResponse)
async def execute_rollback_step(request: RollbackExecuteRequest):
    """Execute the next step in a rollback plan.

    This endpoint executes the next stage of an active rollback plan.

    Args:
        request (RollbackExecuteRequest): The request body containing the plan ID
            to execute.

    Returns:
        RollbackExecuteResponse: The response containing the result of the
            execution.
    """
    try:
        rollback_plan = ROLLBACK_PLANS.get(request.plan_id)
        if not rollback_plan:
            raise HTTPException(status_code=404, detail="Rollback plan not found")
        
        if rollback_plan["status"] not in ["active", "running"]:
            raise HTTPException(status_code=400, detail="Rollback plan is not active")
        
        # Execute current stage
        current_stage_index = rollback_plan["current_stage"]
        stages = rollback_plan["stages"]
        
        if current_stage_index >= len(stages):
            raise HTTPException(status_code=400, detail="Rollback plan already completed")
        
        current_stage = stages[current_stage_index]
        
        # Simulate stage execution
        execution_result = {
            "stage": current_stage,
            "status": "completed",
            "message": f"Successfully executed {current_stage}",
            "executed_at": datetime.utcnow()
        }
        
        # Update rollback plan
        rollback_plan["current_stage"] += 1
        rollback_plan["last_updated"] = datetime.utcnow()
        
        # Check if rollback is complete
        if rollback_plan["current_stage"] >= len(stages):
            rollback_plan["status"] = "completed"
        
        # Determine next stage
        next_stage = None
        if rollback_plan["current_stage"] < len(stages):
            next_stage = stages[rollback_plan["current_stage"]]
        
        return RollbackExecuteResponse(
            plan_id=request.plan_id,
            executed_stage=current_stage,
            execution_status="success",
            next_stage=next_stage,
            rollback_completed=rollback_plan["status"] == "completed",
            message=execution_result["message"],
            executed_at=execution_result["executed_at"],
            rollback_details={
                "capability_id": rollback_plan["capability_id"],
                "total_stages": len(stages),
                "completed_stages": rollback_plan["current_stage"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
