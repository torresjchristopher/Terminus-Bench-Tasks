# Terminus-Bench-Tasks

Library of tasks approved for the Terminus Bench project, a project which builds verified tasks like these to train frontier A.I. models.

## Overview

This repository contains 6 benchmark tasks designed to evaluate and train advanced AI models. Each task is organized in its own directory with instructions, environment setup, tests, and solutions.

## Tasks

### 1. **Build Optimization Performance**
Optimize a C++ build system for improved performance and compilation speed. This task involves analyzing CMake configurations and applying optimization techniques.

- **Location**: `build_optimization_performance/`
- **Type**: C++ Build Optimization
- **Key Components**: Dockerfile, CMakeLists, source code, tests

### 2. **Code Debug Error Resolution**
Debug and resolve errors in a multi-threaded server implementation. This task requires identifying and fixing runtime issues in C code.

- **Location**: `code_debug_error_resolution/`
- **Type**: C Code Debugging
- **Key Components**: Server implementation, load testing, error resolution

### 3. **Debian Production Task**
Create a production-ready Debian package with proper packaging rules, patches, and documentation following Debian standards.

- **Location**: `debian_production_task/`
- **Type**: Debian Packaging
- **Key Components**: debian/ directory, patches, Makefile configuration

### 4. **GitLab CI/CD Configuration**
Configure a proper GitLab CI/CD pipeline with appropriate build, test, and deployment stages.

- **Location**: `gitlab_ci_yml/`
- **Type**: CI/CD Pipeline
- **Key Components**: .gitlab-ci.yml configuration, Docker environment

### 5. **Helm Chart Reference**
Implement a complete Helm chart for Kubernetes deployment with proper templates, values, and security policies.

- **Location**: `helm_chart_reference/`
- **Type**: Kubernetes/Helm
- **Key Components**: Helm charts, Kubernetes manifests, deployment scripts

### 6. **Remote Cloud Infrastructure**
Design and implement a complete AWS infrastructure using Terraform with multiple modules for high availability and disaster recovery.

- **Location**: `remote_cloud/`
- **Type**: Infrastructure as Code (Terraform)
- **Key Components**: VPC, ECS, RDS, ALB, monitoring, Route53 configurations

## Task Structure

Each task directory follows this structure:
```
task-name/
├── instruction.md          # Task description and requirements
├── task.toml              # Task metadata and configuration
├── environment/           # Docker setup and project files
├── solution/              # Reference solution implementation
├── tests/                 # Test suite and validation scripts
└── [additional files]     # Task-specific resources
```

## Getting Started

1. Navigate to any task directory
2. Read the `instruction.md` for task requirements
3. Review the `task.toml` for metadata and configuration
4. Set up the environment using the Dockerfile or provided scripts
5. Review the solution in the `solution/` directory
6. Run tests to validate implementation

## Testing

Each task includes a test suite to validate solutions. Tests are typically run using:
```bash
cd [task-name]/tests
./test.sh
```

## Technologies Used

- **C/C++**: Build optimization and debugging
- **Debian Packaging**: Package management and distribution
- **Docker**: Containerization
- **GitLab CI/CD**: Continuous integration and deployment
- **Kubernetes & Helm**: Container orchestration
- **Terraform**: Infrastructure as code (AWS)
- **Python**: Testing and automation scripts

## Project Purpose

These tasks are designed to:
- Train and evaluate frontier A.I. models on complex, real-world scenarios
- Provide verified benchmarks for AI capability assessment
- Cover DevOps, infrastructure, code quality, and system administration domains

## License

[Add appropriate license information]

## Contributing

For contributions or questions about specific tasks, please refer to the individual task documentation.
