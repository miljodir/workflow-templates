mock_provider "random" {
  mock_resource "random_integer" {
    defaults = {
      result = 7
    }
  }
}

run "mocked_apply" {
  command = apply

  assert {
    condition     = output.number == 8
    error_message = "The mocked provider must return the synthetic number."
  }
}
