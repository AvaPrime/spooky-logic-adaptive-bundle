package spooky.promotion

promote_variant {
  input.stats.uplift_accuracy > 0.03
  input.stats.p_value < 0.05
  input.stats.cost_delta <= 0.10
}
demote_variant {
  input.stats.uplift_accuracy < 0.0
}
