package spooky.tenant

default allow = false

# Example: per-tenant spend cap and risk thresholds
allow_action {
  input.tenant == "gold"
  input.estimated_cost <= 1.00
  input.risk <= 4
}

allow_action {
  input.tenant == "standard"
  input.estimated_cost <= 0.25
  input.risk <= 3
}
