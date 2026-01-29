FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install only base system dependencies required for the task itself
# Note: Python, Terraform, and test tools are installed by test.sh
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    git \
    jq \
    gnupg \
    software-properties-common \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up AWS credentials directory (will be populated at runtime)
RUN mkdir -p ~/.aws

CMD ["/bin/bash"]
