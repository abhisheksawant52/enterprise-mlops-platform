locals {
  name = "${var.name_prefix}-${var.environment}"

  common_tags = merge(
    {
      Project     = "enterprise-mlops-platform"
      Environment = var.environment
    },
    var.tags,
  )
}

# Object storage for models and pipeline artifacts, plus the model registry ECR.
module "storage" {
  source = "./modules/storage"

  name_prefix = local.name
  tags        = local.common_tags
}

# EKS cluster that runs the control-plane API, training jobs, and model serving.
module "eks" {
  source = "./modules/eks"

  name_prefix        = local.name
  kubernetes_version = var.kubernetes_version
  vpc_id             = var.vpc_id
  subnet_ids         = var.private_subnet_ids
  instance_types     = var.node_instance_types
  desired_size       = var.node_desired_size
  tags               = local.common_tags
}

# Metadata database (experiment/registry metadata) on RDS PostgreSQL.
resource "aws_db_subnet_group" "metadata" {
  name       = "${local.name}-metadata"
  subnet_ids = var.private_subnet_ids
  tags       = local.common_tags
}

resource "aws_security_group" "metadata_db" {
  name        = "${local.name}-metadata-db"
  description = "Access to the MLOps metadata database"
  vpc_id      = var.vpc_id
  tags        = local.common_tags
}

resource "aws_db_instance" "metadata" {
  identifier             = "${local.name}-metadata"
  engine                 = "postgres"
  engine_version         = "16.3"
  instance_class         = var.metadata_db_instance_class
  allocated_storage      = 50
  storage_type           = "gp3"
  storage_encrypted      = true
  db_name                = "mlops"
  username               = var.metadata_db_username
  password               = var.metadata_db_password
  db_subnet_group_name   = aws_db_subnet_group.metadata.name
  vpc_security_group_ids = [aws_security_group.metadata_db.id]
  multi_az               = var.environment == "prod"
  skip_final_snapshot    = var.environment != "prod"
  deletion_protection    = var.environment == "prod"
  tags                   = local.common_tags
}
