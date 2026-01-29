output "primary_cluster_id" {
  description = "ID of the primary RDS cluster"
  value       = aws_rds_cluster.primary.id
}

output "primary_cluster_endpoint" {
  description = "Endpoint of the primary RDS cluster"
  value       = aws_rds_cluster.primary.endpoint
}

output "primary_cluster_reader_endpoint" {
  description = "Reader endpoint of the primary RDS cluster"
  value       = aws_rds_cluster.primary.reader_endpoint
}

output "secondary_cluster_id" {
  description = "ID of the secondary RDS cluster"
  value       = aws_rds_cluster.secondary.id
}

output "secondary_cluster_endpoint" {
  description = "Endpoint of the secondary RDS cluster"
  value       = aws_rds_cluster.secondary.endpoint
}

output "secondary_cluster_reader_endpoint" {
  description = "Reader endpoint of the secondary RDS cluster"
  value       = aws_rds_cluster.secondary.reader_endpoint
}

output "global_cluster_id" {
  description = "ID of the global RDS cluster"
  value       = aws_rds_global_cluster.main.id
}
