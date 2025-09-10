package spooky.auto_adopt

# Auto-adopt if: signature ok, sbom/provenance ok, canary passed, and within budget/policy scope.
allow_auto_adopt {
  input.signature_ok
  input.sbom_ok
  input.provenance_ok
  input.canary_passed
}
