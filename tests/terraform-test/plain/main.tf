terraform {
  required_version = ">= 1.7.0"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_integer" "sample" {
  min = 1
  max = 10
}

output "number" {
  value = random_integer.sample.result
}
