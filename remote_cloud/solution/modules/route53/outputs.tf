output "zone_id" {
  description = "Route 53 hosted zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "dns_name" {
  description = "DNS name for the application"
  value       = var.domain_name
}

output "primary_health_check_id" {
  description = "ID of primary region health check"
  value       = aws_route53_health_check.primary.id
}

output "secondary_health_check_id" {
  description = "ID of secondary region health check"
  value       = aws_route53_health_check.secondary.id
}

output "nameservers" {
  description = "Nameservers for the hosted zone"
  value       = aws_route53_zone.main.name_servers
}
