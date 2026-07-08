output "model_bucket_name" {
  description = "Name of the model artifact bucket."
  value       = aws_s3_bucket.models.bucket
}

output "artifact_bucket_name" {
  description = "Name of the pipeline artifact bucket."
  value       = aws_s3_bucket.artifacts.bucket
}

output "ecr_repository_url" {
  description = "URL of the platform ECR repository."
  value       = aws_ecr_repository.platform.repository_url
}
