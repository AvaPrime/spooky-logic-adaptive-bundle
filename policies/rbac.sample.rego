package spooky.rbac

allow {
  input.role == "admin"
}

allow {
  input.role == "operator"
  input.action == "read"
}

deny {
  input.role == "tenant"
  input.action == "killswitch_trigger"
}
