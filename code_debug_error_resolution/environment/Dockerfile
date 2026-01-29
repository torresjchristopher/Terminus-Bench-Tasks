FROM debian:bookworm-slim

# Install build tools, GDB, and utilities
RUN apt-get update && apt-get install -y \
    gcc \
    gdb \
    make \
    curl \
    netcat-traditional \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the vulnerable server code and build files
COPY server.c /app/
COPY Makefile /app/
COPY load_test.sh /app/

# Build the server with debug symbols
RUN make

# The server binary will be at /app/server
