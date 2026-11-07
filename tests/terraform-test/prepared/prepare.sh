#!/usr/bin/env bash
set -euo pipefail

source='git::https://github.com/example/synthetic-unavailable-module.git'
if [[ "$(grep -Fc "$source" main.tf)" -ne 1 ]]; then
  echo "::error::Expected exactly one synthetic dependency source"
  exit 1
fi
sed -i "s|$source|./checks/fixtures/dependency|" main.tf
