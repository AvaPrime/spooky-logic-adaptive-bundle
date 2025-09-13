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
    """A database-backed Last-Write-Wins Map that maintains CRDT semantics.

    This class provides a dictionary-like interface for a database table that
    ishave Last-Write-Wins (LWW) semantics. This means that when there is a
    conflict, the value with the highest timestamp wins. This class also
    includes an in-memory cache for performance.
    """
    
    def __init__(self, session: AsyncSession, model_class, key_field: str = 'id'):
        """Initializes the DatabaseLWWMap.

        Args:
            session: The SQLAlchemy async session to use for database
                operations.
            model_class: The SQLAlchemy model class to use for the map.
            key_field: The name of the primary key field in the model.
        """
        self.session = session
        self.model_class = model_class
        self.key_field = key_field
        self._cache = {}  # In-memory cache for performance
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update = 0
    
    async def put(self, key: str, value: Any, ts: Optional[float] = None):
        """Stores a value with a timestamp, following LWW semantics.

        If the key already exists in the map, the value will only be updated if
        the new timestamp is greater than the existing timestamp.

        Args:
            key: The key to store the value under.
            value: The value to store.
            ts: The timestamp of the operation. If not provided, the current
                time is used.
        """
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
        """Gets a value by key.

        This method first checks the in-memory cache for the key. If the key is
        not in the cache or the cache has expired, it queries the database.

        Args:
            key: The key to get the value for.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if the key
            is not found.
        """
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
        """Merges another LWWMap into this one.

        Args:
            other: The other LWWMap to merge.
        """
        # Get all records from other map
        other_data = await other.to_dict()
        
        for key, value in other_data.items():
            # Get timestamp from other map
            other_record = await other.get(key)
            if other_record and 'ts' in other_record:
                await self.put(key, value, other_record['ts'])
    
    async def to_dict(self) -> Dict[str, Any]:
        """Converts the LWWMap to a dictionary.

        Returns:
            A dictionary representation of the LWWMap.
        """
        stmt = select(self.model_class)
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        
        data = {}
        for record in records:
            key = getattr(record, self.key_field)
            data[key] = record.to_dict()
        
        return data
    
    async def clear_cache(self):
        """Clears the in-memory cache."""
        self._cache.clear()
        self._last_cache_update = 0

class DatabaseGovernanceState:
    """A database-backed governance state that maintains a CRDT interface.

    This class provides a high-level interface for interacting with the
    governance state in the database. It uses the `DatabaseLWWMap` class to
    ensure that the proposals and votes have LWW semantics.
    """
    
    def __init__(self, session: AsyncSession):
        """Initializes the DatabaseGovernanceState.

        Args:
            session: The SQLAlchemy async session to use for database
                operations.
        """
        self.session = session
        self.proposals = DatabaseLWWMap(session, GovernanceProposal, 'id')
        self.votes = DatabaseLWWMap(session, GovernanceVote, 'id')
    
    async def apply_proposal(self, proposal: Dict[str, Any]):
        """Applies a proposal to the governance state.

        Args:
            proposal: The proposal to apply.
        """
        pid = str(proposal["id"])
        ts = proposal.get("ts", time.time())
        await self.proposals.put(pid, proposal, ts)
    
    async def apply_vote(self, vote: Dict[str, Any]):
        """Applies a vote to the governance state.

        Args:
            vote: The vote to apply.
        """
        key = f"{vote['proposal_id']}:{vote['voter']}"
        ts = vote.get("ts", time.time())
        await self.votes.put(key, vote, ts)
    
    async def merge(self, other: 'DatabaseGovernanceState'):
        """Merges another governance state into this one.

        Args:
            other: The other governance state to merge.
        """
        await self.proposals.merge(other.proposals)
        await self.votes.merge(other.votes)
    
    async def serialize(self) -> Dict[str, Any]:
        """Serializes the governance state to a dictionary.

        Returns:
            A dictionary representation of the governance state.
        """
        proposals_data = await self.proposals.to_dict()
        votes_data = await self.votes.to_dict()
        
        return {
            "proposals": proposals_data,
            "votes": votes_data
        }
    
    @classmethod
    async def deserialize(cls, session: AsyncSession, data: Dict[str, Any]) -> 'DatabaseGovernanceState':
        """Deserializes a governance state from a dictionary.

        Args:
            session: The SQLAlchemy async session to use for database
                operations.
            data: The dictionary to deserialize the governance state from.

        Returns:
            A new instance of the DatabaseGovernanceState class.
        """
        state = cls(session)
        
        # Load proposals
        for pid, proposal in data.get("proposals", {}).items():
            await state.apply_proposal(proposal)
        
        # Load votes
        for vote_key, vote in data.get("votes", {}).items():
            await state.apply_vote(vote)
        
        return state
    
    async def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Gets a specific proposal.

        Args:
            proposal_id: The ID of the proposal to get.

        Returns:
            The proposal, or None if not found.
        """
        return await self.proposals.get(proposal_id)
    
    async def get_votes_for_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Gets all votes for a specific proposal.

        Args:
            proposal_id: The ID of the proposal to get the votes for.

        Returns:
            A list of votes for the proposal.
        """
        stmt = select(GovernanceVote).where(GovernanceVote.proposal_id == proposal_id)
        result = await self.session.execute(stmt)
        votes = result.scalars().all()
        
        return [vote.to_dict() for vote in votes]
    
    async def get_active_proposals(self) -> List[Dict[str, Any]]:
        """Gets all active (non-expired) proposals.

        Returns:
            A list of active proposals.
        """
        now = datetime.utcnow()
        stmt = select(GovernanceProposal).where(
            (GovernanceProposal.expires_at.is_(None)) | 
            (GovernanceProposal.expires_at > now)
        ).where(GovernanceProposal.status == 'pending')
        
        result = await self.session.execute(stmt)
        proposals = result.scalars().all()
        
        return [proposal.to_dict() for proposal in proposals]

class PolicyPersistence:
    """Database persistence for policy engine data.

    This class provides methods for storing, retrieving, and updating policy
    rules and their execution history in the database.
    """
    
    def __init__(self, db_manager):
        """Initializes the PolicyPersistence class.

        Args:
            db_manager: The database manager to use for database operations.
        """
        self.db_manager = db_manager
    
    async def store_policy_rule(self, rule):
        """Stores a policy rule in the database.

        If the rule already exists, it will be updated. Otherwise, a new rule
        will be created.

        Args:
            rule: The policy rule to store.
        """
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
        """Gets a policy rule by name.

        Args:
            rule_name: The name of the policy rule to get.

        Returns:
            The policy rule, or None if not found.
        """
        async with self.db_manager.get_session() as session:
            stmt = select(PolicyRule).where(PolicyRule.name == rule_name)
            result = await session.execute(stmt)
            rule = result.scalar_one_or_none()
            
            return rule.to_dict() if rule else None
    
    async def get_policy_rules(self):
        """Retrieves all policy rules from the database.

        Returns:
            A list of all policy rules in the database.
        """
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
        """Gets all enabled policy rules.

        Returns:
            A list of all enabled policy rules.
        """
        async with self.db_manager.get_session() as session:
            stmt = select(PolicyRule).where(PolicyRule.enabled == True)
            result = await session.execute(stmt)
            rules = result.scalars().all()
            
            return [rule.to_dict() for rule in rules]
    
    async def record_policy_execution(self, rule_name: str, outcome: Dict[str, Any], 
                                     success: bool, improvement_score: float):
        """Records a policy execution.

        Args:
            rule_name: The name of the rule that was executed.
            outcome: The outcome of the execution.
            success: Whether the execution was successful.
            improvement_score: The improvement score of the execution.
        """
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
        """Updates the execution statistics for a rule.

        This method updates the execution count, last execution timestamp, and
        success rate of a rule.

        Args:
            session: The SQLAlchemy async session to use for database
                operations.
            rule_name: The name of the rule to update.
            success: Whether the execution was successful.
        """
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
        """Gets the execution history for a rule.

        Args:
            rule_name: The name of the rule to get the execution history for.
            limit: The maximum number of execution records to return.

        Returns:
            A list of execution records for the rule.
        """
        async with self.db_manager.get_session() as session:
            stmt = select(PolicyExecution).where(
                PolicyExecution.rule_name == rule_name
            ).order_by(PolicyExecution.created_at.desc()).limit(limit)
            
            result = await session.execute(stmt)
            executions = result.scalars().all()
            
            return [execution.to_dict() for execution in executions]

class DatabaseManager:
    """Database connection and session management.

    This class provides methods for creating database tables, getting a
    database session, and closing the database connection.
    """
    
    def __init__(self, database_url: str):
        """Initializes the DatabaseManager.

        Args:
            database_url: The URL of the database to connect to.
        """
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_tables(self):
        """Creates all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self) -> AsyncSession:
        """Gets a database session.

        Returns:
            An async database session.
        """
        return self.async_session()
    
    async def close(self):
        """Closes the database connection."""
        await self.engine.dispose()