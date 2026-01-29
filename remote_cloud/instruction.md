# Multi-Region Active-Active AWS Infrastructure with Terraform

Create comprehensive Terraform infrastructure code for a multi-region AWS environment with failover capabilities.

---

## [WARNING] MANDATORY CONFIGURATION REQUIREMENTS

**The following requirements are strictly enforced by automated tests. Failure to meet ANY of these will result in test failures:**

### 1. Terraform Version (REQUIRED)
Your root module (main.tf or versions.tf) **MUST** include this exact terraform block:
```hcl
terraform {
  required_version = "= 1.6.6"
}
```
This is verified by automated tests and must be present exactly as shown.

### 2. RDS Provider Aliases (REQUIRED)
All RDS cluster resources **MUST** use explicit provider aliases:
- Primary cluster: `provider = aws.primary` (us-east-1)
- Secondary cluster: `provider = aws.secondary` (us-west-2)

Example:
```hcl
resource "aws_rds_cluster" "primary" {
  provider = aws.primary
  # ... configuration
}

resource "aws_rds_cluster" "secondary" {
  provider = aws.secondary
  # ... configuration
}
```

### 3. Route53 Health Check Integration (REQUIRED) - MOST CRITICAL TEST
**CRITICAL: This requirement is strictly enforced. EVERY SINGLE `aws_route53_record` resource MUST include the `health_check_id` attribute. This is verified by automated tests that parse each record block and confirm health_check_id is present.**

If ANY Route53 record is missing `health_check_id`, tests will fail.

**Correct Implementation:**
```hcl
resource "aws_route53_health_check" "primary" {
  fqdn              = var.primary_alb_dns_name
  port              = 80
  type              = "HTTP"
  request_interval  = 30
}

resource "aws_route53_record" "primary" {
  zone_id         = aws_route53_zone.main.zone_id
  name            = var.domain_name
  type            = "A"
  set_identifier  = var.primary_region
  health_check_id = aws_route53_health_check.primary.id    # <-- REQUIRED
  
  latency_routing_policy {
    region = var.primary_region
  }
}
```

**Key Points:**
- Every `aws_route53_record` must have exactly one `health_check_id = aws_route53_health_check.<name>.id` line
- Do NOT put this in comments or outside the resource block
- This is verified by automated test parsing that looks inside each `resource "aws_route53_record"` block

### 4. Module Minimum Line Count Requirements (REQUIRED - HARD LIMITS)
**Each module's main.tf file must contain AT LEAST the specified number of lines of actual code (comments and blank lines don't count). These are hard requirements verified by automated tests.**

- **vpc module**: Minimum 50 lines of code (must include aws_vpc, subnets, gateways, routes)
- **alb module**: Minimum 30 lines of code
- **ecs module**: Minimum 40 lines of code
- **rds module**: Minimum 30 lines of code
- **s3 module**: Minimum 30 lines of code  
- **route53 module**: Minimum 25 lines of code
- **iam module**: Minimum 30 lines of code
- **monitoring module**: Minimum 40 lines of code

**Counting Rules:**
- Only count lines with actual Terraform code
- Exclude comments (lines starting with #)
- Exclude empty/whitespace-only lines
- Tests count non-blank, non-comment lines

**Example - This module has 5 code lines:**
```hcl
# This is a comment (NOT counted)

resource "aws_vpc" "main" {  # line 1
  cidr_block = var.cidr     # line 2
}                            # line 3

variable "cidr" {            # line 4
  type = string              # line 5
}
```

---

## Objective

Create Terraform infrastructure code for a highly available, multi-region AWS environment with failover capabilities. The infrastructure should be designed to support automatic failover during regional outages, with Terraform code that includes monitoring and alerting configurations.

## Requirements

**IMPORTANT:** All requirements below focus on infrastructure configuration and Terraform code structure. Your solution will be validated through automated tests that verify resource definitions, module organization, and syntactic correctness.

### 1. Multi-Region VPC Architecture

- Define Terraform configuration for VPCs in **two AWS regions** (us-east-1 and us-west-2)
- Each VPC must have:
  - Appropriate CIDR block configuration
  - Public and private subnets
  - Internet Gateway for public subnets
  - NAT Gateways for private subnet internet access
  - Proper route tables for public and private subnets

### 2. Application Load Balancers (ALB)

- Define Terraform configuration for ALB resources in each region
- ALB must be internet-facing in public subnets (`internal = false`)
- Configure target groups for ECS services
- Enable health checks on target groups (interval: 30s or less)

### 3. ECS Fargate Services

- Define Terraform configuration for containerized application using ECS Fargate in both regions
- Configure ECS service with:
  - Task definition with appropriate resource allocation
  - Auto-scaling configuration
  - Security groups referenced via `security_groups` or `vpc_security_group_ids`
- Associate tasks with ALB target groups

### 5. Terraform Validation (REQUIRED)
Your solution **MUST pass** `terraform validate` without errors. This is a hard requirement verified by automated tests.

**Required Syntax Rules:**
1. **Nested blocks MUST be multiline** (not single-line)
2. **Each nested block must be on its own line** with proper indentation
3. All resources must be syntactically valid

**INCORRECT (will fail):**
```hcl
# Single-line nested blocks FAIL terraform validate
server_side_encryption_configuration { rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } } }
```

**CORRECT:**
```hcl
# Multiline with proper indentation PASSES
server_side_encryption_configuration {
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

Tests verify:
- `terraform init -backend=false` succeeds
- `terraform validate` succeeds without errors
- Output contains "Success" or "valid" message

### 6. Cross-Region RDS Aurora Cluster

> **[WARNING] CRITICAL: PROVIDER ALIAS REQUIREMENT [WARNING]**
>
> This requirement is **strictly enforced by automated tests**. You MUST use explicit provider aliases:
> - `provider = aws.primary` for primary cluster (us-east-1)
> - `provider = aws.secondary` for secondary cluster (us-west-2)
>
> Tests verify the literal strings `aws.primary` and `aws.secondary` are present in your RDS module.

- Define Terraform configuration for Aurora PostgreSQL cluster with global database configuration
- **Primary cluster MUST be in us-east-1 region** and MUST use `provider = aws.primary`
- **Secondary (read replica) cluster MUST be in us-west-2 region** and MUST use `provider = aws.secondary`
- You MUST define at least 2 `aws_rds_cluster` resources (one for each region) using these specific provider aliases
- Configure `vpc_security_group_ids` for the RDS cluster
- Create `aws_security_group_rule` resources with ingress rules that **explicitly allow only PostgreSQL port 5432**. Do not open other database ports (like 3306 or 1433).

### 7. S3 Buckets with Cross-Region Replication

- Create S3 bucket in each region
- Enable versioning on both buckets
- Configure cross-region replication between buckets
- Enable server-side encryption

#### [WARNING] CRITICAL: Terraform HCL Nested Block Syntax

**Terraform requires proper multi-line formatting for nested blocks. Single-line nested blocks will cause terraform validate failures.**

**INCORRECT** (will fail terraform validate):
```hcl
server_side_encryption_configuration { rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } } }
```

**CORRECT** (proper multi-line format):
```hcl
server_side_encryption_configuration {
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

**Key Points:**
- Each nested block must be on its own line
- Use proper indentation (typically 2 spaces) for each nesting level
- Closing braces should align with their opening block
- This applies to ALL nested blocks in your Terraform configuration (S3, RDS, Route53, CloudWatch, etc.)

### 8. Route 53 Latency-Based DNS

> **[WARNING] CRITICAL: HEALTH CHECK ID REQUIREMENT [WARNING]**
>
> This requirement is **strictly enforced by automated tests**. Every `aws_route53_record` resource **MUST** include the `health_check_id` attribute:
> ```hcl
> health_check_id = aws_route53_health_check.primary.id
> ```
> Tests verify that ALL Route53 records contain `health_check_id`. Records without this attribute will cause test failures.

- Create a hosted zone configuration
- Configure latency-based routing policy
- Create records pointing to both regional ALBs
- Set up `aws_route53_health_check` resources for each ALB endpoint with `request_interval` of 30 seconds or less
- **Every `aws_route53_record` resource MUST include the `health_check_id` attribute** referencing an `aws_route53_health_check`
- Configure failover to redirect traffic when health check fails
- TTL should be 60 seconds or less for quick failover (or use alias records)

### 9. IAM Roles and Policies

- Define IAM roles with appropriate assume role policies
- Configure IAM role policy attachments for required permissions

### 10. CloudWatch Dashboards and Monitoring

- Create unified CloudWatch dashboard resource (`aws_cloudwatch_dashboard`) with `dashboard_body` configuration for infrastructure monitoring

### 11. SNS Alerts

- Create SNS topic resources (`aws_sns_topic`) in **BOTH regions** (us-east-1 and us-west-2)
- **IMPORTANT MODULE NAMING REQUIREMENT**: In your root `main.tf`, monitoring modules MUST be called with prefix `monitoring_[a-z]+`. Specifically, use `module "monitoring_primary"` for the primary region and `module "monitoring_secondary"` for the secondary region. This naming pattern is strictly required for automated test validation (tests verify the regex pattern `module\s+"monitoring_[a-z]+"`).
- **Requirement**: You MUST call the monitoring module (or define resources) separately for each region to ensure SNS topics exist in both us-east-1 and us-west-2.
- Configure CloudWatch alarm resources (`aws_cloudwatch_metric_alarm`) for infrastructure monitoring

### 12. Failover Simulation Scripts

- Create an executable script (`simulate_failover.sh`) that contains:
  - AWS CLI or Terraform commands to simulate regional outage
  - References to security groups, ALB, and Route 53 resources
  - Logic to modify security groups to block traffic in primary region
  - DNS resolution monitoring commands
  - Traffic routing validation logic
  - Failover timing measurement logic

- Create an executable script (`validate_failover.sh`) that contains:
  - DNS resolution or endpoint checking logic
  - Commands to validate traffic routing (e.g., curl, dig, nslookup)
  - Validation logic with conditional statements (if/then)
  - Substantial implementation (at least 5 lines of non-comment code)

## Technical Specifications

### Terraform Structure

Your solution must be organized as follows:

```text
solution/
|-- main.tf                 # Provider configuration and module calls
|-- variables.tf            # Input variables
|-- outputs.tf              # Output values (ALB DNS, RDS endpoints, etc.)
|-- terraform.tfvars        # Variable values (use localstack/test values)
|-- modules/
    |-- vpc/               # VPC module
    |   |-- main.tf        # VPC resources
    |   |-- variables.tf   # Module input variables
    |   +-- outputs.tf     # Module outputs
    |-- alb/               # Application Load Balancer module
    |   |-- main.tf        # ALB resources
    |   |-- variables.tf   # Module input variables
    |   +-- outputs.tf     # Module outputs
    |-- ecs/               # ECS Fargate module
    |   |-- main.tf        # ECS resources
    |   |-- variables.tf   # Module input variables
    |   +-- outputs.tf     # Module outputs
    |-- rds/               # RDS Aurora module
    |   |-- main.tf        # RDS resources
    |   |-- variables.tf   # Module input variables
    |   +-- outputs.tf     # Module outputs
    |-- s3/                # S3 with replication module
    |   |-- main.tf        # S3 resources
    |   |-- variables.tf   # Module input variables
    |   +-- outputs.tf     # Module outputs
    |-- route53/           # Route 53 DNS module
    |   |-- main.tf        # Route 53 resources
    |   |-- variables.tf   # Module input variables
    |   +-- outputs.tf     # Module outputs
    |-- iam/               # IAM roles module
    |   |-- main.tf        # IAM resources
    |   |-- variables.tf   # Module input variables
    |   +-- outputs.tf     # Module outputs
    +-- monitoring/        # CloudWatch and SNS module
        |-- main.tf        # Monitoring resources
        |-- variables.tf   # Module input variables
        +-- outputs.tf     # Module outputs
|-- scripts/
    |-- simulate_failover.sh    # Failover simulation script (must be executable)
    +-- validate_failover.sh    # Validation helper script (must be executable)
```

**Important Module Requirements:**

- Each module directory must contain three files: `main.tf`, `variables.tf`, and `outputs.tf`
- All script files in the `scripts/` directory must have executable permissions (`chmod +x`)
- The `terraform validate` command must succeed and output must include the word "Success"

### Testing Requirements

**Automated Test Scope:**

The automated tests (`tests/test_outputs.py`) verify comprehensive implementation through 30 test functions:

**[WARNING] Critical Tests (Most Common Failure Points):**

These tests are strictly enforced and are the most common causes of failure:

1. **`test_terraform_version_constraint`**: Verifies `required_version = "= 1.6.6"` in root terraform block
2. **`test_rds_primary_secondary_regions`**: Verifies literal `provider = aws.primary` and `provider = aws.secondary` in RDS module
3. **`test_route53_uses_health_checks`**: Verifies every `aws_route53_record` has `health_check_id` attribute (MOST COMMON FAILURE)
4. **`test_security_groups_ecs_to_rds`**: Verifies port 5432 is allowed and ports 3306/1433 are NOT present
5. **`test_terraform_validate`**: Runs `terraform init` and `terraform validate` - must succeed with "Success" message
6. **`test_module_minimum_size`**: Verifies each module meets minimum line count requirements (vpc:50, alb:30, ecs:40, rds:30, s3:30, route53:25, iam:30, monitoring:40)

**Structural Tests:**

- Presence of required Terraform files (main.tf, variables.tf, outputs.tf, terraform.tfvars)
- Existence of all 8 required module directories (vpc, alb, ecs, rds, s3, route53, iam, monitoring)
- Each module contains the required files (main.tf, variables.tf, outputs.tf)
- Presence of failover scripts (simulate_failover.sh, validate_failover.sh)

**Module Completeness Tests (Anti-Cheating):**

- **VPC module**: Must contain aws_vpc, aws_subnet (2+), aws_internet_gateway, aws_nat_gateway, aws_route_table, cidr_block configuration
- **ALB module**: Must contain aws_lb, aws_lb_target_group, aws_lb_listener, health_check block, internet-facing configuration (`internal = false`)
- **ECS module**: Must contain aws_ecs_cluster, aws_ecs_service, aws_ecs_task_definition, FARGATE launch type, aws_appautoscaling resources
- **RDS module**: Must contain aws_rds_cluster, aws_rds_cluster_instance, aurora-postgresql engine, global_cluster configuration, vpc_security_group_ids. **Must use explicit `aws.primary` and `aws.secondary` providers.**
- **S3 module**: Must contain aws_s3_bucket, aws_s3_bucket_versioning, aws_s3_bucket_replication_configuration, encryption configuration
- **Route53 module**: Must contain aws_route53_zone, aws_route53_record, aws_route53_health_check, latency_routing_policy, ttl configuration
- **IAM module**: Must contain 2+ aws_iam_role resources, aws_iam_role_policy_attachment, ECS assume role policy
- **Monitoring module**: Must contain aws_cloudwatch_dashboard, aws_cloudwatch_metric_alarm, aws_sns_topic, dashboard_body configuration

**Behavioral Configuration Tests:**

- Multi-region configuration: Verifies us-east-1/us-west-2 in variables/tfvars or provider aliases
- Failover script implementation: Scripts must contain AWS CLI/Terraform/network commands, reference security groups/ALB/Route53
- Failover timing: Route53 TTL <= 60 seconds, health check interval <= 30 seconds, scripts reference timing
- Security group configuration: Security groups defined and referenced across modules
- Output value assignments: All 8 outputs must have actual value assignments (not empty)
- **Security groups ECS to RDS**: Tests verify that `aws_security_group_rule` resources exist with ingress rules allowing database port 5432 **exclusively** (no 3306 or 1433).
- **Route53 health check references**: Tests verify that **every** `aws_route53_record` includes a `health_check_id` attribute referencing an `aws_route53_health_check` resource

**Minimum Implementation Size:**

- Each module's main.tf must meet minimum line counts (vpc: 50, alb: 30, ecs: 40, rds: 30, s3: 30, route53: 25, iam: 30, monitoring: 40)
- Failover scripts must have substantial implementation (simulate: 10+ lines, validate: 5+ lines)

**Terraform Validation:**

- `terraform init -backend=false` succeeds
- `terraform validate` succeeds and outputs a message containing "Success" or "valid" (case-insensitive matching)

---

## [WARNING] Important Notes on Test Validation

### Automated Tests Validate ACTUAL Resource Blocks, Not Just String Presence

Some tests verify that specific attributes appear WITHIN resource blocks, not just anywhere in the code:

1. **health_check_id in Route53 records**: Tests parse each `resource "aws_route53_record"` block and verify that `health_check_id` appears INSIDE that specific block. Placing `health_check_id` in comments or outside resource blocks will fail tests.

2. **provider aliases in RDS**: Tests verify that `provider = aws.primary` and `provider = aws.secondary` appear in RDS resources (not in comments or other files).

3. **Module line counts**: Tests count actual code lines (excluding comments and blank lines) in each module's main.tf file.

### What This Means For Your Implementation

- Do NOT add required attributes as comments
- Do NOT include required strings in comment-only blocks
- Do NOT artificially inflate line counts with blank lines or comments
- All resource definitions must be actual, functional Terraform code


## Deliverables

1. Complete Terraform infrastructure code in `solution/` directory
2. Failover simulation scripts in `solution/scripts/` directory
3. **Minimum 50% of outputs must reference actual module output values** (e.g., `module.alb.dns_name`) rather than hardcoded strings. Ideally, aim for 80% or higher for better infrastructure modularity.
3. All Terraform configurations must follow proper syntax and structure
4. Terraform outputs in `outputs.tf` must include the following variables with these exact names:
   - `primary_alb_dns` - ALB DNS name for us-east-1
   - `secondary_alb_dns` - ALB DNS name for us-west-2
   - `route53_dns_name` - Route 53 hosted zone name
   - `primary_rds_endpoint` - Primary RDS cluster endpoint
   - `secondary_rds_endpoint` - Secondary RDS cluster endpoint
   - `primary_s3_bucket` - Primary S3 bucket name
   - `secondary_s3_bucket` - Secondary S3 bucket name
   - `cloudwatch_dashboard_url` - CloudWatch dashboard URL

## Success Criteria

Your Terraform configuration must meet ALL of the following criteria:

### [WARNING] Critical Requirements (Strictly Enforced by Tests)

These requirements are verified by automated tests and MUST be implemented exactly as specified:

- [ ] **Terraform Version**: Top-level `terraform` block with `required_version = "= 1.6.6"` in root module
- [ ] **RDS Provider Aliases**: Primary RDS cluster uses `provider = aws.primary`, secondary uses `provider = aws.secondary`
- [ ] **Route53 Health Checks**: Every `aws_route53_record` includes `health_check_id` attribute
- [ ] **PostgreSQL Port Only**: Security group rules allow port 5432 exclusively (no 3306 or 1433)
- [ ] **Terraform Validation**: `terraform validate` succeeds with output containing "Success"
- [ ] **Module Line Counts**: Each module meets minimum requirements (vpc:50, alb:30, ecs:40, rds:30, s3:30, route53:25, iam:30, monitoring:40)

### Standard Requirements

- [ ] All required files and modules are present with correct structure
- [ ] All required resource types are defined in appropriate modules
- [ ] Scripts are executable and contain appropriate commands
- [ ] Required outputs are defined with exact names
- [ ] Module implementations meet minimum line count requirements
- [ ] Route 53 TTL <= 60 seconds, health check intervals <= 30 seconds
- [ ] ALB configured as internet-facing (`internal = false`)

## Notes

- For testing purposes, you may use placeholder values for sensitive data

## Implementation Notes

The automated tests verify structural correctness and resource definitions. Your solution should:

- Define all required AWS resources in the appropriate modules
- Include comprehensive Terraform resource blocks (not stub code)
- Provide failover scripts with implementation logic
- Define all required outputs with proper value assignments

## Debugging Common Test Failures

If your solution fails automated tests, check these items:

### Route53 Health Check Failures (`test_route53_uses_health_checks`)
**Symptom**: Test fails saying aws_route53_record is missing health_check_id.
**Fix**: 
- Verify EVERY aws_route53_record has `health_check_id = aws_route53_health_check.xxx.id` INSIDE the resource block
- Do NOT put health_check_id in comments
- Example of WRONG: `# health_check_id = aws_route53_health_check.primary.id`
- Example of CORRECT: Add actual line `health_check_id = aws_route53_health_check.primary.id` in the resource

### Terraform Validation Failures (`test_terraform_validate`)
**Symptom**: Test fails with terraform validate error.
**Fix**:
- Use multiline syntax for nested blocks (not single-line blocks)
- Check all curly braces are properly matched
- Verify all syntax is correct using `terraform validate` locally
- Common issue: `{ rule { apply_server_side_encryption_by_default { ... } } }` FAILS
- Correct: Each block on separate lines with proper indentation

### Module Line Count Failures (`test_module_minimum_size`)
**Symptom**: Test says module has X code lines but needs Y minimum.
**Fix**:
- Check the line count requirement for each module
- Add missing resources (not just comments) to meet the minimum
- Example: vpc module needs 50 lines - make sure you have aws_vpc, 2+ subnets, internet gateway, nat gateway, route tables
- Comments and blank lines don't count toward line count

### RDS Provider Aliases Not Found
**Symptom**: Test can't find `provider = aws.primary` in RDS module.
**Fix**:
- Add explicit `provider = aws.primary` and `provider = aws.secondary` to each RDS resource
- Example: `resource "aws_rds_cluster" "primary" { provider = aws.primary ... }`
- Make sure these appear in actual resource blocks, not in comments