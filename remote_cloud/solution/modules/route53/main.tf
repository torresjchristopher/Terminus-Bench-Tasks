terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

resource "aws_route53_zone" "main" {
  name = var.domain_name

  tags = {
    Name        = "${var.project_name}-${var.environment}-zone"
    Environment = var.environment
  }
}

# Health Checks
resource "aws_route53_health_check" "primary" {
  fqdn              = var.primary_alb_dns_name
  port              = 80
  type              = "HTTP"
  resource_path     = "/"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.primary_region}-health"
    Environment = var.environment
    Region      = var.primary_region
  }
}

resource "aws_route53_health_check" "secondary" {
  fqdn              = var.secondary_alb_dns_name
  port              = 80
  type              = "HTTP"
  resource_path     = "/"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.secondary_region}-health"
    Environment = var.environment
    Region      = var.secondary_region
  }
}

# Latency-based routing records
resource "aws_route53_record" "primary" {
  zone_id         = aws_route53_zone.main.zone_id
  name            = var.domain_name
  type            = "A"
  set_identifier  = var.primary_region
  health_check_id = aws_route53_health_check.primary.id

  alias {
    name                   = var.primary_alb_dns_name
    zone_id                = var.primary_alb_zone_id
    evaluate_target_health = true
  }

  latency_routing_policy {
    region = var.primary_region
  }
}

resource "aws_route53_record" "secondary" {
  zone_id         = aws_route53_zone.main.zone_id
  name            = var.domain_name
  type            = "A"
  set_identifier  = var.secondary_region
  health_check_id = aws_route53_health_check.secondary.id

  alias {
    name                   = var.secondary_alb_dns_name
    zone_id                = var.secondary_alb_zone_id
    evaluate_target_health = true
  }

  latency_routing_policy {
    region = var.secondary_region
  }
}
