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

    def apply_proposal(self, proposal: Dict[str, Any]):
        """
        Applies a proposal to the governance state.

        Args:
            proposal (Dict[str, Any]): The proposal to apply.
        """
        pid = str(proposal["id"])
        ts = proposal.get("ts", time.time())
        self.proposals.put(pid, proposal, ts)

    def apply_vote(self, vote: Dict[str, Any]):
        """
        Applies a vote to the governance state.

        Args:
            vote (Dict[str, Any]): The vote to apply.
        """
        key = f"{vote['proposal_id']}:{vote['voter']}"
        ts = vote.get("ts", time.time())
        self.votes.put(key, vote, ts)

    def merge(self, other: "GovernanceState"):
        """
        Merges another GovernanceState into this one.

        Args:
            other (GovernanceState): The other GovernanceState to merge.
        """
        self.proposals.merge(other.proposals)
        self.votes.merge(other.votes)

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
        g = cls()
        for pid, p in data.get("proposals", {}).items():
            g.proposals.put(pid, p, p.get("ts", time.time()))
        for k, v in data.get("votes", {}).items():
            g.votes.put(k, v, v.get("ts", time.time()))
        return g
