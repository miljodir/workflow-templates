terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_password" "sample" {
  length = 16
}

output "value" {
  value = random_password.sample.result
}
