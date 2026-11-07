run "prepared_dependency_contract" {
  command = plan

  assert {
    condition     = module.dependency.value == "synthetic-value"
    error_message = "The fixture must preserve the tested dependency contract."
  }

  assert {
    condition     = output.value == "test-only-value"
    error_message = "The test-only override must be applied after validation."
  }
}
