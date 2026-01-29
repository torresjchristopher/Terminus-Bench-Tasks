terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws.primary, aws.secondary]
    }
  }
}

# Primary Region RDS Resources
resource "aws_db_subnet_group" "primary" {
  provider   = aws.primary
  name       = "${var.project_name}-${var.environment}-${var.primary_region}-db-subnet"
  subnet_ids = var.primary_private_subnets

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.primary_region}-db-subnet"
    Environment = var.environment
    Region      = var.primary_region
  }
}

resource "aws_security_group" "rds_primary" {
  provider    = aws.primary
  name        = "${var.project_name}-${var.environment}-${var.primary_region}-rds-sg"
  description = "Security group for RDS Aurora cluster"
  vpc_id      = var.primary_vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.primary_region}-rds-sg"
    Environment = var.environment
    Region      = var.primary_region
  }
}

# Security group rule allowing ECS to RDS access (ingress for PostgreSQL port 5432)
resource "aws_security_group_rule" "rds_primary_ingress" {
  provider                 = aws.primary
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = var.primary_ecs_security_group_id
  security_group_id        = aws_security_group.rds_primary.id
  description              = "Allow PostgreSQL access from ECS tasks"
}

# Secondary Region RDS Resources
resource "aws_db_subnet_group" "secondary" {
  provider   = aws.secondary
  name       = "${var.project_name}-${var.environment}-${var.secondary_region}-db-subnet"
  subnet_ids = var.secondary_private_subnets

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.secondary_region}-db-subnet"
    Environment = var.environment
    Region      = var.secondary_region
  }
}

resource "aws_security_group" "rds_secondary" {
  provider    = aws.secondary
  name        = "${var.project_name}-${var.environment}-${var.secondary_region}-rds-sg"
  description = "Security group for RDS Aurora cluster"
  vpc_id      = var.secondary_vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.secondary_ecs_security_group_id]
    description     = "Allow PostgreSQL access from ECS tasks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.secondary_region}-rds-sg"
    Environment = var.environment
    Region      = var.secondary_region
  }
}

# Aurora Global Database
# Multi-region setup: Primary in us-east-1, Secondary in us-west-2
resource "aws_rds_global_cluster" "main" {
  provider                  = aws.primary
  global_cluster_identifier = "${var.project_name}-${var.environment}-global"
  engine                    = "aurora-postgresql"
  engine_version            = "15.3"
  database_name             = "${replace(var.project_name, "-", "_")}_db"
  storage_encrypted         = true
}

# Primary Aurora Cluster
resource "aws_rds_cluster" "primary" {
  provider                    = aws.primary
  cluster_identifier          = "${var.project_name}-${var.environment}-${var.primary_region}-cluster"
  engine                      = aws_rds_global_cluster.main.engine
  engine_version              = aws_rds_global_cluster.main.engine_version
  database_name               = aws_rds_global_cluster.main.database_name
  master_username             = "dbadmin"
  master_password             = "ChangeMe123!" # Should be replaced with secrets manager in production
  global_cluster_identifier   = aws_rds_global_cluster.main.id
  db_subnet_group_name        = aws_db_subnet_group.primary.name
  vpc_security_group_ids      = [aws_security_group.rds_primary.id]
  skip_final_snapshot         = true
  backup_retention_period     = 7
  preferred_backup_window     = "03:00-04:00"
  preferred_maintenance_window = "mon:04:00-mon:05:00"

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.primary_region}-cluster"
    Environment = var.environment
    Region      = var.primary_region
  }

  depends_on = [aws_rds_global_cluster.main]
}

resource "aws_rds_cluster_instance" "primary" {
  provider             = aws.primary
  count                = 1
  identifier           = "${var.project_name}-${var.environment}-${var.primary_region}-instance-${count.index + 1}"
  cluster_identifier   = aws_rds_cluster.primary.id
  instance_class       = var.instance_class
  engine               = aws_rds_cluster.primary.engine
  engine_version       = aws_rds_cluster.primary.engine_version
  publicly_accessible  = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.primary_region}-instance-${count.index + 1}"
    Environment = var.environment
    Region      = var.primary_region
  }
}

# Secondary Aurora Cluster (Read Replica)
resource "aws_rds_cluster" "secondary" {
  provider                    = aws.secondary
  cluster_identifier          = "${var.project_name}-${var.environment}-${var.secondary_region}-cluster"
  engine                      = aws_rds_global_cluster.main.engine
  engine_version              = aws_rds_global_cluster.main.engine_version
  global_cluster_identifier   = aws_rds_global_cluster.main.id
  db_subnet_group_name        = aws_db_subnet_group.secondary.name
  vpc_security_group_ids      = [aws_security_group.rds_secondary.id]
  skip_final_snapshot         = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.secondary_region}-cluster"
    Environment = var.environment
    Region      = var.secondary_region
  }

  depends_on = [aws_rds_cluster_instance.primary]
}

resource "aws_rds_cluster_instance" "secondary" {
  provider             = aws.secondary
  count                = 1
  identifier           = "${var.project_name}-${var.environment}-${var.secondary_region}-instance-${count.index + 1}"
  cluster_identifier   = aws_rds_cluster.secondary.id
  instance_class       = var.instance_class
  engine               = aws_rds_cluster.secondary.engine
  engine_version       = aws_rds_cluster.secondary.engine_version
  publicly_accessible  = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-${var.secondary_region}-instance-${count.index + 1}"
    Environment = var.environment
    Region      = var.secondary_region
  }
}
