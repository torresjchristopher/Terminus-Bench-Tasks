output "primary_vpc_id" {
  description = "Primary VPC ID"
  value       = module.vpc_primary.vpc_id
}

output "secondary_vpc_id" {
  description = "Secondary VPC ID"
  value       = module.vpc_secondary.vpc_id
}

output "primary_alb_dns" {
  description = "Primary ALB DNS name"
  value       = module.alb_primary.dns_name
}

output "secondary_alb_dns" {
  description = "Secondary ALB DNS name"
  value       = module.alb_secondary.dns_name
}

output "route53_dns_name" {
  description = "Route 53 DNS name for the application"
  value       = module.route53.dns_name
}

output "primary_rds_endpoint" {
  description = "Primary RDS cluster endpoint"
  value       = module.rds.primary_cluster_endpoint
}

output "secondary_rds_endpoint" {
  description = "Secondary RDS cluster endpoint"
  value       = module.rds.secondary_cluster_endpoint
}

output "primary_s3_bucket" {
  description = "Primary S3 bucket name"
  value       = module.s3_primary.bucket_name
}

output "secondary_s3_bucket" {
  description = "Secondary S3 bucket name"
  value       = module.s3_secondary.bucket_name
}

output "primary_ecs_cluster" {
  description = "Primary ECS cluster name"
  value       = module.ecs_primary.cluster_name
}

output "secondary_ecs_cluster" {
  description = "Secondary ECS cluster name"
  value       = module.ecs_secondary.cluster_name
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.primary_region}#dashboards:name=${var.project_name}-${var.environment}-dashboard"
}

output "primary_sns_topic_arn" {
  description = "Primary region SNS topic ARN"
  value       = module.monitoring_primary.sns_topic_arn
}

output "secondary_sns_topic_arn" {
  description = "Secondary region SNS topic ARN"
  value       = module.monitoring_secondary.sns_topic_arn
}
