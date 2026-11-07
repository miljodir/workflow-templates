run "tofu_plan" {
  command = plan

  assert {
    condition     = output.value
    error_message = "The exclusively OpenTofu suite must execute."
  }
}
