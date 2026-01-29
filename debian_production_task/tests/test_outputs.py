import subprocess
import tempfile
import os
import re
import hashlib
from pathlib import Path

def get_deb_package(build_dir: Path, package_name: str) -> Path:
    """Get a specific .deb package by name prefix."""
    deb_files = list(build_dir.glob(f"{package_name}_*.deb"))
    # Filter out debug symbol packages if any
    main_packages = [f for f in deb_files if "-dbgsym" not in f.name]
    
    if not main_packages:
        return None
    return main_packages[0]

def _parse_checksum_section(content: str, section_name: str) -> dict:
    """Helper to parse a checksum section from a .changes or .dsc file."""
    files = {}
    checksum_regex = re.compile(r"^\s+([a-f0-9]+)\s+([0-9]+)\s+(.*)$")
    
    in_section = False
    for line in content.splitlines():
        if line.startswith(section_name + ":"):
            in_section = True
            continue
        if in_section:
            if line.startswith(" "):
                match = checksum_regex.match(line)
                if match:
                    checksum, size, filename = match.groups()
                    files[filename.strip()] = {
                        "checksum": checksum,
                        "size": int(size)
                    }
            else:
                # Reached end of section
                break
    return files

def test_multi_binary_packages_exist():
    """Test that both 'hello' and 'hello-doc' packages were created."""
    build_dir = Path("/build")
    
    hello_deb = get_deb_package(build_dir, "hello")
    doc_deb = get_deb_package(build_dir, "hello-doc")
    
    assert hello_deb is not None, "Package 'hello' not found in /build/"
    assert doc_deb is not None, "Package 'hello-doc' not found in /build/"

def test_hello_package_content():
    """Test that 'hello' package contains the binary and Recommends hello-doc."""
    build_dir = Path("/build")
    deb_file = get_deb_package(build_dir, "hello")
    
    # Check content
    result = subprocess.run(["dpkg-deb", "-c", str(deb_file)], capture_output=True, text=True)
    assert result.returncode == 0, "Failed to list content"
    
    assert "/usr/bin/hello" in result.stdout, "Binary /usr/bin/hello missing from hello package"
    assert "man/man1" not in result.stdout, "Man page should not be in hello package"
    
    # Check control info for Recommends and Architecture
    info = subprocess.run(["dpkg-deb", "-I", str(deb_file)], capture_output=True, text=True)
    assert "Recommends: hello-doc" in info.stdout, "hello package must Recommend hello-doc"
    
    # Check that architecture is architecture-dependent (not 'all')
    # The built .deb will show actual arch like 'amd64', 'arm64', etc., not 'any'
    assert "Architecture: all" not in info.stdout, "hello package must NOT be Architecture: all (it's the binary, not doc)"
    # Verify Architecture field exists and has a value
    assert "Architecture:" in info.stdout, "hello package must have Architecture field in control"

def test_doc_package_content():
    """Test that 'hello-doc' package contains the man page and is Arch: all."""
    build_dir = Path("/build")
    deb_file = get_deb_package(build_dir, "hello-doc")
    
    # Check content
    result = subprocess.run(["dpkg-deb", "-c", str(deb_file)], capture_output=True, text=True)
    
    assert "/usr/share/man/man1/hello.1.gz" in result.stdout, "Man page missing from hello-doc package"
    assert "/usr/bin/hello" not in result.stdout, "Binary should not be in hello-doc package"
    
    # Check Architecture
    info = subprocess.run(["dpkg-deb", "-I", str(deb_file)], capture_output=True, text=True)
    assert "Architecture: all" in info.stdout, "hello-doc must be Architecture: all"

def test_binary_is_compiled_elf():
    """Verify the binary in hello package is ELF."""
    build_dir = Path("/build")
    deb_file = get_deb_package(build_dir, "hello")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["dpkg-deb", "-x", str(deb_file), tmpdir], check=True)
        binary_path = Path(tmpdir) / "usr" / "bin" / "hello"
        
        result = subprocess.run(["file", str(binary_path)], capture_output=True, text=True)
        assert "elf" in result.stdout.lower(), "Binary must be ELF"

def test_binary_runs_correctly():
    """Verify binary output matches patched expectation."""
    build_dir = Path("/build")
    deb_file = get_deb_package(build_dir, "hello")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["dpkg-deb", "-x", str(deb_file), tmpdir], check=True)
        binary_path = Path(tmpdir) / "usr" / "bin" / "hello"
        os.chmod(binary_path, 0o755)
        
        result = subprocess.run([str(binary_path)], capture_output=True, text=True)
        assert result.stdout == "Hello, Reproducible World!\n", "Patch not applied correctly"

def test_dpkg_buildpackage_used():
    """Verify standard build tools were used."""
    build_dir = Path("/build")
    changes_files = list(build_dir.glob("*.changes"))
    assert len(changes_files) > 0, "No .changes file found - dpkg-buildpackage must be used"
    
    changes_content = changes_files[0].read_text()
    assert "hello" in changes_content and "hello-doc" in changes_content, ".changes file must reference both packages"
    
    # Verify .changes file has proper format (not just a fake file)
    # Real .changes files have specific headers set by dpkg-buildpackage
    assert "Format:" in changes_content, ".changes file must have Format: header (set by dpkg-buildpackage)"
    assert "Source:" in changes_content, ".changes file must have Source: header (set by dpkg-buildpackage)"
    assert "Binary:" in changes_content, ".changes file must have Binary: header (set by dpkg-buildpackage)"
    
    # Verify files listing in .changes (references .deb, .dsc, etc.)
    assert ".deb" in changes_content, ".changes file must reference generated .deb files"
    
    # Check for .dsc file
    dsc_files = list(build_dir.glob("*.dsc"))
    assert len(dsc_files) > 0, ".dsc file not found - dpkg-buildpackage must be used to create source metadata"
    
    # Verify .dsc file has proper format and reasonable size
    dsc_content = dsc_files[0].read_text()
    assert "Format:" in dsc_content, ".dsc file must have Format: header"
    assert "Source:" in dsc_content, ".dsc file must have Source: header"
    assert "Binary:" in dsc_content, ".dsc file must have Binary: header"
    
    # Verify .dsc has file checksums (proves dpkg-source was used)
    assert "Files:" in dsc_content or "Checksums-Sha256:" in dsc_content, \
        ".dsc file must have file checksums/hashes (generated by dpkg-source/dpkg-buildpackage)"
    
    # Verify changes file references the .dsc file created
    dsc_filename = dsc_files[0].name
    assert dsc_filename in changes_content, ".changes file must reference the .dsc file"

def test_source_files_remain():
    """Verify source files persist."""
    assert Path("/build/hello.c").exists()
    assert Path("/build/hello.1").exists()
    assert Path("/build/debian/rules").exists()
    assert Path("/build/Makefile").exists(), "Makefile must persist after build"

def test_patch_mechanism_used():
    """Verify that the patching mechanism (quilt/series) was explicitly used/configured."""
    series_file = Path("/build/debian/patches/series")
    assert series_file.exists(), "debian/patches/series file not found. Quilt patching requires this file."
    
    content = series_file.read_text()
    assert "01-fix-greeting.patch" in content, "Patch '01-fix-greeting.patch' must be listed in debian/patches/series"
    
    # Verify debian/source/format is configured for quilt
    format_file = Path("/build/debian/source/format")
    assert format_file.exists(), "debian/source/format file not found. Required for quilt patch system."
    
    format_content = format_file.read_text().strip()
    assert format_content == "3.0 (quilt)", f"debian/source/format must contain '3.0 (quilt)', found: {format_content}"
    
    # Verify .dsc file references the quilt format and patch application
    dsc_files = list(Path("/build").glob("*.dsc"))
    assert len(dsc_files) > 0, "No .dsc file for verification"
    
    dsc_content = dsc_files[0].read_text()
    # The Format should be listed in .dsc (proves quilt format was used)
    assert "3.0 (quilt)" in dsc_content, ".dsc file must indicate quilt format"

def test_patch_actually_applied():
    """Verify that the patch was actually applied to source code (anti-cheating)."""
    hello_c_path = Path("/build/hello.c")
    assert hello_c_path.exists(), "hello.c must exist in /build"
    
    content = hello_c_path.read_text()
    # Patch should have changed "Hello, World!" to "Hello, Reproducible World!"
    assert "Hello, Reproducible World!" in content, "Patch not applied: hello.c must contain 'Hello, Reproducible World!'"
    assert content.count("Hello, World!") == 0, "Original string still exists: patch must replace 'Hello, World!' completely"

def test_quilt_patch_file_exists():
    """Verify that the actual patch file exists and has content (anti-cheating)."""
    patch_file = Path("/build/debian/patches/01-fix-greeting.patch")
    assert patch_file.exists(), "Patch file debian/patches/01-fix-greeting.patch not found"
    
    content = patch_file.read_text()
    # Verify it's a real patch file with expected content
    assert "---" in content and "+++" in content, "Patch file must contain diff headers (--- and +++)"
    assert "Hello, World!" in content and "Hello, Reproducible World!" in content, \
        "Patch must show the actual changes from 'Hello, World!' to 'Hello, Reproducible World!'"

def test_build_log_proves_dpkg_buildpackage_usage():
    """ANTI-CHEAT: Verify build.log shows dpkg-buildpackage and its sub-commands were run."""
    log_file = Path("/build/build.log")
    assert log_file.exists(), "Build log file /build/build.log not found. It must be created by redirecting output from dpkg-buildpackage."

    log_content = log_file.read_text()

    # Check for a sequence of commands that are characteristic of a real dpkg-buildpackage run.
    # This is much harder to fake than just creating the files.
    expected_sequence = [
        "dpkg-source --before-build",
        "dpkg-buildpackage: info: source package hello",
        "dpkg-buildpackage: info: binary-only build",
        "dpkg-genchanges",
        "dpkg-source --after-build",
        "signfile", # Part of the final signing process
    ]

    last_found_index = -1
    for item in expected_sequence:
        try:
            # Find the position of the current item in the log after the last found item.
            current_index = log_content.index(item, last_found_index + 1)
            last_found_index = current_index
        except ValueError:
            assert False, (
                f"Build log verification failed. The log must show that dpkg-buildpackage was used correctly. "
                f"Expected sequence item not found (or not in order): '{item}'"
            )

def test_dsc_lists_patch_file():
    """ANTI-CHEAT: Verify .dsc file lists the patch, proving quilt was integrated."""
    build_dir = Path("/build")
    dsc_files = list(build_dir.glob("*.dsc"))
    assert len(dsc_files) > 0, ".dsc file not found"
    dsc_content = dsc_files[0].read_text()

    # When quilt patches are used, the .dsc file lists the original tarball
    # and a debian.tar.gz that contains the debian/ directory, including patches.
    # The checksums section should prove this structure.
    assert "debian.tar.gz" in dsc_content, \
        ".dsc file must list 'debian.tar.gz', which indicates a '3.0 (quilt)' format build with patches."

def test_changes_file_checksums_are_valid():
    """ANTI-CHEAT: Verify checksums in .changes file match actual file artifacts."""
    build_dir = Path("/build")
    changes_files = list(build_dir.glob("*.changes"))
    assert len(changes_files) > 0, "No .changes file found"
    changes_content = changes_files[0].read_text()
    
    # Try parsing SHA256 first, then fallback to MD5
    files_to_check = _parse_checksum_section(changes_content, "Checksums-Sha256")
    hash_algo = hashlib.sha256
    if not files_to_check:
        files_to_check = _parse_checksum_section(changes_content, "Files")
        hash_algo = hashlib.md5

    assert len(files_to_check) > 0, "Could not parse checksums from .changes file"

    for filename, data in files_to_check.items():
        file_path = build_dir / filename
        assert file_path.exists(), f"File '{filename}' listed in .changes not found in /build"
        
        # Verify file size
        actual_size = file_path.stat().st_size
        expected_size = data["size"]
        assert actual_size == expected_size, \
            f"Size mismatch for {filename}: expected {expected_size}, got {actual_size}"
        
        # Verify checksum
        hasher = hash_algo()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        actual_checksum = hasher.hexdigest()
        expected_checksum = data["checksum"]
        
        assert actual_checksum == expected_checksum, \
            f"Checksum mismatch for {filename}: expected {expected_checksum}, got {actual_checksum}"
