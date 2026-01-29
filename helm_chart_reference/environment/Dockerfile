FROM ubuntu:22.04

WORKDIR /app

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install all dependencies in a single RUN command to optimize layer caching
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    ca-certificates \
    gnupg \
    python3 \
    python3-pip \
    jq \
    bash \
    lsb-release \
    apt-transport-https \
    software-properties-common \
    && \
    # Install Docker CLI
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    # Install kubectl
    curl -LO "https://dl.k8s.io/release/v1.28.4/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl && \
    # Install kind
    curl -Lo /usr/local/bin/kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 && \
    chmod +x /usr/local/bin/kind && \
    # Install Helm
    curl -LO https://get.helm.sh/helm-v3.13.2-linux-amd64.tar.gz && \
    tar -zxvf helm-v3.13.2-linux-amd64.tar.gz && \
    mv linux-amd64/helm /usr/local/bin/helm && \
    rm -rf helm-v3.13.2-linux-amd64.tar.gz linux-amd64 && \
    # Install cosign
    curl -Lo /usr/local/bin/cosign https://github.com/sigstore/cosign/releases/download/v2.2.1/cosign-linux-amd64 && \
    chmod +x /usr/local/bin/cosign && \
    # Install yq
    wget https://github.com/mikefarah/yq/releases/download/v4.35.2/yq_linux_amd64 -O /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq && \
    # Clean up
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:${PATH}"
