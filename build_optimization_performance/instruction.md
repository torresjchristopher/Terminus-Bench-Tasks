# Integrate sccache into CMake Build System

The task is to integrate sccache (a compiler caching tool) into an existing CMake-based C++ project to accelerate rebuild times. You will configure sccache with a local cache, perform builds to test cache effectiveness, and generate a performance report.

## Requirements

1. **Install sccache**: Install sccache version 0.8.2 in the container environment

2. **Configure CMake to use sccache**: Modify the `/app/CMakeLists.txt` file to wrap both the C and C++ compilers with sccache by setting BOTH of these CMake variables:
   - `CMAKE_C_COMPILER_LAUNCHER` must be set to reference `sccache` (the CMakeLists.txt should contain the literal string "sccache" on the same line as this variable)
   - `CMAKE_CXX_COMPILER_LAUNCHER` must be set to reference `sccache` (the CMakeLists.txt should contain the literal string "sccache" on the same line as this variable)
   - When CMake runs, these launcher settings will be recorded in the generated `/app/build/CMakeCache.txt` file, which must contain the string "sccache" to verify proper configuration

3. **Configure local cache directory**: Set up sccache to use a local disk cache in `/tmp/sccache` with a maximum size of 10 GB by setting the `SCCACHE_DIR` and `SCCACHE_CACHE_SIZE` environment variables

4. **Perform initial full build**:
   - Clear any existing cache directory at `/tmp/sccache` if it exists
   - Run a clean CMake build from `/app/build` directory (create the directory if needed)
   - The build must produce an executable at `/app/build/demo` (not `/app/demo`)
   - Record the build time and cache statistics

5. **Test cache effectiveness**:
   - Modify a single header file `/app/src/common.h` (add a comment or whitespace)
   - Clean the build artifacts (using `make clean` or similar, but keep the build directory and CMakeCache.txt)
   - Rebuild the project - sccache should reuse cached object files for source files not affected by the header change
   - Record the build time and cache statistics showing cache hits and improved performance

6. **Generate cache report**: Create a report file at `/app/cache_report.txt` with the following required format:
   - A statement indicating that the cache was cleared before the initial build (must include language such as "cleared", "clean", "empty", or "fresh" in reference to the `/tmp/sccache` cache directory)
   - A section labeled "Initial Build Statistics" containing sccache statistics and cache information from the initial build
   - A line containing "Initial Build Time:" followed by a numeric time value (between 0 and 3600 seconds) with "second" or "seconds" (e.g., "Initial Build Time: 5.2 seconds")
   - A section labeled "Rebuild Statistics" or "Rebuild.*Statistics" containing sccache statistics for the rebuild after the header modification
   - A line containing "Rebuild Build Time:" followed by a numeric time value (between 0 and 3600 seconds) with "second" or "seconds" (e.g., "Rebuild Build Time: 1.3 seconds")
   - A line containing "Improvement:" followed by a numeric percentage between -100 and 100 with "%" (e.g., "Improvement: 75.00%")
   - sccache statistics showing cache hits and misses for both builds (must include keywords: "cache", "hit", "miss", or "compile")
   - The rebuild statistics section must contain a line matching the pattern "Cache hits" or "hits" followed by a colon or equals sign and a numeric value of at least 1
   - The report must be at least 5 lines long and 100 characters in total

## Files

- Input: `/app/CMakeLists.txt` (to be modified)
- Input: `/app/src/` (C++ source files including: `main.cpp`, `common.h`, `math_helper.cpp`, `string_processor.cpp`)
- Input: `/app/src/common.h` (header file containing `StringProcessor` and/or `MathHelper` class declarations)
- Output: `/app/cache_report.txt` (performance report)
- Output: Modified `/app/CMakeLists.txt` with sccache integration

## Expected Outcome

After completing this task:

- The project source files (`main.cpp`, `common.h`, `math_helper.cpp`, `string_processor.cpp`) must be present in `/app/src/`
- The `/app/src/common.h` file must contain class declarations for `StringProcessor` and/or `MathHelper` (this is the actual demo project, not a substitute)
- CMakeLists.txt should have sccache configured as the compiler launcher (both CMAKE_C_COMPILER_LAUNCHER and CMAKE_CXX_COMPILER_LAUNCHER)
- The build should produce an executable named `demo` in `/app/build/demo` with executable permissions
- The build must produce actual compilation artifacts (`.o` object files and `.d` dependency files) in `/app/build/CMakeFiles/demo.dir/src/` - at least 2 object files must exist
- The `/tmp/sccache` cache directory should exist and contain at least 3 cached files with a total size of at least 10KB
- The `/app/src/common.h` file should be modified (a comment or whitespace added)
- The `/app/build` directory should be preserved across the initial build and rebuild phases
- The `/app/build/CMakeCache.txt` file should be preserved across the initial build and rebuild phases, still containing sccache and CMAKE_CXX_COMPILER configuration
- The cache_report.txt should include a statement indicating the cache was cleared before the initial build
- The cache_report.txt should contain TWO separate sections: "Initial Build Statistics" and "Rebuild Statistics"
- The "Initial Build Statistics" section must show cache misses (proving the cache was empty at start)
- The "Rebuild Statistics" section must show numeric cache hits with at least 2 cache hits (proving multiple source files were cached and reused)
- The cache_report.txt should demonstrate at least 15% build time improvement on the rebuild (not just -10%)
- The cache_report.txt must explicitly mention the header file modification (include "common.h", "header", or "modification" in the report)
- sccache statistics should show actual numeric cache hit data with at least 2 cache hits on the rebuild
- sccache version 0.8.2 should be installed and available
- sccache must be running as a server (verifiable via `sccache --show-stats` returning success)
- sccache should be configured with a 10GB cache size (verifiable via `sccache --show-stats`)
- The CMakeCache.txt file in `/app/build` should reference both sccache and CMAKE_CXX_COMPILER, proving it was used during the build of a C++ project
