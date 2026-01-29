variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "primary_region" {
  description = "Primary AWS region"
  type        = string
}

variable "secondary_region" {
  description = "Secondary AWS region"
  type        = string
}

variable "primary_vpc_id" {
  description = "Primary VPC ID"
  type        = string
}

variable "secondary_vpc_id" {
  description = "Secondary VPC ID"
  type        = string
}

variable "primary_private_subnets" {
  description = "List of primary private subnet IDs"
  type        = list(string)
}

variable "secondary_private_subnets" {
  description = "List of secondary private subnet IDs"
  type        = list(string)
}

variable "primary_ecs_security_group_id" {
  description = "Primary ECS security group ID"
  type        = string
}

variable "secondary_ecs_security_group_id" {
  description = "Secondary ECS security group ID"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
}
