output "eks_cluster_name" {
  description = "Name of the EKS cluster running the platform."
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "API server endpoint of the EKS cluster."
  value       = module.eks.cluster_endpoint
}

output "model_bucket" {
  description = "S3 bucket storing registered model artifacts."
  value       = module.storage.model_bucket_name
}

output "artifact_bucket" {
  description = "S3 bucket storing pipeline artifacts."
  value       = module.storage.artifact_bucket_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for platform container images."
  value       = module.storage.ecr_repository_url
}

output "metadata_db_endpoint" {
  description = "Connection endpoint for the metadata database."
  value       = aws_db_instance.metadata.endpoint
}
