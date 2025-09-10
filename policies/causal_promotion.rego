package spooky.causal

promote_variant {
  input.cuplift.uplift_mean > 0.02
  input.cuplift.uplift_ci95[0] > 0.0  # lower bound positive
}
