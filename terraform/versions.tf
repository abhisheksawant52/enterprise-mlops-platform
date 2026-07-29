terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.57"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state backend. Configure per-environment with a partial backend file,
  # e.g. `terraform init -backend-config=environments/dev/backend.hcl`.
  # backend "s3" {}
}
