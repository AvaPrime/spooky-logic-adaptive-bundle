"""Database models for governance data persistence."""

from sqlalchemy import Column, String, Text, Float, Integer, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional
import json

Base = declarative_base()

class GovernanceProposal(Base):
    """Database model for governance proposals.

    This class defines the database schema for storing governance proposals.
    It includes fields for the proposal's title, description, proposer, type,
    status, and other metadata. It also includes a CRDT timestamp for conflict
    resolution in a distributed environment.
    """
    __tablename__ = 'governance_proposals'
    
    id = Column(String(255), primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    proposer = Column(String(255), nullable=False)
    proposal_type = Column(String(100), nullable=False)
    status = Column(String(50), default='pending')
    data = Column(JSON)  # Store proposal-specific data
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)
    
    # CRDT timestamp for conflict resolution
    crdt_timestamp = Column(Float, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the proposal to a dictionary.

        This method is used for CRDT compatibility, as it includes the CRDT
        timestamp in the dictionary representation.

        Returns:
            A dictionary representation of the proposal.
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'proposer': self.proposer,
            'proposal_type': self.proposal_type,
            'status': self.status,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'ts': self.crdt_timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GovernanceProposal':
        """Creates a proposal instance from a dictionary.

        Args:
            data: The dictionary to create the proposal from.

        Returns:
            A new instance of the GovernanceProposal class.
        """
        return cls(
            id=data['id'],
            title=data.get('title', ''),
            description=data.get('description'),
            proposer=data.get('proposer', ''),
            proposal_type=data.get('proposal_type', 'general'),
            status=data.get('status', 'pending'),
            data=data.get('data'),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            crdt_timestamp=data.get('ts', datetime.utcnow().timestamp())
        )

class GovernanceVote(Base):
    """Database model for governance votes.

    This class defines the database schema for storing governance votes. It
    includes fields for the proposal ID, voter, vote, weight, and other
    metadata. It also includes a CRDT timestamp for conflict resolution.
    """
    __tablename__ = 'governance_votes'
    
    id = Column(String(255), primary_key=True)  # proposal_id:voter format
    proposal_id = Column(String(255), nullable=False, index=True)
    voter = Column(String(255), nullable=False)
    vote = Column(String(50), nullable=False)  # 'approve', 'reject', 'abstain'
    weight = Column(Float, default=1.0)
    reason = Column(Text)
    metadata = Column(JSON)  # Additional vote data
    created_at = Column(DateTime, default=func.now())
    
    # CRDT timestamp for conflict resolution
    crdt_timestamp = Column(Float, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the vote to a dictionary.

        This method is used for CRDT compatibility, as it includes the CRDT
        timestamp in the dictionary representation.

        Returns:
            A dictionary representation of the vote.
        """
        return {
            'proposal_id': self.proposal_id,
            'voter': self.voter,
            'vote': self.vote,
            'weight': self.weight,
            'reason': self.reason,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ts': self.crdt_timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GovernanceVote':
        """Creates a vote instance from a dictionary.

        Args:
            data: The dictionary to create the vote from.

        Returns:
            A new instance of the GovernanceVote class.
        """
        vote_id = f"{data['proposal_id']}:{data['voter']}"
        return cls(
            id=vote_id,
            proposal_id=data['proposal_id'],
            voter=data['voter'],
            vote=data['vote'],
            weight=data.get('weight', 1.0),
            reason=data.get('reason'),
            metadata=data.get('metadata'),
            crdt_timestamp=data.get('ts', datetime.utcnow().timestamp())
        )

class PolicyExecution(Base):
    """Database model for policy execution history.

    This class defines the database schema for storing the history of policy
    executions. It includes fields for the rule name, trigger, action,
    parameters, outcome, and other metadata.
    """
    __tablename__ = 'policy_executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(255), nullable=False, index=True)
    trigger = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    parameters = Column(JSON)
    outcome = Column(JSON)
    success = Column(Boolean, nullable=False)
    execution_time_ms = Column(Float)
    metrics_snapshot = Column(JSON)  # Metrics at time of execution
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the policy execution to a dictionary.

        Returns:
            A dictionary representation of the policy execution.
        """
        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'trigger': self.trigger,
            'action': self.action,
            'parameters': self.parameters,
            'outcome': self.outcome,
            'success': self.success,
            'execution_time_ms': self.execution_time_ms,
            'metrics_snapshot': self.metrics_snapshot,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PolicyRule(Base):
    """Database model for storing policy rules.

    This class defines the database schema for storing policy rules. It
    includes fields for the rule's name, trigger, conditions, action,
    parameters, and other metadata.
    """
    __tablename__ = 'policy_rules'
    
    name = Column(String(255), primary_key=True)
    trigger = Column(String(100), nullable=False)
    conditions = Column(JSON, nullable=False)
    action = Column(String(100), nullable=False)
    parameters = Column(JSON)
    priority = Column(Integer, default=5)
    cooldown_minutes = Column(Integer, default=60)
    max_executions_per_day = Column(Integer, default=10)
    confidence_threshold = Column(Float, default=0.7)
    
    # Execution tracking
    last_executed = Column(DateTime)
    execution_count_today = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    enabled = Column(Boolean, default=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the policy rule to a dictionary.

        Returns:
            A dictionary representation of the policy rule.
        """
        return {
            'name': self.name,
            'trigger': self.trigger,
            'conditions': self.conditions,
            'action': self.action,
            'parameters': self.parameters,
            'priority': self.priority,
            'cooldown_minutes': self.cooldown_minutes,
            'max_executions_per_day': self.max_executions_per_day,
            'confidence_threshold': self.confidence_threshold,
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'execution_count_today': self.execution_count_today,
            'success_rate': self.success_rate,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }