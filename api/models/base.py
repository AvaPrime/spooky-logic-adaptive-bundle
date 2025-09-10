"""Base Pydantic models and validators for API input validation."""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
import re


class BaseAPIModel(BaseModel):
    """Base model with common configuration."""
    
    class Config:
        # Allow extra fields but validate known ones
        extra = "forbid"
        # Use enum values instead of names
        use_enum_values = True
        # Validate assignment
        validate_assignment = True


class TimestampedModel(BaseAPIModel):
    """Model with automatic timestamp tracking."""
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class TenantModel(BaseAPIModel):
    """Model with tenant validation."""
    tenant: str = Field(..., min_length=1, max_length=100, description="Tenant identifier")
    
    @validator('tenant')
    def validate_tenant(cls, v):
        if not re.match(pattern=r'^[a-zA-Z0-9_-]+$', string=v):
            raise ValueError('Tenant must contain only alphanumeric characters, hyphens, and underscores')
        return v


class CapabilityModel(BaseAPIModel):
    """Model with capability ID validation."""
    capability_id: str = Field(..., min_length=1, max_length=200, description="Capability identifier")
    
    @validator('capability_id')
    def validate_capability_id(cls, v):
        if not re.match(pattern=r'^[a-zA-Z0-9._-]+$', string=v):
            raise ValueError('Capability ID must contain only alphanumeric characters, dots, hyphens, and underscores')
        return v


class MetricsModel(BaseAPIModel):
    """Model with common metrics validation."""
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    cost: float = Field(..., ge=0.0, description="Cost in USD")
    latency_ms: float = Field(..., ge=0.0, description="Latency in milliseconds")


class PaginationModel(BaseAPIModel):
    """Model for pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    

class ErrorResponse(BaseAPIModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseAPIModel):
    """Standard success response model."""
    ok: bool = Field(True, description="Success indicator")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)