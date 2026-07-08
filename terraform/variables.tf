variable "aws_region" {
  description = "AWS region to deploy the MLOps platform into."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name (dev, prod, ...)."
  type        = string
  default     = "dev"
}

variable "name_prefix" {
  description = "Prefix applied to all named resources."
  type        = string
  default     = "mlops"
}

variable "vpc_id" {
  description = "VPC in which to provision the EKS cluster and data stores."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the EKS node groups and RDS."
  type        = list(string)
}

variable "kubernetes_version" {
  description = "EKS control-plane Kubernetes version."
  type        = string
  default     = "1.30"
}

variable "node_instance_types" {
  description = "Instance types for the default managed node group."
  type        = list(string)
  default     = ["m6i.large"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 3
}

variable "metadata_db_instance_class" {
  description = "RDS instance class for the metadata database."
  type        = string
  default     = "db.t3.medium"
}

variable "metadata_db_username" {
  description = "Master username for the metadata database."
  type        = string
  default     = "mlops"
}

variable "metadata_db_password" {
  description = "Master password for the metadata database. Provide via a secret manager or TF_VAR."
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Additional tags applied to all resources."
  type        = map(string)
  default     = {}
}
