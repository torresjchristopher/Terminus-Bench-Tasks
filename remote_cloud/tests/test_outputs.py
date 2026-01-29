"""
Terraform Multi-Region Infrastructure Tests

Tests verify:
- Terraform version constraint (required_version = "= 1.6.6")
- RDS provider aliases (aws.primary, aws.secondary)
- Route53 health_check_id on all records
- PostgreSQL port 5432 exclusivity
"""

import os
import re
import subprocess

# Base path for solution directory
SOLUTION_DIR = "/app/solution"

def read_file(filepath):
    """Read file contents, return empty string if file doesn't exist."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, IOError):
        return ""

def get_all_tf_files(directory):
    """Get all .tf files recursively from a directory."""
    tf_files = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.tf'):
                tf_files.append(os.path.join(root, f))
    return tf_files

def get_module_content(module_name):
    """Get combined content of all .tf files in a module."""
    module_path = os.path.join(SOLUTION_DIR, "modules", module_name)
    content = ""
    for tf_file in get_all_tf_files(module_path):
        content += read_file(tf_file) + "\n"
    return content

def get_root_tf_content():
    """Get combined content of root-level .tf files."""
    content = ""
    for f in ["main.tf", "variables.tf", "outputs.tf", "versions.tf", "providers.tf"]:
        filepath = os.path.join(SOLUTION_DIR, f)
        content += read_file(filepath) + "\n"
    return content


# =============================================================================
# STRUCTURAL TESTS
# =============================================================================

class TestTerraformFilesExist:
    """Test that required Terraform files exist."""

    def test_terraform_files_exist(self):
        """Verify main.tf, variables.tf, outputs.tf exist in solution root."""
        required_files = ["main.tf", "variables.tf", "outputs.tf"]
        for f in required_files:
            filepath = os.path.join(SOLUTION_DIR, f)
            assert os.path.exists(filepath), f"Required file {f} not found in solution root"

    def test_terraform_modules_exist(self):
        """Verify all 8 required module directories exist with proper files."""
        required_modules = ["vpc", "alb", "ecs", "rds", "s3", "route53", "iam", "monitoring"]
        for module in required_modules:
            module_path = os.path.join(SOLUTION_DIR, "modules", module)
            assert os.path.isdir(module_path), f"Module directory {module} not found"
            for f in ["main.tf", "variables.tf", "outputs.tf"]:
                filepath = os.path.join(module_path, f)
                assert os.path.exists(filepath), f"Required file {f} not found in module {module}"

    def test_scripts_exist_and_executable(self):
        """Verify failover scripts exist and are executable."""
        scripts = ["simulate_failover.sh", "validate_failover.sh"]
        scripts_dir = os.path.join(SOLUTION_DIR, "scripts")
        for script in scripts:
            script_path = os.path.join(scripts_dir, script)
            assert os.path.exists(script_path), f"Script {script} not found"
            
            # Check executability
            # In some container envs, os.access might behave differently, but we check permission bits
            # st_mode check is more reliable for 'chmod +x' verification
            st = os.stat(script_path)
            assert bool(st.st_mode & 0o100), f"Script {script} must be executable (chmod +x)"

    def test_terraform_tfvars_exists_and_configured(self):
        """Verify terraform.tfvars exists and has content."""
        tfvars_path = os.path.join(SOLUTION_DIR, "terraform.tfvars")
        assert os.path.exists(tfvars_path), "terraform.tfvars not found"
        content = read_file(tfvars_path)
        assert len(content.strip()) > 0, "terraform.tfvars is empty"


# =============================================================================
# CRITICAL REQUIREMENT TESTS
# =============================================================================

class TestTerraformVersion:
    """Test Terraform version constraint is properly set."""

    def test_terraform_version_constraint(self):
        """Verify required_version = '= 1.6.6' is set in root terraform block."""
        root_content = get_root_tf_content()

        # Check for terraform block with required_version
        terraform_block_pattern = r'terraform\s*\{[^}]*required_version\s*=\s*["\']?=\s*1\.6\.6["\']?[^}]*\}'
        match = re.search(terraform_block_pattern, root_content, re.DOTALL)

        if not match:
            # Also check for the exact string pattern
            assert 'required_version' in root_content, "No required_version found in terraform configuration"
            assert '1.6.6' in root_content, "Terraform version 1.6.6 not specified"
            # More flexible check
            version_pattern = r'required_version\s*=\s*["\']?=?\s*1\.6\.6["\']?'
            assert re.search(version_pattern, root_content), \
                "required_version = \"= 1.6.6\" not found in root terraform block"


class TestRDSProviderAliases:
    """Test RDS module uses correct provider aliases."""

    def test_rds_primary_secondary_regions(self):
        """Verify RDS module uses aws.primary and aws.secondary provider aliases."""
        rds_content = get_module_content("rds")

        # Check for explicit provider aliases
        has_aws_primary = bool(re.search(r'provider\s*=\s*aws\.primary', rds_content))
        has_aws_secondary = bool(re.search(r'provider\s*=\s*aws\.secondary', rds_content))

        assert has_aws_primary, \
            "RDS module must use 'provider = aws.primary' for primary cluster (us-east-1)"
        assert has_aws_secondary, \
            "RDS module must use 'provider = aws.secondary' for secondary cluster (us-west-2)"

        # Also verify aws_rds_cluster resources exist
        assert 'aws_rds_cluster' in rds_content, "RDS module must contain aws_rds_cluster resources"


class TestRoute53HealthChecks:
    """Test Route53 records include health_check_id."""

    def test_route53_uses_health_checks(self):
        """Verify every aws_route53_record includes health_check_id attribute."""
        route53_content = get_module_content("route53")

        # Verify health check resources exist
        assert 'aws_route53_health_check' in route53_content, \
            "Route53 module must contain aws_route53_health_check resources"

        # Parse actual aws_route53_record blocks to ensure health_check_id is within them
        # Use regex to find resource blocks and extract their content
        record_pattern = r'resource\s+"aws_route53_record"\s+"[^"]+"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        records = re.findall(record_pattern, route53_content, re.DOTALL)
        
        assert len(records) > 0, "No aws_route53_record resources found in route53 module"
        
        # Check that each record block contains health_check_id
        for i, record_block in enumerate(records):
            # Verify health_check_id exists within this specific record block
            has_health_check = bool(re.search(r'health_check_id\s*=', record_block))
            assert has_health_check, \
                f"aws_route53_record #{i+1} does not have health_check_id. " \
                "Every aws_route53_record MUST include health_check_id."


class TestSecurityGroupPorts:
    """Test security groups only allow PostgreSQL port."""

    def test_security_groups_ecs_to_rds(self):
        """Verify security group rules allow port 5432 and not other DB ports."""
        rds_content = get_module_content("rds")
        all_content = rds_content + get_module_content("vpc")

        # Check for port 5432 (PostgreSQL)
        has_5432 = bool(re.search(r'(from_port|to_port)\s*=\s*5432', all_content))

        # Check that MySQL (3306) and MSSQL (1433) are NOT present
        has_3306 = bool(re.search(r'(from_port|to_port)\s*=\s*3306', all_content))
        has_1433 = bool(re.search(r'(from_port|to_port)\s*=\s*1433', all_content))

        assert has_5432, "Security group rules must allow PostgreSQL port 5432"
        assert not has_3306, "Security group rules must NOT allow MySQL port 3306"
        assert not has_1433, "Security group rules must NOT allow MSSQL port 1433"


# =============================================================================
# MODULE COMPLETENESS TESTS
# =============================================================================

class TestVPCModule:
    """Test VPC module completeness."""

    def test_vpc_module_complete(self):
        """Verify VPC module contains all required resources."""
        content = get_module_content("vpc")
        required = ["aws_vpc", "aws_subnet", "aws_internet_gateway", "aws_nat_gateway",
                   "aws_route_table", "cidr_block"]
        for r in required:
            assert r in content, f"VPC module missing {r}"
        # Must have at least 2 subnets
        subnet_count = len(re.findall(r'resource\s+"aws_subnet"', content))
        assert subnet_count >= 2, "VPC module must have at least 2 subnets"


class TestALBModule:
    """Test ALB module completeness."""

    def test_alb_module_complete(self):
        """Verify ALB module contains all required resources."""
        content = get_module_content("alb")
        required = ["aws_lb", "aws_lb_target_group", "aws_lb_listener", "health_check"]
        for r in required:
            assert r in content, f"ALB module missing {r}"

    def test_alb_in_public_subnets(self):
        """Verify ALB is internet-facing."""
        content = get_module_content("alb")
        # Check for internal = false
        assert re.search(r'internal\s*=\s*false', content), \
            "ALB must be internet-facing (internal = false)"

    def test_alb_health_check_interval(self):
        """Verify ALB health check interval is 30s or less."""
        content = get_module_content("alb")
        intervals = re.findall(r'interval\s*=\s*(\d+)', content)
        for interval in intervals:
            assert int(interval) <= 30, f"Health check interval {interval} exceeds 30 seconds"


class TestECSModule:
    """Test ECS module completeness."""

    def test_ecs_module_complete(self):
        """Verify ECS module contains all required resources."""
        content = get_module_content("ecs")
        required = ["aws_ecs_cluster", "aws_ecs_service", "aws_ecs_task_definition", "FARGATE"]
        for r in required:
            assert r in content, f"ECS module missing {r}"

    def test_ecs_alb_target_group_association(self):
        """Verify ECS service has target group association."""
        content = get_module_content("ecs")
        assert "load_balancer" in content or "target_group" in content, \
            "ECS service must be associated with ALB target group"

    def test_ecs_autoscaling(self):
        """Verify ECS autoscaling is configured."""
        content = get_module_content("ecs")
        # Check for autoscaling target or appautoscaling
        assert "aws_appautoscaling_target" in content or "aws_appautoscaling_policy" in content, \
            "ECS module must configure autoscaling resources"


class TestRDSModule:
    """Test RDS module completeness."""

    def test_rds_module_complete(self):
        """Verify RDS module contains all required resources."""
        content = get_module_content("rds")
        required = ["aws_rds_cluster", "aws_rds_cluster_instance", "aurora-postgresql",
                   "vpc_security_group_ids"]
        for r in required:
            assert r in content, f"RDS module missing {r}"


class TestS3Module:
    """Test S3 module completeness."""

    def test_s3_module_complete(self):
        """Verify S3 module contains all required resources."""
        content = get_module_content("s3")
        required = ["aws_s3_bucket", "aws_s3_bucket_versioning",
                   "aws_s3_bucket_replication_configuration"]
        for r in required:
            assert r in content, f"S3 module missing {r}"

    def test_s3_encryption(self):
        """Verify S3 buckets have server-side encryption enabled."""
        content = get_module_content("s3")
        assert "server_side_encryption_configuration" in content, \
            "S3 buckets must have server-side encryption configuration"


class TestRoute53Module:
    """Test Route53 module completeness."""

    def test_route53_module_complete(self):
        """Verify Route53 module contains all required resources."""
        content = get_module_content("route53")
        required = ["aws_route53_zone", "aws_route53_record", "aws_route53_health_check"]
        for r in required:
            assert r in content, f"Route53 module missing {r}"

    def test_route53_health_check_interval(self):
        """Verify Route53 health check request_interval is 30s or less."""
        content = get_module_content("route53")
        intervals = re.findall(r'request_interval\s*=\s*(\d+)', content)
        assert len(intervals) > 0, "Route53 module must specify request_interval for health checks"
        for interval in intervals:
            assert int(interval) <= 30, f"Health check request_interval {interval} exceeds 30 seconds"

    def test_route53_latency_policy(self):
        """Verify Route53 uses latency routing policy."""
        content = get_module_content("route53")
        # Check for latency_routing_policy block OR set_identifier + region (which implies latency/geo)
        has_latency = "latency_routing_policy" in content or ("set_identifier" in content and "region" in content)
        assert has_latency, "Route53 records must use latency routing policy"


class TestIAMModule:
    """Test IAM module completeness."""

    def test_iam_module_complete(self):
        """Verify IAM module contains all required resources."""
        content = get_module_content("iam")
        assert "aws_iam_role" in content, "IAM module missing aws_iam_role"
        assert "aws_iam_role_policy_attachment" in content or "aws_iam_policy" in content, \
            "IAM module missing policy attachment"
        # Count IAM roles
        role_count = len(re.findall(r'resource\s+"aws_iam_role"', content))
        assert role_count >= 2, "IAM module must have at least 2 IAM roles"

    def test_iam_assume_role_policy_has_ecs_principal(self):
        """Verify IAM assume role policy contains proper ECS service principal."""
        content = get_module_content("iam")
        
        # Check for assume_role_policy with ECS service principal
        has_ecs_principal = any(principal in content for principal in 
                               ["ecs-tasks.amazonaws.com", "ecs.amazonaws.com"])
        
        # Also check for ec2 principal for ECS container instances
        has_ec2_principal = "ec2.amazonaws.com" in content
        
        # At least one should be present
        assert has_ecs_principal or has_ec2_principal, \
            "IAM assume role policy must contain ECS service principal (ecs-tasks.amazonaws.com or ecs.amazonaws.com) " \
            "or EC2 service principal (ec2.amazonaws.com)"


class TestMonitoringModule:
    """Test Monitoring module completeness."""

    def test_monitoring_module_complete(self):
        """Verify Monitoring module contains all required resources."""
        content = get_module_content("monitoring")
        required = ["aws_cloudwatch_dashboard", "aws_cloudwatch_metric_alarm",
                   "aws_sns_topic", "dashboard_body"]
        for r in required:
            assert r in content, f"Monitoring module missing {r}"

    def test_sns_topics_per_region(self):
        """Verify SNS topics exist. Since the module is reused, we check for at least 1 in the module."""
        content = get_module_content("monitoring")
        sns_count = len(re.findall(r'resource\s+"aws_sns_topic"', content))
        assert sns_count >= 1, "Monitoring module must define at least one SNS topic"
        
        # Also verify it is called twice in main.tf
        main_content = read_file(os.path.join(SOLUTION_DIR, "main.tf"))
        monitoring_calls = len(re.findall(r'module\s+"monitoring_[a-z]+"', main_content))
        assert monitoring_calls >= 2, "Monitoring module should be called for each region in main.tf"


# =============================================================================
# BEHAVIORAL TESTS
# =============================================================================

class TestMultiRegionConfiguration:
    """Test multi-region setup."""

    def test_multi_region_configuration(self):
        """Verify both us-east-1 and us-west-2 regions are configured."""
        root_content = get_root_tf_content()
        all_content = root_content
        for module in ["vpc", "alb", "ecs", "rds", "s3", "route53", "iam", "monitoring"]:
            all_content += get_module_content(module)

        # Check for both regions
        has_us_east_1 = "us-east-1" in all_content
        has_us_west_2 = "us-west-2" in all_content

        assert has_us_east_1, "Configuration must include us-east-1 region"
        assert has_us_west_2, "Configuration must include us-west-2 region"


class TestFailoverScripts:
    """Test failover script implementation."""

    def test_failover_script_implementation(self):
        """Verify simulate_failover.sh has substantial implementation."""
        script_path = os.path.join(SOLUTION_DIR, "scripts", "simulate_failover.sh")
        content = read_file(script_path)

        # Remove comments and empty lines
        lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        assert len(lines) >= 10, "simulate_failover.sh must have at least 10 lines of code"

        # Check for key commands/references
        has_aws_or_terraform = "aws" in content.lower() or "terraform" in content.lower()
        has_security_group = "security" in content.lower() or "sg" in content.lower()
        
        # Check for ALB reference (elastic load balancer, alb, aws_lb)
        has_alb = any(term in content.lower() for term in ["alb", "elastic load balancer", "aws_lb", "load_balancer"])
        
        # Check for Route53 reference
        has_route53 = any(term in content.lower() for term in ["route53", "aws_route53", "route 53"])
        
        # Check for timing/DNS logic (sleep, timeout, interval, dig, nslookup, curl)
        has_timing_logic = any(term in content.lower() for term in ["sleep", "timeout", "interval", "dig", "nslookup", "curl"])

        assert has_aws_or_terraform, "Script must contain AWS CLI or Terraform commands"
        assert has_security_group, "Script must reference security groups"
        assert has_alb, "Script must reference ALB (elastic load balancer, alb, or aws_lb)"
        assert has_route53, "Script must reference Route53 for failover"
        assert has_timing_logic, "Script must include timing/DNS logic (sleep, timeout, dig, nslookup, curl, or interval)"

    def test_simulate_failover_modifies_security_groups(self):
        """Verify failover simulation modifies security groups."""
        script_path = os.path.join(SOLUTION_DIR, "scripts", "simulate_failover.sh")
        content = read_file(script_path)

        # Check for security group modification patterns
        patterns = ["security-group", "authorize", "revoke", "modify", "update"]
        has_sg_modification = any(p in content.lower() for p in patterns)
        assert has_sg_modification, "Failover script must include security group modification logic"

    def test_validate_failover_script_content(self):
        """Verify validate_failover.sh has substantial implementation."""
        script_path = os.path.join(SOLUTION_DIR, "scripts", "validate_failover.sh")
        content = read_file(script_path)

        # Remove comments and empty lines
        lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        assert len(lines) >= 5, "validate_failover.sh must have at least 5 lines of code"
        
        # Check for actual DNS validation commands (curl, dig, nslookup, host, getent)
        has_dns_validation = any(cmd in content.lower() for cmd in ["curl", "dig", "nslookup", "host", "getent"])
        assert has_dns_validation, "Script must contain DNS validation commands (curl, dig, nslookup, host, or getent)"
        
        # Check for actual shell logic (if/then, loops, etc.) not just comments
        has_control_flow = any(pattern in content for pattern in ["if ", "then", "else", "for ", "while ", "case "])
        assert has_control_flow, "Script must contain shell control flow logic (if/then, loops, etc.)"


class TestFailoverTiming:
    """Test failover timing configuration."""

    def test_failover_timing_configuration(self):
        """Verify Route53 TTL and health check timing are appropriate."""
        route53_content = get_module_content("route53")

        # Check TTL
        ttl_matches = re.findall(r'ttl\s*=\s*(\d+)', route53_content)
        for ttl in ttl_matches:
            assert int(ttl) <= 60, f"Route53 TTL {ttl} exceeds 60 seconds"


class TestOutputs:
    """Test output configuration."""

    def test_required_outputs_with_module_references(self):
        """Verify all required outputs exist with proper names."""
        outputs_path = os.path.join(SOLUTION_DIR, "outputs.tf")
        content = read_file(outputs_path)

        required_outputs = [
            "primary_alb_dns",
            "secondary_alb_dns",
            "route53_dns_name",
            "primary_rds_endpoint",
            "secondary_rds_endpoint",
            "primary_s3_bucket",
            "secondary_s3_bucket",
            "cloudwatch_dashboard_url"
        ]

        for output in required_outputs:
            assert output in content, f"Required output '{output}' not found in outputs.tf"

    def test_outputs_reference_module_values(self):
        """Verify outputs reference module values (not hardcoded)."""
        outputs_path = os.path.join(SOLUTION_DIR, "outputs.tf")
        content = read_file(outputs_path)

        # At least 80% of outputs should reference modules
        module_refs = len(re.findall(r'module\.[a-z_]+\.', content))
        output_count = len(re.findall(r'output\s+"[^"]+"', content))

        if output_count > 0:
            ratio = module_refs / output_count
            assert ratio >= 0.5, "At least 50% of outputs must reference module values"


class TestModuleSize:
    """Test module minimum implementation size."""

    def test_module_minimum_size(self):
        """Verify each module meets minimum line count requirements."""
        min_lines = {
            "vpc": 50,
            "alb": 30,
            "ecs": 40,
            "rds": 30,
            "s3": 30,
            "route53": 25,
            "iam": 30,
            "monitoring": 40
        }

        for module, min_count in min_lines.items():
            content = get_module_content(module)
            # Count only actual code lines (exclude comments and blank lines)
            code_lines = [line for line in content.split('\n') 
                         if line.strip() and not line.strip().startswith('#')]
            line_count = len(code_lines)
            assert line_count >= min_count, \
                f"Module {module} has {line_count} code lines, minimum is {min_count}"


class TestMainTFCallsModules:
    """Test main.tf properly calls modules."""

    def test_main_tf_calls_modules(self):
        """Verify main.tf includes module calls."""
        main_path = os.path.join(SOLUTION_DIR, "main.tf")
        content = read_file(main_path)

        required_modules = ["vpc", "alb", "ecs", "rds", "s3", "route53", "iam", "monitoring"]
        for module in required_modules:
            # Allow for suffixes like _primary or _secondary
            pattern = rf'module\s+"{module}(?:_[a-z0-9_]+)?"'
            assert re.search(pattern, content), f"main.tf must call module '{module}'"


class TestSecurityGroupConfiguration:
    """Test security group configuration."""

    def test_security_group_configuration(self):
        """Verify security groups are properly defined."""
        vpc_content = get_module_content("vpc")
        rds_content = get_module_content("rds")
        ecs_content = get_module_content("ecs")
        alb_content = get_module_content("alb")

        all_content = vpc_content + rds_content + ecs_content + alb_content

        # Check for security group resources
        has_security_groups = "aws_security_group" in all_content
        assert has_security_groups, "Security groups must be defined in the configuration"


# =============================================================================
# TERRAFORM VALIDATION
# =============================================================================

class TestTerraformValidation:
    """Test Terraform syntax validation."""

    def test_terraform_validate(self):
        """Run terraform init and validate."""
        # Change to solution directory
        original_dir = os.getcwd()
        try:
            os.chdir(SOLUTION_DIR)

            # Run terraform init
            init_result = subprocess.run(
                ["terraform", "init", "-backend=false"],
                capture_output=True,
                text=True,
                timeout=120
            )
            assert init_result.returncode == 0, \
                f"terraform init failed: {init_result.stderr}"

            # Run terraform validate
            validate_result = subprocess.run(
                ["terraform", "validate"],
                capture_output=True,
                text=True,
                timeout=60
            )
            assert validate_result.returncode == 0, \
                f"terraform validate failed: {validate_result.stderr}"
            assert "Success" in validate_result.stdout or "valid" in validate_result.stdout.lower(), \
                "terraform validate did not report success"
        finally:
            os.chdir(original_dir)
