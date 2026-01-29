#!/bin/bash

set -e

# Get the directory where this script is located (tests directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing test dependencies..."

# Install Python (test dependency) - required for running pytest
if ! command -v python3 &> /dev/null || ! command -v pip3 &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip > /dev/null
fi

# Install Terraform (test dependency) - pinned version for reproducibility
echo "Installing Terraform 1.6.6..."
if ! command -v terraform &> /dev/null; then
    TERRAFORM_VERSION="1.6.6"
    wget -q "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
    unzip -q "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
    mv terraform /usr/local/bin/
    chmod +x /usr/local/bin/terraform
    rm "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
fi

# Install Python test dependencies (all versions pinned in requirements.txt)
# Requirements: pytest==7.4.3, boto3==1.34.18, requests==2.31.0, pyyaml==6.0.1
pip3 install -q -r "$SCRIPT_DIR/requirements.txt"

echo "Running tests..."

# Create logs directory
mkdir -p /logs/verifier

# Run pytest from tests directory
# The -rA flag shows summary of all test results
set +e
python3 -m pytest -rA "$SCRIPT_DIR/test_outputs.py" -v
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
