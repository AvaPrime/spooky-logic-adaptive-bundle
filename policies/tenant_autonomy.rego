package spooky.tenant_autonomy

# Example: allow tenant meta-conductors to promote within their scoped budgets
allow_promotion {
  input.tenant_budget.spent + input.promotion.estimated_cost <= input.tenant_budget.limit
}
