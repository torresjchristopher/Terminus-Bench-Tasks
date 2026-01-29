terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

# SNS Topic for Alerts - deployed in each region via provider = aws
resource "aws_sns_topic" "alerts" {
  provider = aws
  name     = "${var.project_name}-${var.environment}-${var.region}-alerts"

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-alerts"
    Environment = var.environment
    Region      = var.region
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.sns_email
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-${var.region}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", { stat = "Sum", label = "ALB Requests" }],
            [".", "TargetResponseTime", { stat = "Average", label = "ALB Latency" }]
          ]
          period = 60
          stat   = "Average"
          region = var.region
          title  = "ALB Metrics - ${var.region}"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.ecs_service_name, "ClusterName", var.ecs_cluster_name, { stat = "Average" }],
            [".", "MemoryUtilization", ".", ".", ".", ".", { stat = "Average" }]
          ]
          period = 60
          stat   = "Average"
          region = var.region
          title  = "ECS Metrics - ${var.region}"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBClusterIdentifier", var.rds_cluster_id, { stat = "Average" }],
            [".", "CPUUtilization", ".", ".", { stat = "Average" }]
          ]
          period = 60
          stat   = "Average"
          region = var.region
          title  = "RDS Metrics - ${var.region}"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Route53", "HealthCheckStatus", "HealthCheckId", var.route53_health_check_id, { stat = "Average" }]
          ]
          period = 60
          stat   = "Average"
          region = "us-east-1"
          title  = "Route 53 Health Check - ${var.region}"
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_targets" {
  alarm_name          = "${var.project_name}-${var.environment}-${var.region}-alb-unhealthy-targets"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alert when ALB has unhealthy targets"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    TargetGroup  = var.target_group_arn_suffix
    LoadBalancer = var.alb_arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-alb-unhealthy"
    Environment = var.environment
    Region      = var.region
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_service_count" {
  alarm_name          = "${var.project_name}-${var.environment}-${var.region}-ecs-service-count"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "RunningTaskCount"
  namespace           = "ECS/ContainerInsights"
  period              = 60
  statistic           = "Average"
  threshold           = 2
  alarm_description   = "Alert when ECS running count is less than desired"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ServiceName = var.ecs_service_name
    ClusterName = var.ecs_cluster_name
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-ecs-count"
    Environment = var.environment
    Region      = var.region
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-${var.region}-rds-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Alert when RDS CPU exceeds 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBClusterIdentifier = var.rds_cluster_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-rds-cpu"
    Environment = var.environment
    Region      = var.region
  }
}

resource "aws_cloudwatch_metric_alarm" "route53_health_check" {
  alarm_name          = "${var.project_name}-${var.environment}-${var.region}-route53-health"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = 60
  statistic           = "Minimum"
  threshold           = 1
  alarm_description   = "Alert when Route 53 health check fails"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    HealthCheckId = var.route53_health_check_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-route53-health"
    Environment = var.environment
    Region      = var.region
  }
}
