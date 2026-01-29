import subprocess
import time
import socket
from pathlib import Path


def test_server_binary_exists():
    """Test that the patched server binary exists."""
    server_path = Path("/app/server")
    assert server_path.exists(), f"Server binary not found at {server_path}"
    assert server_path.is_file(), f"{server_path} is not a file"


def test_server_compiled_with_debug_symbols():
    """Test that the server was compiled with debug symbols for GDB."""
    result = subprocess.run(
        ["file", "/app/server"],
        capture_output=True,
        text=True
    )
    assert "not stripped" in result.stdout, "Server binary should have debug symbols (not stripped)"


def test_server_source_patched():
    """Test that server.c has been patched to remove the vulnerable pattern."""
    server_source = Path("/app/server.c")
    assert server_source.exists(), "server.c not found"

    content = server_source.read_text()

    # Check that the original vulnerable sscanf pattern has been modified
    # The original pattern was: sscanf(request, "%s %s %s", method, path, version)
    # This should no longer exist with unbounded %s for the path
    lines = content.split('\n')

    # Look for the vulnerable pattern in parse_request function
    in_parse_request = False
    has_vulnerable_pattern = False

    for line in lines:
        if 'void parse_request' in line or 'parse_request(' in line:
            in_parse_request = True
        elif in_parse_request and (line.strip().startswith('void ') or line.strip().startswith('int ') or line.strip().startswith('char ')):
            # Exited parse_request function
            in_parse_request = False

        # Check for the exact vulnerable pattern within parse_request
        if in_parse_request:
            # The vulnerable line: sscanf(request, "%s %s %s", method, path, version);
            if 'sscanf' in line and '"%s %s %s"' in line:
                has_vulnerable_pattern = True
                break

    assert not has_vulnerable_pattern, "The vulnerable unbounded sscanf pattern should be removed or modified"


def test_server_handles_normal_requests():
    """Test that the patched server can handle normal HTTP requests."""
    # Start the server in background
    server_process = subprocess.Popen(
        ["/app/server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Give server time to start
        time.sleep(2)

        # Send a normal request
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect(("localhost", 8080))
            request = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
            sock.sendall(request)

            response = sock.recv(4096)
            assert len(response) > 0, "Should receive a response"
            assert b"HTTP/1.1 200 OK" in response, "Should receive HTTP 200 response"

        finally:
            sock.close()

    finally:
        # Clean up
        server_process.terminate()
        server_process.wait(timeout=5)


def test_server_survives_long_path_attack():
    """Test that the server doesn't crash when receiving very long paths."""
    # Start the server in background
    server_process = subprocess.Popen(
        ["/app/server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Give server time to start
        time.sleep(2)

        # Send multiple requests with very long paths
        for i in range(10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect(("localhost", 8080))

                # Create a path longer than MAX_PATH_LEN (256 bytes)
                long_path = "/" + "A" * 500
                request = f"GET {long_path} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode()

                sock.sendall(request)

                # Try to receive response (may be truncated or error, but shouldn't crash)
                response = sock.recv(4096)

                sock.close()

            except (ConnectionRefusedError, BrokenPipeError, ConnectionResetError):
                # If connection fails, server might have crashed
                assert False, f"Server appears to have crashed on request {i+1}"

            time.sleep(0.1)

        # Check if server is still running
        poll_result = server_process.poll()
        assert poll_result is None, "Server should still be running after long path attacks"

        # Try one more normal request to confirm server is responsive
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect(("localhost", 8080))
            request = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
            sock.sendall(request)
            response = sock.recv(4096)
            assert len(response) > 0, "Server should still respond after attack"

        finally:
            sock.close()

    finally:
        # Clean up
        server_process.terminate()
        server_process.wait(timeout=5)


def test_no_buffer_overflow_vulnerability():
    """Test that the buffer overflow vulnerability has been fixed."""
    server_source = Path("/app/server.c")
    content = server_source.read_text()

    # The original vulnerable pattern should not exist
    # The vulnerable line was: sscanf(request, "%s %s %s", method, path, version);
    vulnerable_pattern = 'sscanf(request, "%s %s %s"'

    assert vulnerable_pattern not in content, \
        "The vulnerable unbounded sscanf pattern must be fixed. The original pattern 'sscanf(request, \"%s %s %s\"' should not exist."


def test_proper_path_length_handling():
    """Test that paths just under and over the limit are handled correctly."""
    # Start the server in background
    server_process = subprocess.Popen(
        ["/app/server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Give server time to start
        time.sleep(2)

        # Test path just under typical limit (255 chars is common)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect(("localhost", 8080))
            valid_long_path = "/" + "a" * 254
            request = f"GET {valid_long_path} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode()
            sock.sendall(request)

            response = sock.recv(4096)
            # Should get some response (either 200 or 414, but not crash)
            assert len(response) > 0, "Server should respond to valid-length paths"

        finally:
            sock.close()

        # Test extremely long path (over any reasonable limit)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect(("localhost", 8080))
            oversized_path = "/" + "b" * 600
            request = f"GET {oversized_path} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode()
            sock.sendall(request)

            response = sock.recv(4096)
            # Should get response (either truncated/handled or 414 error)
            assert len(response) > 0, "Server should handle oversized paths without crashing"
            # Optionally check for 414 status code (proper error handling)
            # This is nice-to-have but not required

        finally:
            sock.close()

        # Verify server is still running
        poll_result = server_process.poll()
        assert poll_result is None, "Server should still be running after handling various path lengths"

    finally:
        # Clean up
        server_process.terminate()
        server_process.wait(timeout=5)
