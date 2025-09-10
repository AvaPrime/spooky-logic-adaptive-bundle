package spooky.quarantine

# Allow promotion from quarantine if minimum success and max failure ratio satisfied (checked upstream),
# and policy risk threshold is under the limit for the tenant/task.
allow_promote_from_quarantine {
  input.ready_to_promote
  input.risk <= 3
}
