#!/usr/bin/env python3
"""Test script for output directory resource mapping."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import directly using the file path to avoid __init__ importing server
from wikigen.mcp.output_resources import discover_all_projects
from wikigen.config import get_output_dir

print("=" * 60)
print("Testing Output Directory Resource Mapping")
print("=" * 60)

# Test 1: Get output directory
print("\n1. Testing output directory detection:")
try:
    output_dir = get_output_dir()
    print(f"   ✓ Output directory: {output_dir}")
    print(f"   ✓ Exists: {output_dir.exists()}")
    print(f"   ✓ Absolute path: {output_dir.absolute()}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 2: Discover projects
print("\n2. Testing document discovery:")
try:
    projects = discover_all_projects()
    print(f"   ✓ Found {len(projects)} markdown files")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 3: Show sample results
print("\n3. Sample discovered files (first 20):")
if projects:
    for i, (name, path) in enumerate(sorted(projects.items())[:20], 1):
        try:
            # Show relative path from home if possible
            rel_path = path.relative_to(Path.home())
            path_str = f"~/{rel_path}"
        except (ValueError, TypeError):
            path_str = str(path)

        print(f"   {i:2d}. {name}")
        print(f"       -> {path_str}")

    if len(projects) > 20:
        print(f"\n   ... and {len(projects) - 20} more files")

    # Test 4: Check for specific patterns
    print("\n4. Pattern check:")
    flat_files = [name for name in projects.keys() if "/" not in name]
    nested_files = [name for name in projects.keys() if "/" in name]
    print(f"   ✓ Flat files (at root): {len(flat_files)}")
    print(f"   ✓ Nested files (in folders): {len(nested_files)}")

    if flat_files:
        print("\n   Example flat files:")
        for name in sorted(flat_files)[:5]:
            print(f"     - {name}")

    if nested_files:
        print("\n   Example nested files:")
        for name in sorted(nested_files)[:5]:
            print(f"     - {name}")
else:
    print("   ⚠ No markdown files found in output directory")
    print("   This could mean:")
    print("     - Output directory is empty")
    print("     - No .md files exist yet")
    print("     - Files are in a different location")

print("\n" + "=" * 60)
print("✓ All tests completed successfully!")
print("=" * 60)
