FROM python:3.12-slim-bookworm

# Install Debian package building tools required for dpkg-buildpackage
RUN apt-get update && apt-get install -y \
    build-essential \
    debhelper \
    devscripts \
    dpkg-dev \
    curl \
    file \
    && rm -rf /var/lib/apt/lists/*

# Create the /build directory as specified in the task instructions
WORKDIR /build

# Copy source files for building the Debian package
# Files are in the same directory as Dockerfile (environment/)
COPY hello.c /build/
COPY Makefile /build/
COPY hello.1 /build/
COPY debian/ /build/debian/
