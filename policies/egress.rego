package spooky.egress

allow_tool[tool] {
  tool := input.tool
  allowed := {"mhe.search", "sympy.solve", "pytest.run"}
  tool.name == allowed[_]
}
