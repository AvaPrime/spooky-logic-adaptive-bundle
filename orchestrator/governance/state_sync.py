from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time, json
import asyncio
import os
from orchestrator.federation.crdt import LWWMap
from .persistence import DatabaseGovernanceState, DatabaseManager

# Configuration for database persistence
DATABASE_URL = os.getenv('GOVERNANCE_DATABASE_URL', 'sqlite+aiosqlite:///governance.db')
USE_DATABASE = os.getenv('USE_DATABASE_PERSISTENCE', 'true').lower() == 'true'

@dataclass
class GovernanceState:
    """Governance board modeled as CRDT maps: proposals and votes.
    
    Supports both in-memory (legacy) and database-backed persistence.
    """
    proposals: LWWMap = field(default_factory=LWWMap)
    votes: LWWMap = field(default_factory=LWWMap)
    
    # Database persistence components
    _db_manager: Optional[DatabaseManager] = field(default=None, init=False)
    _db_state: Optional[DatabaseGovernanceState] = field(default=None, init=False)
    _use_database: bool = field(default=USE_DATABASE, init=False)

<<<<<<< HEAD
    async def _ensure_db_connection(self):
        """Ensure database connection is established."""
        if self._use_database and self._db_manager is None:
            self._db_manager = DatabaseManager(DATABASE_URL)
            await self._db_manager.create_tables()
            session = await self._db_manager.get_session()
            self._db_state = DatabaseGovernanceState(session)
    
    async def apply_proposal(self, proposal: Dict[str, Any]):
        """Apply a proposal to both in-memory and database storage."""
=======
    def apply_proposal(self, proposal: Dict[str, Any]):
        """
        Applies a proposal to the governance state.

        Args:
            proposal (Dict[str, Any]): The proposal to apply.
        """
>>>>>>> 3c4a90cdb18cd40d228da1653114b2f244bb47fd
        pid = str(proposal["id"])
        ts = proposal.get("ts", time.time())
        
        # Always update in-memory for backward compatibility
        self.proposals.put(pid, proposal, ts)
        
        # Update database if enabled
        if self._use_database:
            await self._ensure_db_connection()
            await self._db_state.apply_proposal(proposal)

<<<<<<< HEAD
    async def apply_vote(self, vote: Dict[str, Any]):
        """Apply a vote to both in-memory and database storage."""
=======
    def apply_vote(self, vote: Dict[str, Any]):
        """
        Applies a vote to the governance state.

        Args:
            vote (Dict[str, Any]): The vote to apply.
        """
>>>>>>> 3c4a90cdb18cd40d228da1653114b2f244bb47fd
        key = f"{vote['proposal_id']}:{vote['voter']}"
        ts = vote.get("ts", time.time())
        
        # Always update in-memory for backward compatibility
        self.votes.put(key, vote, ts)
        
        # Update database if enabled
        if self._use_database:
            await self._ensure_db_connection()
            await self._db_state.apply_vote(vote)

<<<<<<< HEAD
    async def merge(self, other: "GovernanceState"):
        """Merge another governance state into this one."""
        # Merge in-memory data
=======
    def merge(self, other: "GovernanceState"):
        """
        Merges another GovernanceState into this one.

        Args:
            other (GovernanceState): The other GovernanceState to merge.
        """
>>>>>>> 3c4a90cdb18cd40d228da1653114b2f244bb47fd
        self.proposals.merge(other.proposals)
        self.votes.merge(other.votes)
        
        # Merge database data if enabled
        if self._use_database and other._db_state:
            await self._ensure_db_connection()
            await self._db_state.merge(other._db_state)

<<<<<<< HEAD
    async def serialize(self) -> Dict[str, Any]:
        """Serialize governance state to dictionary."""
        if self._use_database:
            await self._ensure_db_connection()
            return await self._db_state.serialize()
        else:
            return {"proposals": self.proposals.to_dict(), "votes": self.votes.to_dict()}

    @classmethod
    async def deserialize(cls, data: Dict[str, Any]) -> "GovernanceState":
        """Deserialize governance state from dictionary."""
        g = cls()
        
        # Load into in-memory structures
        for pid, p in data.get("proposals", {}).items():
            g.proposals.put(pid, p, p.get("ts", time.time()))
        for k, v in data.get("votes", {}).items():
            g.votes.put(k, v, v.get("ts", time.time()))
        
        # Load into database if enabled
        if g._use_database:
            await g._ensure_db_connection()
            g._db_state = await DatabaseGovernanceState.deserialize(
                await g._db_manager.get_session(), data
            )
        
        return g
    
    async def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific proposal."""
        if self._use_database:
            await self._ensure_db_connection()
            return await self._db_state.get_proposal(proposal_id)
        else:
            return self.proposals.get(proposal_id)
    
    async def get_votes_for_proposal(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get all votes for a specific proposal."""
        if self._use_database:
            await self._ensure_db_connection()
            return await self._db_state.get_votes_for_proposal(proposal_id)
        else:
            # Filter in-memory votes
            votes = []
            for key, (vote_data, _) in self.votes.data.items():
                if vote_data.get('proposal_id') == proposal_id:
                    votes.append(vote_data)
            return votes
    
    async def get_active_proposals(self) -> List[Dict[str, Any]]:
        """Get all active proposals."""
        if self._use_database:
            await self._ensure_db_connection()
            return await self._db_state.get_active_proposals()
        else:
            # Return all proposals from in-memory storage
            return list(self.proposals.to_dict().values())
    
    async def close(self):
        """Close database connections."""
        if self._db_manager:
            await self._db_manager.close()

    # Synchronous methods for backward compatibility
    def apply_proposal_sync(self, proposal: Dict[str, Any]):
        """Synchronous version of apply_proposal for backward compatibility."""
        pid = str(proposal["id"])
        self.proposals.put(pid, proposal, proposal.get("ts", time.time()))
        
        # Schedule async database update if needed
        if self._use_database:
            asyncio.create_task(self._async_apply_proposal(proposal))
    
    def apply_vote_sync(self, vote: Dict[str, Any]):
        """Synchronous version of apply_vote for backward compatibility."""
        key = f"{vote['proposal_id']}:{vote['voter']}"
        self.votes.put(key, vote, vote.get("ts", time.time()))
        
        # Schedule async database update if needed
        if self._use_database:
            asyncio.create_task(self._async_apply_vote(vote))
    
    async def _async_apply_proposal(self, proposal: Dict[str, Any]):
        """Helper for async proposal application."""
        await self._ensure_db_connection()
        await self._db_state.apply_proposal(proposal)
    
    async def _async_apply_vote(self, vote: Dict[str, Any]):
        """Helper for async vote application."""
        await self._ensure_db_connection()
        await self._db_state.apply_vote(vote)

# Legacy synchronous interface for backward compatibility
class LegacyGovernanceState(GovernanceState):
    """Legacy synchronous interface that maintains the original API."""
    
    def apply_proposal(self, proposal: Dict[str, Any]):
        return self.apply_proposal_sync(proposal)
    
    def apply_vote(self, vote: Dict[str, Any]):
        return self.apply_vote_sync(vote)
    
    def merge(self, other: "GovernanceState"):
        # Synchronous merge for in-memory data only
        self.proposals.merge(other.proposals)
        self.votes.merge(other.votes)
    
    def serialize(self) -> Dict[str, Any]:
        return {"proposals": self.proposals.to_dict(), "votes": self.votes.to_dict()}
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "LegacyGovernanceState":
=======
    def serialize(self) -> Dict[str, Any]:
        """
        Serializes the governance state to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the governance state.
        """
        return {"proposals": self.proposals.to_dict(), "votes": self.votes.to_dict()}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "GovernanceState":
        """
        Deserializes a dictionary into a GovernanceState object.

        Args:
            data (Dict[str, Any]): The dictionary to deserialize.

        Returns:
            GovernanceState: The deserialized GovernanceState object.
        """
>>>>>>> 3c4a90cdb18cd40d228da1653114b2f244bb47fd
        g = cls()
        for pid, p in data.get("proposals", {}).items():
            g.proposals.put(pid, p, p.get("ts", time.time()))
        for k, v in data.get("votes", {}).items():
            g.votes.put(k, v, v.get("ts", time.time()))
        return g
