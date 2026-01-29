variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "replication_role_arn" {
  description = "ARN of IAM role for S3 replication"
  type        = string
}

variable "destination_bucket_arn" {
  description = "ARN of destination bucket for replication"
  type        = string
  default     = ""
}
