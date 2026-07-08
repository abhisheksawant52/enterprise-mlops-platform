provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "enterprise-mlops-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
