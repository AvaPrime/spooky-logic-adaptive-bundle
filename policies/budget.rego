package spooky.budget

default allow = false

allow {
  input.estimated_cost <= input.budget.max
}

escalate {
  input.estimated_cost > input.budget.max
}
