#!/bin/bash

# Oracle solution - Ensure solution files are in correct location
# Harbor framework expects files at /app/solution/

set -e

echo "Setting up Remote Cloud infrastructure solution..."

# The solution files should already be at /app/solution/ in test environment
# Just verify required files exist
REQUIRED_FILES=(
    "main.tf"
    "variables.tf"
    "outputs.tf"
    "terraform.tfvars"
)

SOLUTION_DIR="/app/solution"

# Check if we're already in the solution directory or need to find it
if [ -f "./main.tf" ]; then
    SOLUTION_DIR="."
elif [ ! -d "$SOLUTION_DIR" ]; then
    # Try to copy from current location
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    mkdir -p /app/solution
    cp -r "$SCRIPT_DIR"/* /app/solution/ 2>/dev/null || true
    SOLUTION_DIR="/app/solution"
fi

cd "$SOLUTION_DIR"

# Verify required files exist
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file not found: $file"
        exit 1
    fi
done

# Make scripts executable
if [ -d "scripts" ]; then
    chmod +x scripts/*.sh 2>/dev/null || true
fi

# Verify modules directory exists
if [ ! -d "modules" ]; then
    echo "ERROR: modules directory not found"
    exit 1
fi

echo "SUCCESS: Multi-region AWS infrastructure solution is ready"
echo "Solution location: $SOLUTION_DIR"
ls -la "$SOLUTION_DIR"
exit 0
