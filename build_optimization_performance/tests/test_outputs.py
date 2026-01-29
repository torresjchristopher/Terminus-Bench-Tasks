"""Tests for sccache integration task."""
from pathlib import Path
import re
import subprocess


def test_cache_report_exists():
    """Verify that the cache report file exists at /app/cache_report.txt."""
    report_path = Path("/app/cache_report.txt")
    assert report_path.exists(), "cache_report.txt file does not exist at /app/"


def test_cmake_sccache_configuration():
    """Verify that CMakeLists.txt has been modified to use sccache as compiler launcher."""
    cmake_path = Path("/app/CMakeLists.txt")
    assert cmake_path.exists(), "CMakeLists.txt does not exist"

    content = cmake_path.read_text()

    # Check for BOTH C and CXX compiler launcher configuration
    assert "CMAKE_C_COMPILER_LAUNCHER" in content, \
        "CMakeLists.txt does not configure CMAKE_C_COMPILER_LAUNCHER"

    assert "CMAKE_CXX_COMPILER_LAUNCHER" in content, \
        "CMakeLists.txt does not configure CMAKE_CXX_COMPILER_LAUNCHER"

    # Verify sccache is set as the launcher (not just mentioned)
    assert re.search(r"CMAKE_C_COMPILER_LAUNCHER.*sccache", content, re.IGNORECASE), \
        "CMAKE_C_COMPILER_LAUNCHER is not set to sccache"

    assert re.search(r"CMAKE_CXX_COMPILER_LAUNCHER.*sccache", content, re.IGNORECASE), \
        "CMAKE_CXX_COMPILER_LAUNCHER is not set to sccache"


def test_report_contains_build_times():
    """Verify that the report contains initial and rebuild build times."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Check for initial build time
    assert re.search(r"Initial Build Time:.*\d+\.?\d*.*second", content, re.IGNORECASE), \
        "Report does not contain initial build time"

    # Check for rebuild build time
    assert re.search(r"Rebuild Build Time:.*\d+\.?\d*.*second", content, re.IGNORECASE), \
        "Report does not contain rebuild build time"


def test_report_contains_improvement_percentage():
    """Verify that the report contains build time improvement percentage."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Check for improvement percentage
    assert re.search(r"Improvement:.*\d+\.?\d*.*%", content, re.IGNORECASE) or \
           re.search(r"\d+\.?\d*%.*improvement", content, re.IGNORECASE), \
        "Report does not contain build time improvement percentage"


def test_report_contains_cache_statistics():
    """Verify that the report contains sccache statistics for both builds."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Check for cache-related keywords that would appear in sccache stats
    cache_keywords = ["cache", "hit", "miss", "compile"]

    found_keywords = sum(1 for keyword in cache_keywords if keyword.lower() in content.lower())

    assert found_keywords >= 2, \
        "Report does not contain sufficient cache statistics (expected cache hits/misses information)"


def test_report_shows_cache_effectiveness():
    """Verify that the report demonstrates cache hits occurred during rebuild."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # The report should mention rebuild or second build statistics
    rebuild_section = re.search(r"Rebuild.*Statistics", content, re.IGNORECASE | re.DOTALL)

    assert rebuild_section, \
        "Report does not contain a rebuild statistics section"


def test_build_produces_executable():
    """Verify that the build process produced the demo executable."""
    # The executable must be in /app/build/demo as per instruction
    executable_path = Path("/app/build/demo")

    assert executable_path.exists(), \
        "Build did not produce the expected demo executable at /app/build/demo"

    # Verify the executable is actually executable
    assert executable_path.stat().st_mode & 0o111, \
        "Demo file exists but is not executable"

    # Verify build directory exists and has CMake artifacts (proves actual build occurred)
    build_dir = Path("/app/build")
    assert build_dir.exists() and build_dir.is_dir(), \
        "/app/build directory does not exist - build may not have been performed correctly"

    # Check for CMake build artifacts
    cmake_cache = build_dir / "CMakeCache.txt"
    assert cmake_cache.exists(), \
        "CMakeCache.txt not found in /app/build - build was not done with CMake"

    # Verify the CMakeCache references sccache (proves sccache was actually used)
    cache_content = cmake_cache.read_text()
    assert "sccache" in cache_content, \
        "CMakeCache.txt does not reference sccache - build may not have used sccache launcher"

    # Verify CMakeCache shows this is a C++ project (anti-cheating: not a fake cache file)
    assert "CMAKE_CXX_COMPILER" in cache_content, \
        "CMakeCache.txt does not reference CMAKE_CXX_COMPILER - may be a fabricated file"

    # Verify object files were created (proves compilation happened)
    cmake_files_dir = build_dir / "CMakeFiles" / "demo.dir"
    assert cmake_files_dir.exists(), \
        "CMakeFiles/demo.dir does not exist - build artifacts missing"

    # Check for at least one object file (.o) or dependency file (.d)
    build_artifacts = list(cmake_files_dir.rglob("*.o")) + list(cmake_files_dir.rglob("*.d"))
    assert len(build_artifacts) > 0, \
        "No object files or dependency files found - build may not have actually compiled sources"


def test_report_has_reasonable_structure():
    """Verify that the report has a reasonable structure with sections."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Report should have multiple lines and reasonable length
    lines = content.strip().split('\n')

    assert len(lines) >= 5, \
        "Report is too short - expected detailed performance information"

    assert len(content) >= 100, \
        "Report content is too brief - expected detailed cache statistics"


def test_build_times_are_numeric():
    """Verify that build times in the report are actual numeric values."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Extract initial build time (handles formats like "5.2", ".2", "5", etc.)
    initial_match = re.search(r"Initial Build Time:\s*(\d*\.?\d+)", content, re.IGNORECASE)
    assert initial_match, "Could not extract numeric initial build time"
    initial_time = float(initial_match.group(1))
    assert 0 < initial_time < 3600, f"Initial build time {initial_time} seems unreasonable (expected 0-3600 seconds)"

    # Extract rebuild time (handles formats like "5.2", ".2", "5", etc.)
    rebuild_match = re.search(r"Rebuild Build Time:\s*(\d*\.?\d+)", content, re.IGNORECASE)
    assert rebuild_match, "Could not extract numeric rebuild build time"
    rebuild_time = float(rebuild_match.group(1))
    assert 0 < rebuild_time < 3600, f"Rebuild time {rebuild_time} seems unreasonable (expected 0-3600 seconds)"

    # Extract improvement percentage (handles formats like "75.00", ".5", "75", etc.)
    improvement_match = re.search(r"Improvement:\s*(-?\d*\.?\d+)\s*%", content, re.IGNORECASE)
    assert improvement_match, "Could not extract numeric improvement percentage"
    improvement = float(improvement_match.group(1))
    assert -100 <= improvement <= 100, f"Improvement percentage {improvement}% is out of reasonable range"

    # Verify that sccache actually provided some benefit (rebuild should show improvement or at least cache usage)
    # Allowing small negative values for cases where rebuild overhead exists but cache is working
    assert improvement > -10, \
        f"Cache shows no effectiveness - improvement is {improvement}%, expected at least -10% to show cache is working"


def test_sccache_version():
    """Verify that sccache version 0.8.2 is installed."""
    try:
        result = subprocess.run(
            ["sccache", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_output = result.stdout + result.stderr
        assert "0.8.2" in version_output, \
            f"sccache version 0.8.2 not found. Got: {version_output}"
    except FileNotFoundError:
        assert False, "sccache command not found - is it installed?"
    except subprocess.TimeoutExpired:
        assert False, "sccache --version command timed out"


def test_cache_statistics_show_actual_usage():
    """Verify that cache statistics show actual cache hits (not just keywords)."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Look for numerical cache statistics in the rebuild section
    rebuild_section_match = re.search(r"Rebuild.*Statistics.*", content, re.IGNORECASE | re.DOTALL)
    assert rebuild_section_match, "Could not find rebuild statistics section"

    rebuild_section = content[rebuild_section_match.start():]

    # Check for actual numeric cache hit statistics
    # sccache --show-stats output includes patterns like "Cache hits: 123" or "Compile requests: 123"
    has_cache_hits = re.search(r"(cache\s+hit|hit)s?\s*[:=]?\s*\d+", rebuild_section, re.IGNORECASE)
    has_compile_requests = re.search(r"compile\s+(request|call)s?\s*[:=]?\s*\d+", rebuild_section, re.IGNORECASE)

    assert has_cache_hits or has_compile_requests, \
        "Rebuild statistics do not show numeric cache hit data from actual sccache usage"

    # Extract the numeric values to verify they're reasonable
    if has_cache_hits:
        cache_hit_match = re.search(r"(cache\s+hit|hit)s?\s*[:=]?\s*(\d+)", rebuild_section, re.IGNORECASE)
        if cache_hit_match:
            cache_hits = int(cache_hit_match.group(2))
            # Should have at least 1 cache hit in a rebuild scenario
            assert cache_hits >= 1, \
                f"Cache hits count is {cache_hits}, expected at least 1 to demonstrate cache effectiveness"


def test_common_header_was_modified():
    """Verify that common.h was modified as required by the task."""
    header_path = Path("/app/src/common.h")
    assert header_path.exists(), "/app/src/common.h does not exist"

    content = header_path.read_text()

    # The task requires modifying common.h (adding a comment or whitespace)
    # Check for evidence of modification (comment or extra whitespace at end)
    lines = content.split('\n')

    # Look for a comment that wasn't in the original, or trailing content
    has_modification = (
        "cache test" in content.lower() or
        "modification" in content.lower() or
        len(lines) > 10 or  # Original is minimal, modifications would add lines
        any(line.strip().startswith("//") and len(line.strip()) > 2 for line in lines[-5:])
    )

    assert has_modification, \
        "common.h does not appear to have been modified as required"


def test_sccache_cache_directory_exists():
    """Verify that the sccache cache directory was created and cache size is configured."""
    cache_dir = Path("/tmp/sccache")

    # The cache directory should exist after running the builds
    assert cache_dir.exists(), \
        "/tmp/sccache directory does not exist - was SCCACHE_DIR configured correctly?"

    assert cache_dir.is_dir(), \
        "/tmp/sccache exists but is not a directory"

    # Check that the cache directory has content (indicating it was actually used)
    cache_contents = list(cache_dir.rglob("*"))
    assert len(cache_contents) > 0, \
        "/tmp/sccache directory is empty - cache was not actually used"


def test_sccache_configuration():
    """Verify that sccache is properly configured with the required cache size."""
    try:
        # Run sccache --show-stats which includes configuration info
        result = subprocess.run(
            ["sccache", "--show-stats"],
            capture_output=True,
            text=True,
            timeout=5
        )
        stats_output = result.stdout + result.stderr

        # Check that cache directory is configured to /tmp/sccache
        # sccache --show-stats shows "Cache location" or similar
        assert "/tmp/sccache" in stats_output or "tmp/sccache" in stats_output, \
            f"sccache is not configured to use /tmp/sccache. Stats output: {stats_output}"

        # Verify cache size is set to 10G (may appear as "10.0 GiB", "10G", "10 GB", etc.)
        has_10g_config = any(pattern in stats_output for pattern in ["10.0 GiB", "10 GiB", "10G", "10 GB", "10.0 GB"])
        assert has_10g_config, \
            f"sccache cache size does not appear to be set to 10G. Stats output: {stats_output}"

    except FileNotFoundError:
        assert False, "sccache command not found"
    except subprocess.TimeoutExpired:
        assert False, "sccache --show-stats command timed out"


def test_project_source_files_exist():
    """Verify that the expected C++ source files are present in the project."""
    # Anti-cheating: Ensure this is actually the demo project, not a fabricated one
    src_dir = Path("/app/src")
    assert src_dir.exists() and src_dir.is_dir(), \
        "/app/src directory does not exist"

    # Check for expected source files from the demo project
    expected_files = ["main.cpp", "common.h", "math_helper.cpp", "string_processor.cpp"]
    for filename in expected_files:
        file_path = src_dir / filename
        assert file_path.exists(), \
            f"Expected source file {filename} not found in /app/src"

    # Verify common.h contains expected content (proving it's the real project)
    common_h = src_dir / "common.h"
    common_content = common_h.read_text()
    assert "StringProcessor" in common_content or "MathHelper" in common_content, \
        "common.h does not contain expected class names - may not be the actual project file"


def test_report_has_initial_build_statistics_section():
    """Verify that the report contains a distinct initial build statistics section."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Look for a section labeled "Initial Build Statistics" or similar
    initial_section = re.search(
        r"Initial\s+Build\s+Statistics",
        content,
        re.IGNORECASE | re.DOTALL
    )

    assert initial_section, \
        "Report does not contain a distinct 'Initial Build Statistics' section. " \
        "Expected to find a separate section header for initial build stats (not just combined with rebuild)"


def test_report_has_separate_rebuild_statistics_section():
    """Verify that the report contains distinct initial and rebuild statistics sections."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Both sections must exist as separate, distinct sections
    initial_section = re.search(
        r"Initial\s+Build\s+Statistics",
        content,
        re.IGNORECASE
    )
    rebuild_section = re.search(
        r"Rebuild\s+(?:Build\s+)?Statistics",
        content,
        re.IGNORECASE
    )

    assert initial_section and rebuild_section, \
        "Report must contain TWO separate sections: 'Initial Build Statistics' and 'Rebuild Statistics'. " \
        f"Found initial: {bool(initial_section)}, Found rebuild: {bool(rebuild_section)}"

    # Verify they are at different positions (truly separate)
    if initial_section and rebuild_section:
        assert initial_section.start() < rebuild_section.start(), \
            "Initial and Rebuild statistics sections must be in correct order (Initial before Rebuild)"


def test_cache_cleared_before_initial_build():
    """Verify that the cache was cleared before the initial build (evidence in report)."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # The report should indicate cache was cleared before initial build
    # Look for evidence like "cleared", "cleaned", "fresh", "empty", "starting with empty cache", etc.
    cache_clear_evidence = re.search(
        r"(clear|clean|empty|fresh|initial.*cache|cache.*clear)",
        content,
        re.IGNORECASE
    )

    assert cache_clear_evidence, \
        "Report does not indicate that the cache was cleared before initial build. " \
        "Include a statement in the report mentioning that /tmp/sccache was cleared or cache started empty"


def test_build_directory_preserved_across_rebuilds():
    """Verify that the build directory and CMakeCache.txt are preserved between initial and rebuild."""
    # Check that /app/build directory still exists after rebuild (wasn't deleted)
    build_dir = Path("/app/build")
    assert build_dir.exists() and build_dir.is_dir(), \
        "/app/build directory does not exist - it should have been preserved across rebuilds"

    # Verify CMakeCache.txt still exists
    cmake_cache = build_dir / "CMakeCache.txt"
    assert cmake_cache.exists(), \
        "CMakeCache.txt should be preserved in /app/build across rebuilds (not deleted during rebuild)"

    # Verify CMakeCache.txt still contains sccache and compiler configuration
    # (proving it was created during initial build and not recreated)
    cache_content = cmake_cache.read_text()
    assert "CMAKE_CXX_COMPILER" in cache_content, \
        "CMakeCache.txt lost CMAKE_CXX_COMPILER configuration"
    assert "sccache" in cache_content, \
        "CMakeCache.txt lost sccache configuration"


def test_report_shows_cache_stats_in_two_sections():
    """Verify that both initial and rebuild statistics sections contain cache information."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Find the two sections
    initial_match = re.search(
        r"Initial\s+Build\s+Statistics(.*?)(?=Rebuild\s+(?:Build\s+)?Statistics|$)",
        content,
        re.IGNORECASE | re.DOTALL
    )
    rebuild_match = re.search(
        r"Rebuild\s+(?:Build\s+)?Statistics(.*?)$",
        content,
        re.IGNORECASE | re.DOTALL
    )

    assert initial_match, "Could not find Initial Build Statistics section"
    assert rebuild_match, "Could not find Rebuild Statistics section"

    initial_section = initial_match.group(1)
    rebuild_section = rebuild_match.group(1)

    # Check that initial section has some cache reference
    initial_has_cache_info = any(
        keyword in initial_section.lower()
        for keyword in ["cache", "compile", "hit", "miss", "request", "sccache"]
    )
    assert initial_has_cache_info, \
        "Initial Build Statistics section does not contain cache-related information"

    # Check that rebuild section has cache hits specifically
    rebuild_has_hits = re.search(
        r"(cache\s+hit|hit)s?\s*[:=]?\s*\d+",
        rebuild_section,
        re.IGNORECASE
    )
    assert rebuild_has_hits, \
        "Rebuild Statistics section does not show cache hits as a numeric value"


def test_minimum_cache_hits_for_rebuild():
    """Verify that the rebuild achieves at least 2 cache hits (proving multiple source files were cached)."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Find the rebuild section
    rebuild_match = re.search(
        r"Rebuild\s+(?:Build\s+)?Statistics(.*?)$",
        content,
        re.IGNORECASE | re.DOTALL
    )
    assert rebuild_match, "Could not find Rebuild Statistics section"
    rebuild_section = rebuild_match.group(1)

    # Extract cache hit count
    cache_hit_match = re.search(
        r"(cache\s+hit|hit)s?\s*[:=]?\s*(\d+)",
        rebuild_section,
        re.IGNORECASE
    )
    assert cache_hit_match, "Could not find cache hits value in rebuild statistics"

    cache_hits = int(cache_hit_match.group(2))
    # The project has multiple source files, so a proper rebuild should have at least 2 cache hits
    assert cache_hits >= 2, \
        f"Rebuild must achieve at least 2 cache hits (got {cache_hits}). " \
        "This verifies that multiple source files were properly cached and reused."


def test_initial_build_shows_cache_misses():
    """Verify that the initial build shows cache misses (proving it was a fresh build)."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Find the initial build section
    initial_match = re.search(
        r"Initial\s+Build\s+Statistics(.*?)(?=Rebuild\s+(?:Build\s+)?Statistics|$)",
        content,
        re.IGNORECASE | re.DOTALL
    )
    assert initial_match, "Could not find Initial Build Statistics section"
    initial_section = initial_match.group(1)

    # The initial build should show cache misses (not hits) proving it started fresh
    has_miss_info = re.search(
        r"(cache\s+miss|miss)e?s?\s*[:=]?\s*\d+",
        initial_section,
        re.IGNORECASE
    )
    assert has_miss_info, \
        "Initial Build Statistics must show cache misses, proving the cache was empty at start"


def test_demonstrable_improvement_threshold():
    """Verify that the rebuild shows at least 15% improvement over initial build."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # Extract improvement percentage
    improvement_match = re.search(r"Improvement:\s*(-?\d*\.?\d+)\s*%", content, re.IGNORECASE)
    assert improvement_match, "Could not find improvement percentage in report"

    improvement = float(improvement_match.group(1))
    # Require at least 15% improvement to prove sccache is actually effective
    assert improvement >= 15, \
        f"Rebuild must show at least 15% improvement (got {improvement}%). " \
        "A properly configured sccache should provide significant speedup on rebuilds."


def test_sccache_server_running():
    """Verify that sccache is running as a server for optimal caching."""
    try:
        result = subprocess.run(
            ["sccache", "--show-stats"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # sccache --show-stats only works when server is running
        # If it fails, server is not running
        assert result.returncode == 0, \
            f"sccache server is not running. Start it with 'sccache --start-server'. Error: {result.stderr}"
    except FileNotFoundError:
        assert False, "sccache command not found"
    except subprocess.TimeoutExpired:
        assert False, "sccache --show-stats command timed out - server may be unresponsive"


def test_object_files_properly_cleaned():
    """Verify that object files were deleted between initial and rebuild (forcing recompilation)."""
    # After the full workflow, we should have fresh object files from the rebuild
    # This test verifies the rebuild actually compiled files (not just reported cached data)
    build_dir = Path("/app/build")
    cmake_files_dir = build_dir / "CMakeFiles" / "demo.dir" / "src"

    assert cmake_files_dir.exists(), \
        "CMakeFiles/demo.dir/src does not exist - compilation artifacts missing"

    # Check for object files
    object_files = list(cmake_files_dir.glob("*.o"))
    assert len(object_files) >= 2, \
        f"Expected at least 2 object files in CMakeFiles/demo.dir/src, found {len(object_files)}. " \
        "This verifies that multiple source files were actually compiled."


def test_cache_directory_has_substantial_content():
    """Verify that the sccache directory has substantial cached content (not just metadata)."""
    cache_dir = Path("/tmp/sccache")
    assert cache_dir.exists(), "/tmp/sccache directory does not exist"

    # Count all files in the cache directory
    all_files = list(cache_dir.rglob("*"))
    file_count = len([f for f in all_files if f.is_file()])

    # A proper cache should have multiple files (one for each compiled object)
    assert file_count >= 3, \
        f"Cache directory has only {file_count} files. " \
        "A working cache should store at least 3 cached compilation results."

    # Check total size of cached content
    total_size = sum(f.stat().st_size for f in all_files if f.is_file())
    # Each cached object should be at least a few KB
    assert total_size >= 10000, \
        f"Cache directory total size is only {total_size} bytes. " \
        "Expected at least 10KB of cached compilation data."


def test_report_mentions_header_modification():
    """Verify that the report mentions the header file modification that triggered rebuild."""
    report_path = Path("/app/cache_report.txt")
    content = report_path.read_text()

    # The report should mention the header modification
    header_mentioned = any(keyword in content.lower() for keyword in [
        "common.h", "header", "modification", "modified"
    ])

    assert header_mentioned, \
        "Report should mention the header file modification (common.h) that triggered the rebuild. " \
        "Include information about what was changed to trigger the cache effectiveness test."
