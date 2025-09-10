"""Database persistence layer for governance data with CRDT compatibility."""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
import time
import asyncio
from datetime import datetime, timedelta
import logging
import json
from contextlib import asynccontextmanager
from dataclasses import asdict

from .models import Base, GovernanceProposal, GovernanceVote, PolicyExecution, PolicyRule

logger = logging.getLogger(__name__)

class DatabaseLWWMap:
    """Database-backed Last-Write-Wins Map that maintains CRDT semantics."""
    
    def __init__(self, session: AsyncSession, model_class, key_field: str = 'id'):
        self.session = session
        self.model_class = model_class
        self.key_field = key_field
        self._cache = {}  # In-memory cache for performance
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update = 0
    
    async def put(self, key: str, value: Any, ts: Optional[float] = None):
        """Store a value with timestamp, following LWW semantics."""
        ts = ts or time.time()
        
        try:
            # Check if record exists
            stmt = select(self.model_class).where(getattr(self.model_class, self.key_field) == key)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Only update if timestamp is newer (LWW semantics)
                if ts > existing.crdt_timestamp:
                    if isinstance(value, dict):
                        # Update from dictionary
                        for attr, val in value.items():
                            if hasattr(existing, attr) and attr != self.key_field:
                                setattr(existing, attr, val)
                        existing.crdt_timestamp = ts
                    else:
                        # Direct value update (for simple cases)
                        existing.crdt_timestamp = ts
                    
                    await self.session.commit()
            else:
                # Create new record
                if isinstance(value, dict):
                    # Create from dictionary
                    value['ts'] = ts
                    new_record = self.model_class.from_dict({self.key_field: key, **value})
                else:
                    # Create with direct value
                    new_record = self.model_class(**{self.key_field: key, 'crdt_timestamp': ts})
                
                self.session.add(new_record)
                await self.session.commit()
            
            # Update cache
            self._cache[key] = (value, ts)
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to store {key}: {e}")
            raise
    
    async def get(self, key: str, default=None):
        """Get a value by key."""
        # Check cache first
        if key in self._cache and time.time() - self._last_cache_update < self._cache_ttl:
            return self._cache[key][0]
        
        # Query database
        stmt = select(self.model_class).where(getattr(self.model_class, self.key_field) == key)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            value = record.to_dict()
            self._cache[key] = (value, record.crdt_timestamp)
            return value
        
        return default
    
    async def merge(self, other: 'DatabaseLWWMap'):
        """Merge another LWWMap into this one."""
        # Get all records from other map
        other_data = await other.to_dict()
        
        for key, value in other_data.items():
            # Get timestamp from other map
            other_record = await other.get(key)
            if other_record and 'ts' in other_record:
                await self.put(key, value, other_record['ts'])
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        stmt = select(self.model_class)
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        
        data = {}
        for record in records:
            key = getattr(record, self.key_field)
            data[key] = record.to_dict()
        
        return data
    
    async def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
        self._last_cache_update = 0

class DatabaseGovernanceState:
    """Database-backed governance state that maintains CRDT interface."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.proposals = DatabaseLWWMap(session, GovernanceProposal, 'id')
        self.votes = DatabaseLWWMap(session, GovernanceVote, 'id')
    
    async def apply_proposal(self, proposal: Dict[str, Any]):
        """Apply a proposal to the governance state."""
        pid = str(proposal["id"])
        ts = proposal.get("ts", time.time())
        await self.proposals.put(pid, proposal, ts)
    
    async def apply_vote(self, vote: Dict[str, Any]):
        """Apply a vote to the governance state."""
        key = f"{vote['proposal_id']}:{vote['voter']}"
        ts = vote.get("ts", time.time())
        await self.votes.put(key, vote, ts)
    
    async def merge(self, other: 'DatabaseGovernanceState'):
        """Merge another governance state into this one."""
        await self.proposals.merge(other.proposals)
        await self.votes.merge(other.votes)
    
    async def serialize(self) -> Dict[str, Any]:
        """Serialize to dictionary format."""
        proposals_data = await self.proposals.to_dict()
        votes_data = await self.votes.to_dict()
        
        return {
            "proposals": proposals_data,
            "votes": votes_data
        }
    
    @classmethod
    async def deserialize(cls, session: AsyncSession, data: Dict[str, Any]) -> 'DatabaseGovernanceState':
        """Deserialize from dictionary format."""
        state = cls(session)
        
        # Load proposals
        for pid, proposal in data.get("proposals", {}).items():
            await state.apply_proposal(proposal)
        
        # Load votes
        for vote_key, vote in data.get("votes", {}).items():
            await state.apply_vote(vote)
        
        return state
    
    async def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific proposal."""
        return await self.proposals.get(proposal_id)
    
    async def get_votes_for_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get all votes for a specific proposal."""
        stmt = select(GovernanceVote).where(GovernanceVote.proposal_id == proposal_id)
        result = await self.session.execute(stmt)
        votes = result.scalars().all()
        
        return [vote.to_dict() for vote in votes]
    
    async def get_active_proposals(self) -> List[Dict[str, Any]]:
        """Get all active (non-expired) proposals."""
        now = datetime.utcnow()
        stmt = select(GovernanceProposal).where(
            (GovernanceProposal.expires_at.is_(None)) | 
            (GovernanceProposal.expires_at > now)
        ).where(GovernanceProposal.status == 'pending')
        
        result = await self.session.execute(stmt)
        proposals = result.scalars().all()
        
        return [proposal.to_dict() for proposal in proposals]

class PolicyPersistence:
    """Database persistence for policy engine data."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def store_policy_rule(self, rule):
        """Store a policy rule in the database."""
        from .models import PolicyRule as DBPolicyRule
        
        # Convert PolicyRule to database model
        db_rule = DBPolicyRule(
            name=rule.name,
            trigger=rule.trigger.value,
            conditions=json.dumps([asdict(c) for c in rule.conditions]),
            action=rule.action.value,
            parameters=json.dumps(rule.parameters),
            priority=rule.priority,
            cooldown_minutes=rule.cooldown_minutes,
            max_executions_per_day=rule.max_executions_per_day,
            confidence_threshold=rule.confidence_threshold
        )
        
        async with self.db_manager.get_session() as session:
            # Check if rule already exists
            existing = await session.execute(
                select(DBPolicyRule).where(DBPolicyRule.name == rule.name)
            )
            existing_rule = existing.scalar_one_or_none()
            
            if existing_rule:
                # Update existing rule
                existing_rule.trigger = db_rule.trigger
                existing_rule.conditions = db_rule.conditions
                existing_rule.action = db_rule.action
                existing_rule.parameters = db_rule.parameters
                existing_rule.priority = db_rule.priority
                existing_rule.cooldown_minutes = db_rule.cooldown_minutes
                existing_rule.max_executions_per_day = db_rule.max_executions_per_day
                existing_rule.confidence_threshold = db_rule.confidence_threshold
                existing_rule.updated_at = datetime.utcnow()
            else:
                # Insert new rule
                session.add(db_rule)
            await session.commit()
    
    async def get_policy_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get a policy rule by name."""
        async with self.db_manager.get_session() as session:
            stmt = select(PolicyRule).where(PolicyRule.name == rule_name)
            result = await session.execute(stmt)
            rule = result.scalar_one_or_none()
            
            return rule.to_dict() if rule else None
    
    async def get_policy_rules(self):
        """Retrieve all policy rules from database."""
        from ..policy_engine import PolicyRule as EngineRule, PolicyTrigger, AdaptationAction, PolicyCondition
        from .models import PolicyRule as DBPolicyRule
        
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(DBPolicyRule))
            db_rules = result.scalars().all()
            
            # Convert database models back to engine objects
            engine_rules = []
            for db_rule in db_rules:
                # Parse conditions from JSON
                conditions_data = json.loads(db_rule.conditions)
                conditions = [PolicyCondition(**cond) for cond in conditions_data]
                
                engine_rule = EngineRule(
                    name=db_rule.name,
                    trigger=PolicyTrigger(db_rule.trigger),
                    conditions=conditions,
                    action=AdaptationAction(db_rule.action),
                    parameters=json.loads(db_rule.parameters),
                    priority=db_rule.priority,
                    cooldown_minutes=db_rule.cooldown_minutes,
                    max_executions_per_day=db_rule.max_executions_per_day,
                    confidence_threshold=db_rule.confidence_threshold
                )
                engine_rules.append(engine_rule)
            
            return engine_rules
    
    async def get_all_policy_rules(self) -> List[Dict[str, Any]]:
        """Get all enabled policy rules."""
        async with self.db_manager.get_session() as session:
            stmt = select(PolicyRule).where(PolicyRule.enabled == True)
            result = await session.execute(stmt)
            rules = result.scalars().all()
            
            return [rule.to_dict() for rule in rules]
    
    async def record_policy_execution(self, rule_name: str, outcome: Dict[str, Any], 
                                     success: bool, improvement_score: float):
        """Record a policy execution."""
        execution = PolicyExecution(
            rule_name=rule_name,
            outcome=outcome,
            success=success,
            improvement_score=improvement_score
        )
        
        async with self.db_manager.get_session() as session:
            session.add(execution)
            await session.commit()
            
            # Update rule execution stats
            await self._update_rule_stats(session, rule_name, success)
    
    async def _update_rule_stats(self, session: AsyncSession, rule_name: str, success: bool):
        """Update rule execution statistics."""
        stmt = select(PolicyRule).where(PolicyRule.name == rule_name)
        result = await session.execute(stmt)
        rule = result.scalar_one_or_none()
        
        if rule:
            # Reset daily count if it's a new day
            today = datetime.utcnow().date()
            if rule.last_executed and rule.last_executed.date() != today:
                rule.execution_count_today = 0
            
            rule.execution_count_today += 1
            rule.last_executed = datetime.utcnow()
            
            # Update success rate (simple moving average)
            if success:
                rule.success_rate = min(1.0, rule.success_rate + 0.1)
            else:
                rule.success_rate = max(0.0, rule.success_rate - 0.1)
            
            await session.commit()
    
    async def get_execution_history(self, rule_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history for a rule."""
        async with self.db_manager.get_session() as session:
            stmt = select(PolicyExecution).where(
                PolicyExecution.rule_name == rule_name
            ).order_by(PolicyExecution.created_at.desc()).limit(limit)
            
            result = await session.execute(stmt)
            executions = result.scalars().all()
            
            return [execution.to_dict() for execution in executions]

class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_tables(self):
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        return self.async_session()
    
    async def close(self):
        """Close the database connection."""
        await self.engine.dispose()