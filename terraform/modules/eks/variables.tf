variable "name_prefix" {
  description = "Prefix applied to cluster and IAM resource names."
  type        = string
}

variable "kubernetes_version" {
  description = "EKS control-plane Kubernetes version."
  type        = string
  default     = "1.30"
}

variable "vpc_id" {
  description = "VPC hosting the cluster (reserved for future SG wiring)."
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for the cluster and node group."
  type        = list(string)
}

variable "instance_types" {
  description = "Instance types for the managed node group."
  type        = list(string)
  default     = ["m6i.large"]
}

variable "desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 3
}

variable "min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 6
}

variable "tags" {
  description = "Tags applied to all cluster resources."
  type        = map(string)
  default     = {}
}
