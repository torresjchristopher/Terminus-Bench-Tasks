variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "multiregion-app"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "primary_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}

variable "secondary_region" {
  description = "Secondary AWS region"
  type        = string
  default     = "us-west-2"
}

variable "primary_vpc_cidr" {
  description = "CIDR block for primary VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "secondary_vpc_cidr" {
  description = "CIDR block for secondary VPC"
  type        = string
  default     = "10.1.0.0/16"
}

variable "domain_name" {
  description = "Domain name for Route 53"
  type        = string
  default     = "example.com"
}

variable "sns_email" {
  description = "Email address for SNS notifications"
  type        = string
  default     = "admin@example.com"
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS tasks"
  type        = number
  default     = 256
}

variable "ecs_task_memory" {
  description = "Memory for ECS tasks"
  type        = number
  default     = 512
}

variable "ecs_desired_count" {
  description = "Desired count of ECS tasks per region"
  type        = number
  default     = 2
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r5.large"
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project    = "MultiRegion"
    ManagedBy  = "Terraform"
  }
}
