# Create Dynamic GitLab CI Pipeline for Microservices

Create a `.gitlab-ci.yml` file at `/app/.gitlab-ci.yml` that dynamically triggers child pipelines for each microservice in the `services/` directory.

## Important: Variable Types in This Task

This task involves THREE types of variables you must distinguish:
1. **Shell variables** (${service_name}, ${language}, ${image}): Used in the discover-services script and expanded by the shell
2. **GitLab CI variables** ($CI_COMMIT_REF_SLUG, $CI_PIPELINE_ID): Used in generated YAML files, interpreted by GitLab
3. **YAML variables** (${service_name}): Placeholders in the generated child pipeline YAML files that GitLab CI will substitute

When writing generated YAML files (`.gitlab-ci-${service_name}.yml`), use backslash escaping for GitLab variables: `\$CI_COMMIT_REF_SLUG` so they appear as `$CI_COMMIT_REF_SLUG` in the generated file.

## Requirements

### 1. Dynamic Child Pipeline Triggering

- The parent pipeline must have a job named `discover-services` (**exact name required**) that automatically scans all subdirectories in `/app/services/` (e.g., `services/user-api`, `services/payment-processor`, `services/notification-service`)
- The `discover-services` job must:
  - Iterate through service directories using shell loops (e.g., `for`, `while`, `find`)
  - Generate a separate child pipeline YAML file for each microservice named `.gitlab-ci-${service_name}.yml` (using the service directory name as the variable)
  - **Explicitly write these files** using `cat >`, `echo >`, `printf`, or `tee` within the script
  - Output the generated YAML files as artifacts
  - Also generate a `dynamic-triggers.yml` file containing trigger job definitions for each service
- **Critical**: The main `.gitlab-ci.yml` must use dynamic includes to load the generated triggers using this **exact structure**:
  ```yaml
  include:
    - artifact: dynamic-triggers.yml
      job: discover-services
  ```
  *(Note: The `job:` field must be exactly `discover-services`)*

- Child pipeline triggers must use `strategy: depend` to ensure the parent waits for child completion
- Child pipelines must ONLY trigger when files in that specific service directory change (path-based rules)

### 2. Language Detection and Jobs

Each child pipeline must detect the programming language based on the presence of these files. **You must use these exact lowercase string identifiers for the language:**

- **python**: presence of `requirements.txt` or `pyproject.toml`
- **nodejs**: presence of `package.json`
- **go**: presence of `go.mod`
- **java**: presence of `pom.xml` or `build.gradle`

Based on the detected language, the child pipeline must run these jobs in order:

1. **build** - Build/compile the service
2. **lint** - Run language-specific linters
3. **test** - Run unit tests and generate JUnit XML reports
4. **vulnerability-scan** - Scan dependencies for security vulnerabilities

### 3. Dependency Caching

Implement per-language dependency caching:

- **Python**: Cache `~/.cache/pip`
- **Node.js**: Cache `node_modules/`
- **Go**: Cache `~/go/pkg/mod`
- **Java**: Cache `~/.m2/repository`

**Critical Cache Key Requirement**: Cache keys MUST be unique per language and dependency file content. Use this exact structure:
```yaml
cache:
  key:
    prefix: ${language}-$CI_COMMIT_REF_SLUG
    files:
      - services/${service_name}/${dep_file}
  paths:
    - ${cache_path}
```

The key MUST include:
1. The language identifier (e.g., `python`, `nodejs`, `go`, `java`)
2. The branch name (`$CI_COMMIT_REF_SLUG`)
3. **A hash of the dependency file** using the `files:` directive (e.g., `files: ["services/${service_name}/requirements.txt"]`)

**Cache Key Structure is Mandatory**: This exact structure is required for proper caching. GitLab CI's `files:` directive automatically computes a hash of the specified files, which ensures the cache is invalidated when dependencies change. This is non-negotiable for reproducible builds.

**CRITICAL YAML GENERATION RULE - Dollar Sign Escaping**:
When you programmatically write the child pipeline YAML files (`.gitlab-ci-${service_name}.yml`), GitLab CI variables like `$CI_COMMIT_REF_SLUG` must be written with a backslash escape: `\$CI_COMMIT_REF_SLUG` in the output file. This ensures GitLab interprets the dollar sign as a GitLab variable reference, NOT a shell variable.

**Example - How to Write It**:
If you're using `printf`, `echo`, or `cat` to write YAML files, write:
```
printf "prefix: ${language}-\$CI_COMMIT_REF_SLUG\n" >> ".gitlab-ci-${service_name}.yml"
```

The backslash before `$CI_COMMIT_REF_SLUG` prevents the shell from expanding it and ensures it appears as `$CI_COMMIT_REF_SLUG` in the written YAML file (which is what GitLab needs).

### 3.5. YAML Generation Best Practices (Critical for Validity)

When programmatically generating YAML files through shell scripts, follow these rules to ensure valid YAML syntax:

**1. Use Heredoc (cat << 'EOF') for Multiline Content**:
```bash
cat > ".gitlab-ci-${service_name}.yml" << 'EOF'
stages:
  - build
  - test

build:
  stage: build
  script:
    - echo "Building..."
EOF
```
Heredoc with single quotes (`'EOF'`) preserves literal content and prevents shell expansion. This is the most reliable method for YAML generation.

**2. Use printf with Proper Escaping for Single-Line Additions**:
```bash
printf "  - service: %s\n" "$service_name" >> ".gitlab-ci-${service_name}.yml"
printf "    prefix: %s-\$CI_COMMIT_REF_SLUG\n" "$language" >> ".gitlab-ci-${service_name}.yml"
```
Use `\$` (backslash escape) for GitLab variables so they appear as `$VAR` in the file.

**3. Avoid EOF Marker Issues**:
- **DO**: Use `cat << 'EOF'` (with single quotes) to prevent expansions within the heredoc block
- **DO NOT**: Use unquoted EOF or double-quoted `"EOF"` unless you specifically need shell expansion
- **DO NOT**: Put shell variables directly in heredoc blocks without proper escaping

**4. YAML Indentation Must Be Consistent**:
- Use **2-space indentation** throughout (GitLab CI standard)
- **DO NOT** mix spaces and tabs
- **DO NOT** use 4-space indentation (common Python mistake)

**5. Quote String Values Containing Special Characters**:
```yaml
script:
  - "echo 'Building service ${service_name}'"
  - "prefix: '${language}-$CI_COMMIT_REF_SLUG'"
```

**6. Validate Generated YAML Before Output**:
The discover-services script should output generated YAML files. These files will be parsed by GitLab CI, so they MUST be valid YAML:
- All colons (`:`) must be followed by space or newline
- All lists must have `-` followed by space
- Indentation must be consistent and use spaces only
- No trailing whitespace on lines

### 4. Artifact Requirements

**CRITICAL**: These artifact configurations are for **CHILD pipeline jobs** (generated dynamically in `.gitlab-ci-${service_name}.yml` files), NOT the parent `.gitlab-ci.yml`. The discover-services job must generate child pipeline files that include these exact artifact specifications.

#### Test Reports (JUnit XML format)

Each service's test job (in the child pipeline) must produce a JUnit XML report with the **exact** following configuration:

```yaml
artifacts:
  name: ${service_name}-test-reports
  paths:
    - reports/junit-${service_name}.xml
  reports:
    junit:
      - reports/junit-${service_name}.xml
```

- **Artifact name**: MUST match pattern `${service_name}-test-reports` (with variable substitution)
- **Path**: MUST contain `reports/junit-${service_name}.xml` (exact directory and filename pattern)
- **Structure**: MUST use nested `reports: junit:` structure as shown - do not use `artifacts: reports:` alone
- **Type**: MUST use nested `reports: junit:` structure

#### Security Scan Reports (JSON format)

Each service's vulnerability-scan job must produce a JSON report with the **exact** following configuration:

```yaml
artifacts:
  name: ${service_name}-security-scan
  paths:
    - reports/security-${service_name}.json
  expire_in: 30 days
```

- **Artifact name**: MUST match pattern `${service_name}-security-scan` (with variable substitution)
- **Path**: MUST contain `reports/security-${service_name}.json` (exact directory and filename pattern with .json extension)
- **Expiry**: MUST explicitly state `expire_in: 30 days` (exact spacing and wording)

### 5. Parent Pipeline Aggregation

The parent pipeline must have a final stage named `aggregate` that:

- Contains a job named exactly `aggregate-results` (this exact name is required)
- This `aggregate` stage must be the FINAL (last) stage in the `stages:` list

The `aggregate-results` job MUST:

1. **Use `needs:` directive**: Since you're using dynamic includes from `discover-services`, you MUST specify:
   ```yaml
   needs:
     - discover-services
   ```

2. **Have a `script:` section** that collects artifacts from child pipelines:
   ```yaml
   script:
     - echo "Collecting JUnit reports..."
     - find . -name "junit-*.xml" -type f -exec cp {} ./collected-reports/ \;
     - echo "Collecting security scan reports..."
     - find . -name "security-*.json" -type f -exec cp {} ./collected-reports/ \;
     - ls -la ./collected-reports/
   ```

3. **Aggregate artifacts**: Use `find`, `cp`, or `mv` commands to collect both:
   - JUnit XML reports (pattern: `junit-*.xml`)
   - Security scan reports (pattern: `security-*.json`)

### 6. Job Dependencies

Enforce proper job ordering within each child pipeline:

- `lint` depends on `build`
- `test` depends on `lint`
- `vulnerability-scan` depends on `build`

### 7. File Change Detection

Each trigger job in `dynamic-triggers.yml` must use GitLab CI rules to only run when specific paths change. Use this exact structure:

```yaml
trigger-${service_name}:
  stage: trigger
  trigger:
    include:
      - artifact: .gitlab-ci-${service_name}.yml
        job: discover-services
    strategy: depend
  rules:
    - changes:
        - services/${service_name}/**/*
        - .gitlab-ci.yml
```

The rules MUST specify:
- Files in `services/${service_name}/**/*` (using the service name variable)
- The `.gitlab-ci.yml` file itself

## Output Requirements

Create the following file:

- `/app/.gitlab-ci.yml` - The main GitLab CI configuration

### Required Structure

Your `.gitlab-ci.yml` MUST have this basic structure:

```yaml
stages:
  - discover
  - trigger
  - aggregate    # MUST be the last stage

discover-services:
  stage: discover
  script:
    # ... discovery and file generation logic ...
  artifacts:
    paths:
      - .gitlab-ci-*.yml
      - dynamic-triggers.yml

aggregate-results:
  stage: aggregate
  needs:
    - discover-services
  script:
    # ... artifact collection logic ...

include:
  - artifact: dynamic-triggers.yml
    job: discover-services
```

The configuration must be valid YAML and follow GitLab CI syntax for:

- Dynamic child pipelines
- Parent-child pipeline relationships
- Artifact passing
- Dependency caching
- Path-based change detection rules

**Implementation Note**: When using shell commands (like `printf` or `echo`) to generate child pipeline YAML files, **you MUST properly escape dollar signs** so the **literal** variable name is written to the file.

### Escaping Examples (CRITICAL)

**Incorrect (Variable expands immediately -> Invalid YAML):**
```bash
# Shell expands $CI_COMMIT_REF_SLUG to empty string (or current shell value)
printf "  ref: $CI_COMMIT_REF_SLUG\n" >> child.yml
# Result in file: "  ref: " (Syntax Error if value expected)
```

**Correct (Literal variable written to file -> Valid YAML):**
```bash
# METHOD 1: Single quotes with Heredoc (Recommended)
# The single quotes around 'EOF' prevent shell expansion inside the block
cat >> child.yml << 'EOF'
  ref: $CI_COMMIT_REF_SLUG
EOF

# METHOD 2: Double backslash with printf
# You need \\$ to produce a single literal $ in the file
printf "  ref: \\$CI_COMMIT_REF_SLUG\n" >> child.yml

# METHOD 3: Single backslash with echo (Not recommended if quotes used)
echo "  ref: \$CI_COMMIT_REF_SLUG" >> child.yml
```

## Validation

Your solution will be tested against a repository with multiple microservices in different languages. The tests will verify:

- Child pipelines are generated correctly
- Language detection works
- Artifact paths and names match specifications
- Caching keys are properly configured
- Dependencies between jobs are correct
- Change detection rules are properly set
