# Debug Multi-threaded C HTTP Server with GDB

A multi-threaded C HTTP server is experiencing sporadic segmentation faults under load. Your task is to use GDB to diagnose the issue, identify the root cause, and patch the code to fix the crash.

## The Problem

The HTTP server (`server.c`) handles concurrent requests using threads. Under load testing, the server crashes with a segmentation fault when processing HTTP requests with very long paths (500+ characters). You need to identify and fix the root cause.

## Your Task

Debug the server and fix the crash:

1. **Compile the server with debug symbols** - The server code is in `/app/server.c`. Compile it with the `-g` flag for debugging.

2. **Diagnose the crash (recommended approach using GDB)**:
   - Run the server under GDB
   - Trigger the crash using the provided load test script (`/app/load_test.sh`)
   - Use GDB commands like `backtrace`, `print`, `info locals` to examine the crash
   - Identify where and why the segfault occurs

   *Alternatively, you may identify the issue through code review and testing.*

3. **Fix the vulnerability**:
   - Once you've identified the root cause, patch `server.c` to fix it
   - Your fix must modify or remove any unbounded string operations
   - Ensure the fix handles paths of at least 500 characters without crashing
   - The server should either handle long paths gracefully or reject them properly

4. **Verify the fix**:
   - Recompile the patched server
   - Run the load test again to confirm the server no longer crashes

## Files Provided

- `/app/server.c` - Multi-threaded HTTP server source code (listens on port 8080)
- `/app/Makefile` - Build configuration
- `/app/load_test.sh` - Script to generate load and trigger the crash

## Success Criteria

The task is complete when:

1. You have patched `server.c` to fix the vulnerability
2. The server handles normal HTTP GET requests (e.g., `GET / HTTP/1.1`) successfully
3. The server handles HTTP requests with paths of at least 500 characters without crashing
4. The patched server binary exists at `/app/server` with debug symbols
