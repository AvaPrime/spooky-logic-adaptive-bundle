"""Configuration for governance and policy engine with database persistence"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Database configuration for governance persistence"""
    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

@dataclass
class GovernanceConfig:
    """Configuration for governance system"""
    # Database settings
    database: Optional[DatabaseConfig] = None
    
    # Legacy in-memory mode (for backward compatibility)
    use_memory_storage: bool = False
    
    # Policy engine settings
    policy_config_path: str = "config/policies.yaml"
    enable_policy_learning: bool = True
    
    # CRDT settings for distributed governance
    enable_crdt_sync: bool = True
    sync_interval_seconds: int = 30
    
    # Audit and logging
    enable_audit_logging: bool = True
    audit_log_level: str = "INFO"

def get_governance_config() -> GovernanceConfig:
    """Get governance configuration from environment variables"""
    
    # Database configuration
    db_url = os.getenv("GOVERNANCE_DB_URL")
    if db_url:
        database_config = DatabaseConfig(
            url=db_url,
            echo=os.getenv("GOVERNANCE_DB_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("GOVERNANCE_DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("GOVERNANCE_DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("GOVERNANCE_DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("GOVERNANCE_DB_POOL_RECYCLE", "3600"))
        )
    else:
        database_config = None
    
    return GovernanceConfig(
        database=database_config,
        use_memory_storage=os.getenv("GOVERNANCE_USE_MEMORY", "false").lower() == "true",
        policy_config_path=os.getenv("GOVERNANCE_POLICY_CONFIG", "config/policies.yaml"),
        enable_policy_learning=os.getenv("GOVERNANCE_ENABLE_LEARNING", "true").lower() == "true",
        enable_crdt_sync=os.getenv("GOVERNANCE_ENABLE_CRDT", "true").lower() == "true",
        sync_interval_seconds=int(os.getenv("GOVERNANCE_SYNC_INTERVAL", "30")),
        enable_audit_logging=os.getenv("GOVERNANCE_ENABLE_AUDIT", "true").lower() == "true",
        audit_log_level=os.getenv("GOVERNANCE_AUDIT_LEVEL", "INFO")
    )

# Example configurations for different environments

DEVELOPMENT_CONFIG = GovernanceConfig(
    database=DatabaseConfig(
        url="sqlite+aiosqlite:///./governance_dev.db",
        echo=True
    ),
    use_memory_storage=False,
    enable_policy_learning=True,
    enable_crdt_sync=False,  # Disable for single-node development
    enable_audit_logging=True
)

PRODUCTION_CONFIG = GovernanceConfig(
    database=DatabaseConfig(
        url="postgresql+asyncpg://user:pass@localhost/governance",
        echo=False,
        pool_size=20,
        max_overflow=40
    ),
    use_memory_storage=False,
    enable_policy_learning=True,
    enable_crdt_sync=True,
    sync_interval_seconds=15,  # More frequent sync in production
    enable_audit_logging=True
)

TEST_CONFIG = GovernanceConfig(
    database=DatabaseConfig(
        url="sqlite+aiosqlite:///:memory:",
        echo=False
    ),
    use_memory_storage=False,
    enable_policy_learning=False,  # Disable learning in tests
    enable_crdt_sync=False,
    enable_audit_logging=False
)

# Legacy in-memory configuration (for backward compatibility)
LEGACY_CONFIG = GovernanceConfig(
    database=None,
    use_memory_storage=True,
    enable_policy_learning=True,
    enable_crdt_sync=True,
    enable_audit_logging=True
)