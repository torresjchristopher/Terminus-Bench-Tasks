FROM ubuntu:22.04

# Set working directory
WORKDIR /app

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install base dependencies
# We only need basic tools for the agent and verification of file existence.
# Compilers (Java, Go, Node) are NOT needed as we only generate CI YAMLs.
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    wget \
    unzip \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create example microservices structure
RUN mkdir -p /app/services

# Python microservice
RUN mkdir -p /app/services/user-api && \
    echo "flask==3.1.0" > /app/services/user-api/requirements.txt && \
    echo "requests==2.32.3" >> /app/services/user-api/requirements.txt && \
    printf 'def get_user():\n    return {"id": 1, "name": "Alice"}\n' > /app/services/user-api/app.py && \
    printf 'import pytest\nfrom app import get_user\n\ndef test_get_user():\n    """Test user retrieval"""\n    result = get_user()\n    assert result["id"] == 1\n    assert result["name"] == "Alice"\n' > /app/services/user-api/test_app.py

# Node.js microservice
RUN mkdir -p /app/services/payment-processor && \
    echo '{"name":"payment-processor","version":"1.0.0","scripts":{"test":"jest"},"dependencies":{"express":"4.21.2"},"devDependencies":{"jest":"29.7.0"}}' > /app/services/payment-processor/package.json && \
    printf 'function processPayment(amount) { return amount > 0; }\nmodule.exports = { processPayment };\n' > /app/services/payment-processor/index.js && \
    printf 'const { processPayment } = require("./index");\ntest("processes valid payment", () => { expect(processPayment(100)).toBe(true); });\n' > /app/services/payment-processor/index.test.js

# Go microservice
RUN mkdir -p /app/services/notification-service && \
    cd /app/services/notification-service && \
    printf 'module notification-service\n\ngo 1.18\n' > go.mod && \
    printf 'package main\n\nfunc SendNotification(msg string) bool {\n    return len(msg) > 0\n}\n' > main.go && \
    printf 'package main\n\nimport "testing"\n\nfunc TestSendNotification(t *testing.T) {\n    if !SendNotification("test") {\n        t.Error("Expected true")\n    }\n}\n' > main_test.go

# Java microservice
RUN mkdir -p /app/services/order-service/src/main/java/com/example && \
    mkdir -p /app/services/order-service/src/test/java/com/example && \
    echo '<?xml version="1.0"?><project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion><groupId>com.example</groupId><artifactId>order-service</artifactId><version>1.0.0</version><properties><maven.compiler.source>17</maven.compiler.source><maven.compiler.target>17</maven.compiler.target></properties><dependencies><dependency><groupId>junit</groupId><artifactId>junit</artifactId><version>4.13.2</version><scope>test</scope></dependency></dependencies></project>' > /app/services/order-service/pom.xml && \
    printf 'package com.example;\npublic class Order { public boolean isValid() { return true; } }\n' > /app/services/order-service/src/main/java/com/example/Order.java && \
    printf 'package com.example;\nimport org.junit.Test;\nimport static org.junit.Assert.*;\npublic class OrderTest { @Test public void testOrder() { assertTrue(new Order().isValid()); } }\n' > /app/services/order-service/src/test/java/com/example/OrderTest.java

# Create reports directory
RUN mkdir -p /app/reports

# Set permissions
RUN chmod -R 755 /app
