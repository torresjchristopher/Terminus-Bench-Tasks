FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install build essentials and dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    g++ \
    wget \
    curl \
    time \
    bc \
    && rm -rf /var/lib/apt/lists/*

# Install sccache 0.8.2
RUN wget https://github.com/mozilla/sccache/releases/download/v0.8.2/sccache-v0.8.2-x86_64-unknown-linux-musl.tar.gz && \
    tar -xzf sccache-v0.8.2-x86_64-unknown-linux-musl.tar.gz && \
    mv sccache-v0.8.2-x86_64-unknown-linux-musl/sccache /usr/local/bin/ && \
    chmod +x /usr/local/bin/sccache && \
    rm -rf sccache-v0.8.2-x86_64-unknown-linux-musl.tar.gz sccache-v0.8.2-x86_64-unknown-linux-musl

# Set working directory
WORKDIR /app

# Copy the C++ project files
COPY project/ /app/
