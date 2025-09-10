from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List
import time, json
from orchestrator.federation.crdt import LWWMap

@dataclass
class GovernanceState:
    """Governance board modeled as CRDT maps: proposals and votes."""
    proposals: LWWMap = field(default_factory=LWWMap)
    votes: LWWMap = field(default_factory=LWWMap)

    def apply_proposal(self, proposal: Dict[str, Any]):
        pid = str(proposal["id"])
        self.proposals.put(pid, proposal, proposal.get("ts", time.time()))

    def apply_vote(self, vote: Dict[str, Any]):
        key = f"{vote['proposal_id']}:{vote['voter']}"
        self.votes.put(key, vote, vote.get("ts", time.time()))

    def merge(self, other: "GovernanceState"):
        self.proposals.merge(other.proposals)
        self.votes.merge(other.votes)

    def serialize(self) -> Dict[str, Any]:
        return {"proposals": self.proposals.to_dict(), "votes": self.votes.to_dict()}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "GovernanceState":
        g = cls()
        for pid, p in data.get("proposals", {}).items():
            g.proposals.put(pid, p, p.get("ts", time.time()))
        for k, v in data.get("votes", {}).items():
            g.votes.put(k, v, v.get("ts", time.time()))
        return g
