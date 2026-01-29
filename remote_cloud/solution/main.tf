terraform {
  required_version = "= 1.6.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Primary region provider
provider "aws" {
  alias  = "primary"
  region = "us-east-1"

  default_tags {
    tags = merge(var.common_tags, {
      Environment = var.environment
    })
  }
}

# Secondary region provider
provider "aws" {
  alias  = "secondary"
  region = "us-west-2"

  default_tags {
    tags = merge(var.common_tags, {
      Environment = var.environment
    })
  }
}

# IAM Roles (Global)
module "iam" {
  source = "./modules/iam"
  providers = {
    aws = aws.primary
  }

  project_name = var.project_name
  environment  = var.environment
}

# Primary Region Infrastructure
module "vpc_primary" {
  source = "./modules/vpc"
  providers = {
    aws = aws.primary
  }

  project_name = var.project_name
  environment  = var.environment
  region       = var.primary_region
  vpc_cidr     = var.primary_vpc_cidr
}

module "alb_primary" {
  source = "./modules/alb"
  providers = {
    aws = aws.primary
  }

  project_name     = var.project_name
  environment      = var.environment
  region           = var.primary_region
  vpc_id           = module.vpc_primary.vpc_id
  public_subnets   = module.vpc_primary.public_subnets
  s3_bucket_name   = module.s3_primary.bucket_name
}

module "ecs_primary" {
  source = "./modules/ecs"
  providers = {
    aws = aws.primary
  }

  project_name              = var.project_name
  environment               = var.environment
  region                    = var.primary_region
  vpc_id                    = module.vpc_primary.vpc_id
  private_subnets           = module.vpc_primary.private_subnets
  alb_target_group_arn      = module.alb_primary.target_group_arn
  alb_security_group_id     = module.alb_primary.security_group_id
  ecs_task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_task_role_arn         = module.iam.ecs_task_role_arn
  task_cpu                  = var.ecs_task_cpu
  task_memory               = var.ecs_task_memory
  desired_count             = var.ecs_desired_count
}

module "s3_primary" {
  source = "./modules/s3"
  providers = {
    aws = aws.primary
  }

  project_name               = var.project_name
  environment                = var.environment
  region                     = var.primary_region
  replication_role_arn       = module.iam.s3_replication_role_arn
  destination_bucket_arn     = module.s3_secondary.bucket_arn
}

# Secondary Region Infrastructure
module "vpc_secondary" {
  source = "./modules/vpc"
  providers = {
    aws = aws.secondary
  }

  project_name = var.project_name
  environment  = var.environment
  region       = var.secondary_region
  vpc_cidr     = var.secondary_vpc_cidr
}

module "alb_secondary" {
  source = "./modules/alb"
  providers = {
    aws = aws.secondary
  }

  project_name     = var.project_name
  environment      = var.environment
  region           = var.secondary_region
  vpc_id           = module.vpc_secondary.vpc_id
  public_subnets   = module.vpc_secondary.public_subnets
  s3_bucket_name   = module.s3_secondary.bucket_name
}

module "ecs_secondary" {
  source = "./modules/ecs"
  providers = {
    aws = aws.secondary
  }

  project_name              = var.project_name
  environment               = var.environment
  region                    = var.secondary_region
  vpc_id                    = module.vpc_secondary.vpc_id
  private_subnets           = module.vpc_secondary.private_subnets
  alb_target_group_arn      = module.alb_secondary.target_group_arn
  alb_security_group_id     = module.alb_secondary.security_group_id
  ecs_task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_task_role_arn         = module.iam.ecs_task_role_arn
  task_cpu                  = var.ecs_task_cpu
  task_memory               = var.ecs_task_memory
  desired_count             = var.ecs_desired_count
}

module "s3_secondary" {
  source = "./modules/s3"
  providers = {
    aws = aws.secondary
  }

  project_name               = var.project_name
  environment                = var.environment
  region                     = var.secondary_region
  replication_role_arn       = module.iam.s3_replication_role_arn
  destination_bucket_arn     = module.s3_primary.bucket_arn
}

# RDS Aurora Global Database
module "rds" {
  source = "./modules/rds"
  providers = {
    aws.primary   = aws.primary
    aws.secondary = aws.secondary
  }

  project_name              = var.project_name
  environment               = var.environment
  primary_region            = var.primary_region
  secondary_region          = var.secondary_region
  primary_vpc_id            = module.vpc_primary.vpc_id
  secondary_vpc_id          = module.vpc_secondary.vpc_id
  primary_private_subnets   = module.vpc_primary.private_subnets
  secondary_private_subnets = module.vpc_secondary.private_subnets
  primary_ecs_security_group_id   = module.ecs_primary.security_group_id
  secondary_ecs_security_group_id = module.ecs_secondary.security_group_id
  instance_class            = var.rds_instance_class
}

# Route 53 DNS
module "route53" {
  source = "./modules/route53"
  providers = {
    aws = aws.primary
  }

  project_name              = var.project_name
  environment               = var.environment
  domain_name               = var.domain_name
  primary_alb_dns_name      = module.alb_primary.dns_name
  primary_alb_zone_id       = module.alb_primary.zone_id
  secondary_alb_dns_name    = module.alb_secondary.dns_name
  secondary_alb_zone_id     = module.alb_secondary.zone_id
  primary_region            = var.primary_region
  secondary_region          = var.secondary_region
}

# Monitoring and Alerts
module "monitoring_primary" {
  source = "./modules/monitoring"
  providers = {
    aws = aws.primary
  }

  project_name                = var.project_name
  environment                 = var.environment
  region                      = var.primary_region
  sns_email                   = var.sns_email
  alb_arn_suffix              = module.alb_primary.arn_suffix
  ecs_cluster_name            = module.ecs_primary.cluster_name
  ecs_service_name            = module.ecs_primary.service_name
  target_group_arn_suffix     = module.alb_primary.target_group_arn_suffix
  rds_cluster_id              = module.rds.primary_cluster_id
  route53_health_check_id     = module.route53.primary_health_check_id
}

module "monitoring_secondary" {
  source = "./modules/monitoring"
  providers = {
    aws = aws.secondary
  }

  project_name                = var.project_name
  environment                 = var.environment
  region                      = var.secondary_region
  sns_email                   = var.sns_email
  alb_arn_suffix              = module.alb_secondary.arn_suffix
  ecs_cluster_name            = module.ecs_secondary.cluster_name
  ecs_service_name            = module.ecs_secondary.service_name
  target_group_arn_suffix     = module.alb_secondary.target_group_arn_suffix
  rds_cluster_id              = module.rds.secondary_cluster_id
  route53_health_check_id     = module.route53.secondary_health_check_id
}