mock_provider "random" {
  mock_resource "random_password" {
    defaults = {
      result = "synthetic-password"
    }
  }
}

run "mocked_sensitive_output" {
  command = apply

  assert {
    condition     = output.value == "synthetic-password"
    error_message = "The mocked sensitive output must retain its synthetic value."
  }
}
