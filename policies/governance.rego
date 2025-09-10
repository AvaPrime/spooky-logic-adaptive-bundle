package spooky.governance

# A proposal is approved if it reaches quorum and majority yes votes.
approved {
  input.quorum_met
  input.yes_votes >= input.no_votes
}

# Require audit fields
valid_audit {
  input.proposal.tenant
  input.proposal.capability_id
  input.proposal.action
  input.proposal.rationale
}
