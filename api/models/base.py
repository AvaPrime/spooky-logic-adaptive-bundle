"""Base Pydantic models and validators for API input validation.

This module defines a set of base Pydantic models that provide common
functionality and validation for other models throughout the API.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
import re


class BaseAPIModel(BaseModel):
    """A base model with common configuration for all API models.

    This model sets up a common configuration for all other models in the API,
    including forbidding extra fields, using enum values, and validating on
    assignment.
    """
    
    class Config:
        """Pydantic configuration options."""
        # Forbid extra fields that are not defined in the model
        extra = "forbid"
        # Use the values of enums instead of their names
        use_enum_values = True
        # Validate fields on assignment
        validate_assignment = True


class TimestampedModel(BaseAPIModel):
    """A model with automatic timestamp tracking for creation and updates.

    Attributes:
        created_at: The timestamp when the record was created.
        updated_at: The timestamp when the record was last updated.
    """
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class TenantModel(BaseAPIModel):
    """A model with validation for a tenant identifier.

    Attributes:
        tenant: The identifier of the tenant.
    """
    tenant: str = Field(..., min_length=1, max_length=100, description="Tenant identifier")
    
    @validator('tenant')
    def validate_tenant(cls, v):
        """Validate the tenant identifier.

        Args:
            v: The tenant identifier string.

        Returns:
            The validated tenant identifier string.

        Raises:
            ValueError: If the tenant identifier contains invalid characters.
        """
        if not re.match(pattern=r'^[a-zA-Z0-9_-]+$', string=v):
            raise ValueError('Tenant must contain only alphanumeric characters, hyphens, and underscores')
        return v


class CapabilityModel(BaseAPIModel):
    """A model with validation for a capability identifier.

    Attributes:
        capability_id: The identifier of the capability.
    """
    capability_id: str = Field(..., min_length=1, max_length=200, description="Capability identifier")
    
    @validator('capability_id')
    def validate_capability_id(cls, v):
        """Validate the capability identifier.

        Args:
            v: The capability identifier string.

        Returns:
            The validated capability identifier string.

        Raises:
            ValueError: If the capability identifier contains invalid characters.
        """
        if not re.match(pattern=r'^[a-zA-Z0-9._-]+$', string=v):
            raise ValueError('Capability ID must contain only alphanumeric characters, dots, hyphens, and underscores')
        return v


class MetricsModel(BaseAPIModel):
    """A model with common metrics validation.

    Attributes:
        score: The score of the metric, between 0 and 1.
        cost: The cost of the metric in USD.
        latency_ms: The latency of the metric in milliseconds.
    """
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    cost: float = Field(..., ge=0.0, description="Cost in USD")
    latency_ms: float = Field(..., ge=0.0, description="Latency in milliseconds")


class PaginationModel(BaseAPIModel):
    """A model for pagination parameters.

    Attributes:
        page: The page number for pagination.
        size: The page size for pagination.
    """
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    

class ErrorResponse(BaseAPIModel):
    """A standard error response model.

    Attributes:
        error: The error message.
        code: The error code.
        details: Additional details about the error.
        timestamp: The timestamp of the error.
    """
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseAPIModel):
    """A standard success response model.

    Attributes:
        ok: A boolean indicating success.
        message: An optional success message.
        data: The response data.
        timestamp: The timestamp of the response.
    """
    ok: bool = Field(True, description="Success indicator")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)