variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "domain_name" {
  description = "Domain name for Route 53 hosted zone"
  type        = string
}

variable "primary_alb_dns_name" {
  description = "DNS name of primary ALB"
  type        = string
}

variable "primary_alb_zone_id" {
  description = "Zone ID of primary ALB"
  type        = string
}

variable "secondary_alb_dns_name" {
  description = "DNS name of secondary ALB"
  type        = string
}

variable "secondary_alb_zone_id" {
  description = "Zone ID of secondary ALB"
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
