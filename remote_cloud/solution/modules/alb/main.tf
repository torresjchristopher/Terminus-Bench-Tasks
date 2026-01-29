terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-${var.region}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP traffic from internet"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS traffic from internet"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-alb-sg"
    Environment = var.environment
    Region      = var.region
  }
}

resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-${var.region}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnets

  enable_deletion_protection = false
  enable_http2               = true

  access_logs {
    bucket  = var.s3_bucket_name
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-alb"
    Environment = var.environment
    Region      = var.region
  }
}

resource "aws_lb_target_group" "main" {
  name        = "${var.project_name}-${var.environment}-${var.region}-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200,404"
  }

  deregistration_delay = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-tg"
    Environment = var.environment
    Region      = var.region
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.region}-listener"
    Environment = var.environment
    Region      = var.region
  }
}
