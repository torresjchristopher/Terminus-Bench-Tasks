#!/bin/bash

# Solution script: Debug and fix the server crash

echo "[*] Step 1: Identifying the vulnerability..."

# The vulnerability is in the parse_request function
# sscanf writes to 'path' without bounds checking

echo "[*] Step 2: Patching server.c to fix the vulnerability..."

# Apply the fix directly by editing server.c
# Replace the vulnerable sscanf line with a safer implementation
sed -i '/sscanf(request, "%s %s %s", method, path, version);/c\    char temp_path[BUFFER_SIZE];\
\
    \/\/ Parse with width limits and validate\
    if (sscanf(request, "%15s %1023s %15s", method, temp_path, version) == 3) {\
        if (strlen(temp_path) < MAX_PATH_LEN) {\
            strncpy(path, temp_path, MAX_PATH_LEN - 1);\
            path[MAX_PATH_LEN - 1] = '"'"'\\0'"'"';\
        } else {\
            strncpy(path, temp_path, MAX_PATH_LEN - 1);\
            path[MAX_PATH_LEN - 1] = '"'"'\\0'"'"';\
        }\
    }' /app/server.c

echo "[*] Step 3: Recompiling the fixed server..."
cd /app
make clean
make

echo "[*] Step 4: Verifying the fix..."
echo "[*] The patched server is now at /app/server"

# Verify the binary exists
if [ -f /app/server ]; then
    echo "[*] SUCCESS: Server patched and compiled successfully"
    exit 0
else
    echo "[*] ERROR: Failed to compile fixed server"
    exit 1
fi
