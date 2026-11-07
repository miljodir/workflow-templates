terraform {
  required_version = ">= 1.7.0"
}

module "dependency" {
  source = "git::https://github.com/example/synthetic-unavailable-module.git"
  label  = "synthetic-value"
}

output "value" {
  value = module.dependency.value
}
