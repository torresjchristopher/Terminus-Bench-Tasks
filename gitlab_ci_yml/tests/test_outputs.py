from pathlib import Path
import yaml
import re


def test_gitlab_ci_file_exists():
    """Test that .gitlab-ci.yml file exists at /app/.gitlab-ci.yml."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    assert gitlab_ci_path.exists(), f"File {gitlab_ci_path} does not exist"


def test_gitlab_ci_valid_yaml():
    """Test that .gitlab-ci.yml is valid YAML syntax."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    try:
        config = yaml.safe_load(content)
        assert config is not None, "YAML file is empty"
        assert isinstance(config, dict), "YAML root must be a dictionary"
    except yaml.YAMLError as e:
        assert False, f"Invalid YAML syntax: {e}"


def test_gitlab_ci_has_stages():
    """Test that .gitlab-ci.yml defines required stages with 'aggregate' as the final stage."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    config = yaml.safe_load(gitlab_ci_path.read_text())

    assert "stages" in config, "Missing 'stages' key in GitLab CI config"
    stages = config["stages"]
    assert isinstance(stages, list), "Stages must be a list"

    # Check for key stages (discover/trigger for child pipelines, aggregate for results)
    assert any("discover" in str(s).lower() or "trigger" in str(s).lower() for s in stages), \
        "Missing discovery or trigger stage for child pipelines"
    assert any("aggregate" in str(s).lower() for s in stages), \
        "Missing aggregate stage for collecting results"

    # Verify 'aggregate' is the FINAL stage as required by instructions
    last_stage = str(stages[-1]).lower()
    assert "aggregate" in last_stage, \
        f"The 'aggregate' stage must be the FINAL stage, but found '{stages[-1]}' as last stage"


def test_gitlab_ci_has_child_pipeline_triggers():
    """Test that .gitlab-ci.yml dynamically triggers child pipelines for services."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    config = yaml.safe_load(gitlab_ci_path.read_text())
    content = gitlab_ci_path.read_text()

    # Look for jobs that trigger child pipelines
    has_trigger_jobs = False
    for job_name, job_config in config.items():
        if isinstance(job_config, dict) and "trigger" in job_config:
            has_trigger_jobs = True
            break
        # Also check for 'extends' that might reference a trigger template
        if isinstance(job_config, dict) and "extends" in job_config:
            extended = job_config["extends"]
            if "trigger" in str(extended).lower():
                has_trigger_jobs = True
                break

    # Alternative: Check for trigger keyword in raw content
    if not has_trigger_jobs:
        has_trigger_jobs = "trigger:" in content

    assert has_trigger_jobs, "No child pipeline trigger jobs found in configuration"


def test_gitlab_ci_language_detection():
    """Test that configuration handles ALL four language types (Python, Node.js, Go, Java) as required."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Check for language detection logic or references to ALL required languages
    required_languages = ["python", "nodejs", "go", "java"]
    detected_languages = []

    for lang in required_languages:
        if lang in content.lower():
            detected_languages.append(lang)

    # Must handle ALL 4 languages as specified in instruction
    assert len(detected_languages) == 4, \
        f"Configuration must handle ALL 4 languages (Python, Node.js, Go, Java), found: {detected_languages}"

    for lang in required_languages:
        assert lang in detected_languages, f"Missing required language support: {lang}"


def test_gitlab_ci_artifact_specifications():
    """Test that configuration specifies proper artifact names and paths for test reports and security scans."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)

    # Check for JUnit report artifacts with proper YAML structure (reports: junit:)
    # Must be declared as `reports: junit:` in GitLab CI, not just keyword presence
    has_junit_reports_structure = False

    for job_name, job_config in config.items():
        if isinstance(job_config, dict) and "artifacts" in job_config:
            artifacts = job_config["artifacts"]
            if isinstance(artifacts, dict) and "reports" in artifacts:
                reports = artifacts["reports"]
                if isinstance(reports, dict) and "junit" in reports:
                    has_junit_reports_structure = True
                    break

    # Also check in raw content for the YAML structure pattern
    if not has_junit_reports_structure:
        has_junit_reports_structure = re.search(r'reports:\s*\n\s*junit:', content) is not None

    assert has_junit_reports_structure, \
        "JUnit reports must be declared with proper YAML structure 'reports: junit:' (not just keyword)"

    assert re.search(r"junit.*\.xml", content, re.IGNORECASE), \
        "Missing JUnit XML file path specification"

    # Check for security scan artifacts
    assert "security" in content.lower() or "vulnerability" in content.lower() or "scan" in content.lower(), \
        "Missing security/vulnerability scan configuration"

    # Check for proper artifact paths
    assert "reports/" in content, "Missing reports/ directory in artifact paths"


def test_gitlab_ci_dependency_caching():
    """Test that configuration implements per-language dependency caching."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)

    # Look for cache configuration
    has_cache = False

    # Check in jobs or in raw content
    if "cache" in content:
        has_cache = True

    for job_name, job_config in config.items():
        if isinstance(job_config, dict) and "cache" in job_config:
            has_cache = True
            cache_config = job_config["cache"]
            # Check for cache key and paths
            if isinstance(cache_config, dict):
                assert "key" in cache_config or "paths" in cache_config, \
                    f"Job {job_name} has cache but missing key or paths"

    assert has_cache, "No dependency caching configured"


def test_gitlab_ci_job_dependencies():
    """Test that jobs have proper dependencies (lint depends on build, test depends on lint, etc.)."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Check for dependency keywords
    assert "dependencies:" in content or "needs:" in content, \
        "Missing job dependencies configuration (dependencies: or needs:)"


def test_gitlab_ci_change_detection_rules():
    """Test that configuration includes rules for file change detection."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Check for rules with changes
    assert "rules:" in content, "Missing rules configuration for conditional job execution"
    assert "changes:" in content, "Missing changes: keyword for file-based triggering"

    # Check for service path patterns
    assert "services/" in content, "Missing services/ path in change detection rules"


def test_gitlab_ci_aggregate_results_job():
    """Test that there is an 'aggregate-results' job (exact name) to collect all artifacts."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    config = yaml.safe_load(gitlab_ci_path.read_text())

    # Check for exact job name 'aggregate-results' as specified in instructions
    assert "aggregate-results" in config, \
        "Missing exact job name 'aggregate-results' - instructions require this specific name"

    job_config = config["aggregate-results"]
    assert isinstance(job_config, dict), "aggregate-results must be a job configuration dict"

    # Check that it has artifacts configuration or script section
    assert "artifacts" in job_config or "script" in job_config, \
        "aggregate-results job should have artifacts or script section"


def test_services_directory_exists():
    """Test that services directory exists with microservices."""
    services_path = Path("/app/services")
    assert services_path.exists(), "Services directory /app/services does not exist"
    assert services_path.is_dir(), "/app/services is not a directory"

    # Check for at least one service
    services = list(services_path.iterdir())
    assert len(services) > 0, "No microservices found in /app/services/"


def test_microservices_have_language_files():
    """Test that microservices have proper language detection files."""
    services_path = Path("/app/services")

    for service_dir in services_path.iterdir():
        if service_dir.is_dir():
            # Check for at least one language marker file
            has_language_file = (
                (service_dir / "requirements.txt").exists() or
                (service_dir / "pyproject.toml").exists() or
                (service_dir / "package.json").exists() or
                (service_dir / "go.mod").exists() or
                (service_dir / "pom.xml").exists() or
                (service_dir / "build.gradle").exists()
            )
            assert has_language_file, \
                f"Service {service_dir.name} missing language detection file (requirements.txt, package.json, go.mod, pom.xml, etc.)"


def test_gitlab_ci_artifact_expiry():
    """Test that artifacts have proper expiration settings."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Check for expire_in configuration
    assert "expire_in:" in content or "expire_in :" in content, \
        "Missing expire_in configuration for artifacts"

    # Check for 30 days expiry as specified in requirements
    assert "30 days" in content or "30days" in content, \
        "Security scan artifacts should have 30 days expiry"


def test_artifact_naming_conventions():
    """Test that artifacts follow exact naming conventions: {service-name}-test-reports and {service-name}-security-scan."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Check for artifact name patterns
    # Must contain references to service-name in artifact names
    assert re.search(r'name:\s*["\\]?\$?\{?service[_-]?name\}?-test-reports', content, re.IGNORECASE), \
        "Missing artifact naming pattern '{service-name}-test-reports'"

    assert re.search(r'name:\s*["\\]?\$?\{?service[_-]?name\}?-security-scan', content, re.IGNORECASE), \
        "Missing artifact naming pattern '{service-name}-security-scan'"


def test_artifact_paths_exact():
    """Test that artifact paths match exact specifications: reports/junit-{service-name}.xml and reports/security-{service-name}.json."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Check for JUnit XML path pattern
    assert re.search(r'reports/junit-\\?\$?\{?service[_-]?name\}?\.xml', content, re.IGNORECASE), \
        "Missing JUnit artifact path pattern 'reports/junit-{service-name}.xml'"

    # Check for security scan JSON path pattern
    assert re.search(r'reports/security-\\?\$?\{?service[_-]?name\}?\.json', content, re.IGNORECASE), \
        "Missing security scan artifact path pattern 'reports/security-{service-name}.json'"


def test_cache_keys_include_dependency_hash():
    """Test that cache keys include language, CI_COMMIT_REF_SLUG, and dependency file hash as required."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Must include language in cache key (python, nodejs, go, java, or ${language})
    has_language = re.search(r'key:.*?(python|nodejs|go|java|\${?language\}?)', content, re.IGNORECASE | re.DOTALL)
    assert has_language, "Cache key must include language identifier"

    # Must include $CI_COMMIT_REF_SLUG or equivalent branch/ref identifier
    has_ref_slug = re.search(r'\${?CI_COMMIT_REF_SLUG\}?', content, re.IGNORECASE)
    assert has_ref_slug, "Cache key must include $CI_COMMIT_REF_SLUG for branch-specific caching"

    # Must include dependency file hash
    hash_patterns = [
        r'checksum.*requirements\.txt',
        r'checksum.*package\.json',
        r'checksum.*go\.(mod|sum)',
        r'checksum.*pom\.xml',
        r'md5sum.*requirements\.txt',
        r'md5sum.*package(-lock)?\.json',
        r'md5sum.*go\.(mod|sum)',
        r'md5sum.*pom\.xml',
        r'sha\d+sum.*requirements\.txt',
        r'sha\d+sum.*package(-lock)?\.json',
        r'sha\d+sum.*go\.(mod|sum)',
        r'sha\d+sum.*pom\.xml',
        r'files:.*requirements\.txt',
        r'files:.*package\.json',
        r'files:.*go\.mod',
        r'files:.*pom\.xml'
    ]

    has_hash = False
    for pattern in hash_patterns:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            has_hash = True
            break

    assert has_hash, \
        "Cache key must include dependency file hash (checksum/md5sum/sha256sum of requirements.txt, package.json, go.mod, or pom.xml)"

    # Verify per-language cache paths are specified
    cache_paths = {
        'python': r'\.cache/pip|/pip',
        'nodejs': r'node_modules',
        'go': r'go/pkg/mod',
        'java': r'\.m2/repository|m2/repository'
    }

    for lang, path_pattern in cache_paths.items():
        if lang in content.lower():
            assert re.search(path_pattern, content, re.IGNORECASE), \
                f"Missing cache path for {lang} (expected pattern: {path_pattern})"


def test_job_dependency_ordering():
    """Test that job dependencies follow exact ordering: lint depends on build, test depends on lint, vuln-scan depends on build."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Check for lint depending on build
    assert re.search(r'lint.*?(?:dependencies|needs):.*?build', content, re.DOTALL | re.IGNORECASE) or \
           re.search(r'(?:dependencies|needs):.*?build.*?lint', content, re.DOTALL | re.IGNORECASE), \
        "Lint job must depend on build job"

    # Check for test depending on lint
    assert re.search(r'test.*?(?:dependencies|needs):.*?lint', content, re.DOTALL | re.IGNORECASE) or \
           re.search(r'(?:dependencies|needs):.*?lint.*?test', content, re.DOTALL | re.IGNORECASE), \
        "Test job must depend on lint job"

    # Check for vulnerability-scan depending on build
    assert re.search(r'vulnerability.*?(?:dependencies|needs):.*?build', content, re.DOTALL | re.IGNORECASE) or \
           re.search(r'scan.*?(?:dependencies|needs):.*?build', content, re.DOTALL | re.IGNORECASE), \
        "Vulnerability scan job must depend on build job"


def test_path_based_triggering():
    """Test that child pipelines only trigger on specific service path changes."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Check for service-specific path patterns in rules
    assert re.search(r'changes:.*?services/\$?{?service[_-]?name}?/\*\*/\*', content, re.IGNORECASE | re.DOTALL) or \
           re.search(r'changes:.*?$SERVICE_PATH/\*\*/\*', content, re.IGNORECASE | re.DOTALL), \
        "Child pipelines must have path-based change detection for specific service directories"

    # Check for .gitlab-ci.yml change detection
    assert re.search(r'changes:.*\.gitlab-ci\.yml', content, re.IGNORECASE | re.DOTALL), \
        "Child pipelines must trigger when .gitlab-ci.yml changes"


def test_aggregate_job_completeness():
    """Test that aggregate-results job depends on ALL child pipeline trigger jobs and aggregates artifacts."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)

    # Must have exact job name 'aggregate-results'
    assert "aggregate-results" in config, \
        "Must have exact job name 'aggregate-results' as specified in instructions"

    aggregate_job = config["aggregate-results"]
    aggregate_job_name = "aggregate-results"

    assert isinstance(aggregate_job, dict), "aggregate-results must be a job configuration"

    # Find all trigger jobs (child pipeline triggers) at top level
    trigger_jobs = []
    for job_name, job_config in config.items():
        if isinstance(job_config, dict):
            if "trigger" in job_config or ("extends" in job_config and "trigger" in str(job_config.get("extends", "")).lower()):
                trigger_jobs.append(job_name)

    # Check if dynamic includes are being used (triggers generated from discover job)
    uses_dynamic_includes = False
    if "include" in config:
        includes = config["include"]
        if isinstance(includes, list):
            for inc in includes:
                if isinstance(inc, dict) and "artifact" in inc and "job" in inc:
                    if "discover" in str(inc.get("job", "")).lower():
                        uses_dynamic_includes = True
                        break
        elif isinstance(includes, dict):
            if "artifact" in includes and "discover" in str(includes.get("job", "")).lower():
                uses_dynamic_includes = True

    # Aggregate job must have needs or dependencies
    has_needs = "needs" in aggregate_job or "dependencies" in aggregate_job
    assert has_needs, \
        f"Aggregate job '{aggregate_job_name}' must use 'needs:' or 'dependencies:' to ensure proper execution order"

    job_str = str(aggregate_job)

    if trigger_jobs:
        # If trigger jobs are at top level, aggregate must depend on them
        depends_on_triggers = any(trigger_job in job_str for trigger_job in trigger_jobs)
        assert depends_on_triggers, \
            f"Aggregate job must depend on child pipeline trigger jobs: {trigger_jobs}"
    elif uses_dynamic_includes:
        # If using dynamic includes, aggregate must depend on discover-services
        # (which generates all triggers) to ensure proper ordering
        depends_on_discover = "discover" in job_str.lower()
        assert depends_on_discover, \
            "When using dynamic includes for triggers, aggregate-results must depend on discover-services job"

    # Check that it has script section that downloads/lists artifacts
    assert "script" in aggregate_job, "Aggregate job must have script section"

    # Check for artifact downloading or listing commands
    script_content = " ".join(aggregate_job["script"]) if isinstance(aggregate_job["script"], list) else str(aggregate_job["script"])

    assert "artifact" in script_content.lower() or "download" in script_content.lower() or "ls" in script_content.lower() or "find" in script_content.lower(), \
        "Aggregate job must download or list artifacts"


def test_child_pipeline_strategy_depend():
    """Test that child pipeline triggers use strategy: depend to wait for completion."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)

    # Find trigger jobs that should have strategy: depend
    trigger_jobs = []
    for job_name, job_config in config.items():
        if isinstance(job_config, dict) and "trigger" in job_config:
            trigger_jobs.append((job_name, job_config))

    # Check for strategy: depend in trigger configuration
    has_strategy_depend = False

    for job_name, job_config in trigger_jobs:
        trigger_config = job_config.get("trigger", {})
        if isinstance(trigger_config, dict):
            if trigger_config.get("strategy") == "depend":
                has_strategy_depend = True
                break

    # Also check for template with strategy: depend
    if not has_strategy_depend:
        has_strategy_depend = re.search(r'strategy:\s*depend', content, re.IGNORECASE) is not None

    assert has_strategy_depend, \
        "Child pipeline triggers must use 'strategy: depend' to wait for child pipeline completion"


def test_generated_child_pipeline_files():
    """Test that child pipeline YAML files are actually generated via auto-discovery (anti-cheating measure)."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    config = yaml.safe_load(gitlab_ci_path.read_text())
    content = gitlab_ci_path.read_text()

    # Check that discover job exists and generates child pipeline files
    assert "discover-services" in config, "Must have 'discover-services' job that generates child pipeline files"

    # Find the discover job
    discover_job = config["discover-services"]

    # Check that discover job has script that scans services directory
    assert "script" in discover_job, "Discover job must have script section"
    script_content = " ".join(discover_job["script"]) if isinstance(discover_job["script"], list) else str(discover_job["script"])

    # Verify it scans /app/services or services/ directory
    assert "services" in script_content.lower(), \
        "Discover job script must scan the services/ directory"

    # Verify it has logic to iterate/loop through directories (for, while, find, ls, etc.)
    has_iteration = any(keyword in script_content.lower() for keyword in ["for ", "while ", "find ", "ls -", "each"])
    assert has_iteration, \
        "Discover job must iterate through service directories (use for/while/find/ls)"

    # ANTI-CHEAT: Verify it actually WRITES child pipeline files (cat >, echo >, tee, >, printf >)
    has_file_write = any(write_op in script_content.lower() for write_op in ["cat >", "cat>", "echo >", "echo>", "tee ", "> .gitlab-ci", "printf "])
    assert has_file_write, \
        "Discover job must actually WRITE child pipeline files (use cat >, echo >, tee, or printf)"

    # ANTI-CHEAT: Verify the file write includes the service name variable (not hardcoded)
    has_dynamic_filename = any(var in script_content for var in ["${service", "$service", "$(service"])
    assert has_dynamic_filename, \
        "Child pipeline filenames must be dynamically generated using service name variable (e.g., .gitlab-ci-${service_name}.yml)"

    # Check for child pipeline file references (e.g., .gitlab-ci-{service}.yml)
    assert re.search(r'\.gitlab-ci-.*\.yml', content), \
        "Must reference generated child pipeline files (e.g., .gitlab-ci-{service}.yml)"

    # Check that child pipeline files are created as artifacts
    if "artifacts" in discover_job:
        artifacts = discover_job["artifacts"]
        if isinstance(artifacts, dict) and "paths" in artifacts:
            paths = artifacts["paths"]
            assert any(".gitlab-ci" in str(p) and ".yml" in str(p) for p in paths), \
                "Discover job must create child pipeline YAML files as artifacts"

    # Verify language detection logic exists in discover job
    has_language_detection = any(lang_file in script_content for lang_file in
                                 ["requirements.txt", "package.json", "go.mod", "pom.xml"])
    assert has_language_detection, \
        "Discover job must include language detection logic (check for requirements.txt, package.json, go.mod, pom.xml)"

    # ANTI-CHEAT: Verify all 4 languages are handled in the discover job
    languages_in_discover = sum(1 for lang in ["python", "nodejs", "go", "java"] if lang in script_content.lower())
    assert languages_in_discover >= 4, \
        f"Discover job must handle all 4 languages (Python, Node.js, Go, Java), found {languages_in_discover}"

    # Verify alternate lock/build files are checked (as per instructions)
    assert "pyproject.toml" in script_content, "Discover job must check for pyproject.toml (Python alternate)"
    assert "build.gradle" in script_content, "Discover job must check for build.gradle (Java alternate)"


def test_path_changes_exclusivity():
    """Test that jobs ONLY trigger on specific path changes (not always)."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)

    # Find all jobs with trigger or extends (child pipeline related)
    child_pipeline_jobs = []
    for job_name, job_config in config.items():
        if isinstance(job_config, dict):
            if "trigger" in job_config or ("extends" in job_config and "trigger" in str(job_config.get("extends", "")).lower()):
                child_pipeline_jobs.append((job_name, job_config))

    # Each child pipeline trigger job must have rules with changes
    for job_name, job_config in child_pipeline_jobs:
        # Check if this job or its template has rules with changes
        if "rules" in job_config:
            rules = job_config["rules"]
            has_changes = any(
                isinstance(rule, dict) and "changes" in rule
                for rule in rules
            )
            assert has_changes, \
                f"Job {job_name} must have 'rules: changes:' to trigger ONLY on specific path changes"

    # Also validate that rules contain service-specific paths
    assert re.search(r'changes:.*services/', content, re.IGNORECASE | re.DOTALL), \
        "Rules must include service-specific path patterns (services/{service}/)"

    # ANTI-CHEAT: Verify trigger jobs use service-specific variables (not hardcoded paths)
    # Look for template that uses ${SERVICE} or similar variable
    has_template = any(".trigger-template" in str(k) or "trigger" in str(k) and "extends" in str(v)
                      for k, v in config.items() if isinstance(v, dict))

    if has_template:
        # Find template
        template_job = None
        for job_name, job_config in config.items():
            if ".trigger-template" in str(job_name).lower() and isinstance(job_config, dict):
                template_job = job_config
                break

        if template_job and "rules" in template_job:
            rules_str = str(template_job["rules"])
            # Must use variable like ${SERVICE}, $SERVICE, or similar
            assert "${SERVICE}" in rules_str or "$SERVICE" in rules_str or "$(SERVICE" in rules_str, \
                "Template rules must use SERVICE variable for dynamic path matching"


def test_discover_job_name_exact():
    """Test that the discovery job is named exactly 'discover-services'."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    config = yaml.safe_load(gitlab_ci_path.read_text())

    assert "discover-services" in config, \
        "Must have exact job name 'discover-services' as specified in instructions"


def test_dynamic_trigger_jobs_per_service():
    """Test that trigger jobs are dynamically generated via include artifact, not hardcoded."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)

    # The main config should use dynamic includes for triggers
    # Check for include directive that references artifact from discover job
    has_dynamic_include = False

    if "include" in config:
        includes = config["include"]
        if isinstance(includes, list):
            for inc in includes:
                if isinstance(inc, dict):
                    if "artifact" in inc and "job" in inc:
                        if inc.get("job") == "discover-services":
                            has_dynamic_include = True
                            break
        elif isinstance(includes, dict):
            if "artifact" in includes and "job" in includes:
                if includes.get("job") == "discover-services":
                    has_dynamic_include = True

    # Also check raw content for include with artifact pattern
    if not has_dynamic_include:
        # Fallback check for raw text if YAML parsing misses it, but enforce exact name
        has_dynamic_include = (
            "include:" in content and
            "artifact:" in content and
            "job: discover-services" in content
        )

    assert has_dynamic_include, \
        (
            "Triggers must be dynamically generated via 'include: artifact:' from 'discover-services' job. "
            "Static/hardcoded trigger jobs are not allowed."
        )

    # Verify discover job generates trigger file as artifact
    discover_job = config.get("discover-services")
    if discover_job:
        assert "artifacts" in discover_job, \
            "Discover job must output artifacts including trigger definitions"
        artifacts = discover_job["artifacts"]
        if isinstance(artifacts, dict) and "paths" in artifacts:
            paths_str = str(artifacts["paths"])
            assert "trigger" in paths_str.lower() or ".yml" in paths_str, \
                "Discover job must output trigger YAML file as artifact"


def test_security_scan_artifact_expiry_exact():
    """Test that security scan artifacts have exactly 30 days expiry (not just any 30 days string)."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()

    # Find security/vulnerability scan sections
    security_sections = re.findall(r'vulnerability-scan.*?(?=\n[a-zA-Z]|\Z)', content, re.DOTALL | re.IGNORECASE)
    security_sections.extend(re.findall(r'scan.*?(?=\n[a-zA-Z]|\Z)', content, re.DOTALL | re.IGNORECASE))

    # At least one security scan section must exist
    assert len(security_sections) > 0, "Must have vulnerability scan job sections"

    # Each security scan section with artifacts must have 30 days expiry
    for section in security_sections:
        if "artifacts:" in section and ("security" in section.lower() or "scan" in section.lower()):
            # Only enforce if it looks like a job definition, not a script line
            if "expire_in:" in section:
                assert re.search(r'expire_in:\s*["\\]?30\s*days["\\]?', section, re.IGNORECASE), \
                    "Security scan artifacts must have 'expire_in: 30 days' (exact specification)"


def test_aggregate_downloads_child_artifacts():
    """Test that aggregate-results job actually downloads/collects artifacts from child pipelines."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    config = yaml.safe_load(gitlab_ci_path.read_text())

    # Must have exact job name 'aggregate-results'
    assert "aggregate-results" in config, \
        "Must have exact job name 'aggregate-results' as specified in instructions"

    aggregate_job = config["aggregate-results"]
    assert isinstance(aggregate_job, dict), "aggregate-results must be a job configuration"

    # Get script content
    assert "script" in aggregate_job, "Aggregate job must have script section"
    script_content = " ".join(aggregate_job["script"]) if isinstance(aggregate_job["script"], list) else str(aggregate_job["script"])

    # ANTI-CHEAT: Must actually search for/copy/collect report files
    # Looking for commands that collect junit and security reports
    has_junit_collection = "junit" in script_content.lower() and (
        "find" in script_content.lower() or
        "cp" in script_content.lower() or
        "mv" in script_content.lower() or
        "collect" in script_content.lower()
    )
    assert has_junit_collection, \
        "Aggregate job must collect JUnit reports (use find/cp/mv commands with junit pattern)"

    has_security_collection = "security" in script_content.lower() and (
        "find" in script_content.lower() or
        "cp" in script_content.lower() or
        "mv" in script_content.lower() or
        "collect" in script_content.lower()
    )
    assert has_security_collection, \
        "Aggregate job must collect security scan reports (use find/cp/mv commands with security pattern)"

    # Must reference reports/ directory where child pipelines save artifacts
    assert "reports/" in script_content or "reports" in script_content, \
        "Aggregate job must reference reports/ directory where child artifacts are stored"


def test_exact_dynamic_triggers_include():
    """Test that main .gitlab-ci.yml uses EXACT include snippet: 'artifact: dynamic-triggers.yml'."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)
    
    # Must have include directive
    assert "include" in config, "Missing 'include' directive in .gitlab-ci.yml"
    
    includes = config["include"]
    if not isinstance(includes, list):
        includes = [includes]
    
    # Must find the exact dynamic-triggers.yml artifact include
    found_dynamic_triggers = False
    for inc in includes:
        if isinstance(inc, dict):
            if inc.get("artifact") == "dynamic-triggers.yml" and "job" in inc:
                found_dynamic_triggers = True
                break
    
    assert found_dynamic_triggers, \
        "Must use exact include: 'artifact: dynamic-triggers.yml' from discover job. " \
        "This is the required dynamic trigger mechanism."


def test_exact_cache_key_structure():
    """Test that cache keys follow EXACT structure: prefix: ${language}-$CI_COMMIT_REF_SLUG with files: directive."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)
    
    # Find at least one job with proper cache key structure
    has_proper_cache_structure = False
    
    for job_name, job_config in config.items():
        if isinstance(job_config, dict) and "cache" in job_config:
            cache = job_config["cache"]
            if isinstance(cache, dict) and "key" in cache:
                key_config = cache["key"]
                if isinstance(key_config, dict):
                    # Must have prefix with language and $CI_COMMIT_REF_SLUG
                    if "prefix" in key_config:
                        prefix = str(key_config.get("prefix", ""))
                        if "$CI_COMMIT_REF_SLUG" in prefix or "${CI_COMMIT_REF_SLUG}" in prefix:
                            # Must also have files: directive for dependency hash
                            if "files" in key_config:
                                files = key_config["files"]
                                if isinstance(files, list) and len(files) > 0:
                                    has_proper_cache_structure = True
                                    break
    
    assert has_proper_cache_structure, \
        "Cache keys must follow exact structure: " \
        "key: { prefix: '${language}-$CI_COMMIT_REF_SLUG', files: ['services/${service_name}/...'] }. " \
        "The 'files:' directive is required for dependency hash computation."


def test_exact_artifact_paths_strict():
    """Test that artifact paths EXACTLY match: reports/junit-${service_name}.xml and reports/security-${service_name}.json."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    
    # Artifact paths are generated in CHILD pipelines, not the parent
    # So we check the SCRIPT content that generates these paths
    # Look for the discover-services job script that writes child pipeline files
    
    # Must contain evidence that exact artifact paths are being generated in child pipelines
    # Match patterns like: reports/junit-${service_name}.xml or /app/reports/junit-${service_name}.xml
    junit_path_pattern = r'reports/junit-.*service.*name.*\.xml'
    security_path_pattern = r'reports/security-.*service.*name.*\.json'
    
    junit_found = re.search(junit_path_pattern, content, re.IGNORECASE) is not None
    security_found = re.search(security_path_pattern, content, re.IGNORECASE) is not None
    
    assert junit_found, \
        "Must have exact artifact path pattern: 'reports/junit-${service_name}.xml' (or with variable substitution) " \
        "in the script that generates child pipeline YAMLs"
    assert security_found, \
        "Must have exact artifact path pattern: 'reports/security-${service_name}.json' (or with variable substitution) " \
        "in the script that generates child pipeline YAMLs"


def test_dollar_sign_escaping_in_generated_files():
    """Test that dollar signs are properly escaped when generating child pipeline YAML files."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)
    
    # Find discover job
    discover_job = config.get("discover-services")
    assert discover_job is not None, "Must have discover-services job"
    assert "script" in discover_job, "Discover job must have script"
    
    script_content = " ".join(discover_job["script"]) if isinstance(discover_job["script"], list) else str(discover_job["script"])
    
    # When writing child pipeline files with cat/echo/printf, dollar signs must be escaped
    # Valid patterns: \$VAR, \\$VAR in quotes, or using single quotes with heredoc
    
    # Check for evidence of proper escaping
    has_escaped_vars = False
    
    # Single quotes with heredoc (safest method)
    if "cat" in script_content.lower() and "'EOF'" in script_content:
        has_escaped_vars = True
    
    # Backslash escaping patterns
    if re.search(r'\\?\$[A-Z_]', script_content) and ("echo" in script_content.lower() or "printf" in script_content.lower()):
        has_escaped_vars = True
    
    # Double backslash escaping
    if re.search(r'\\\\\$', script_content):
        has_escaped_vars = True
    
    # If it writes child pipeline files, must have proper escaping
    if "gitlab-ci-" in script_content.lower() and ".yml" in script_content.lower():
        # This is generating YAML files, so escaping is critical
        # Verify file actually contains escaped variables (anti-cheat)
        assert has_escaped_vars, \
            "When generating child pipeline YAML files, dollar signs MUST be properly escaped " \
            "to prevent variable expansion. Use: cat << 'EOF' ... EOF, or \\$VAR with printf/echo."


def test_discover_job_generates_dynamic_triggers_file():
    """Test that discover job EXPLICITLY generates dynamic-triggers.yml file."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    content = gitlab_ci_path.read_text()
    config = yaml.safe_load(content)
    
    # Find discover job
    discover_job = config.get("discover-services")
    assert discover_job is not None, "Must have discover-services job"
    assert "script" in discover_job, "Discover job must have script"
    
    script_content = " ".join(discover_job["script"]) if isinstance(discover_job["script"], list) else str(discover_job["script"])
    
    # Must explicitly write dynamic-triggers.yml file (not just mention it)
    has_write_triggers = any(pattern in script_content.lower() 
                            for pattern in ["dynamic-triggers", "trigger"])
    assert has_write_triggers, \
        "Discover job script must explicitly generate and write dynamic-triggers.yml"
    
    # Must output as artifact
    assert "artifacts" in discover_job, "Discover job must have artifacts"
    artifacts = discover_job["artifacts"]
    if isinstance(artifacts, dict) and "paths" in artifacts:
        paths_str = str(artifacts["paths"])
        assert "dynamic-triggers" in paths_str.lower() or ".yml" in paths_str, \
            "Discover job must output dynamic-triggers.yml as artifact"


def test_generated_yaml_syntax_validation():
    """ANTI-CHEAT: Verify that generated child pipeline YAML files are syntactically valid (not fake/dummy strings)."""
    # The test validates that IF child pipeline files are generated, they must be valid YAML
    # This prevents agents from writing fake YAML that just contains placeholder strings
    
    # Check if any .gitlab-ci-*.yml files exist (which would be generated by discover job)
    app_dir = Path("/app")
    generated_yml_files = list(app_dir.glob(".gitlab-ci-*.yml"))
    
    if generated_yml_files:
        # If files are generated, they MUST be valid YAML (anti-cheat measure)
        for yml_file in generated_yml_files:
            try:
                content = yml_file.read_text()
                config = yaml.safe_load(content)
                assert config is not None, f"{yml_file.name}: Generated YAML file is empty"
                assert isinstance(config, dict), f"{yml_file.name}: Generated YAML must be a dictionary at root level"
                
                # Validate that it has required job sections (not just placeholder text)
                assert len(config) > 0, f"{yml_file.name}: Generated YAML has no jobs defined"
                
                # Must have at least one pipeline job (build, test, scan, etc.)
                valid_job_keywords = ["build", "test", "lint", "scan", "stage", "script", "trigger"]
                has_job_structure = any(
                    keyword in str(config).lower() 
                    for keyword in valid_job_keywords
                )
                assert has_job_structure, f"{yml_file.name}: Generated YAML lacks job structure (missing build/test/scan jobs)"
                
            except yaml.YAMLError as e:
                assert False, f"Generated YAML file {yml_file.name} has invalid syntax: {e} (anti-cheat check failed)"
    
    # If no generated files but services exist, discover job may not be working properly
    # This is checked by test_generated_child_pipeline_files, so just noting here


def test_discover_job_output_format():
    """ANTI-CHEAT: Validate that discover job script outputs proper shell/GitLab CI format (not hardcoded fake output)."""
    gitlab_ci_path = Path("/app/.gitlab-ci.yml")
    config = yaml.safe_load(gitlab_ci_path.read_text())
    
    # Find discover job
    assert "discover-services" in config, "Must have 'discover-services' job"
    discover_job = config["discover-services"]
    
    # Script must contain actual shell logic for YAML generation
    script_content = " ".join(discover_job["script"]) if isinstance(discover_job["script"], list) else str(discover_job["script"])
    
    # Check for shell output redirection (actual file writing, not fake echo)
    has_output_redirection = any(
        pattern in script_content 
        for pattern in [">>", "> ", ".gitlab-ci-", "cat <<", "printf", "echo"]
    )
    assert has_output_redirection, \
        "Discover job must use shell output redirection (>, >>) to write YAML files"
    
    # Check for nested YAML structure generation (indentation, colons, etc.)
    # Real YAML generation has these patterns
    yaml_structure_patterns = ["stages:", "script:", "image:", "cache:", "trigger:", "rules:"]
    has_yaml_structure = sum(1 for pattern in yaml_structure_patterns if pattern in script_content) >= 3
    assert has_yaml_structure, \
        "Discover job script must generate proper YAML structure (stages:, script:, cache:, trigger:, rules:)"
