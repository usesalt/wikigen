#!/usr/bin/env python3
"""
Release script for Salt Docs CLI.
Creates a git tag and pushes it to trigger the release workflow.
"""

import subprocess
import sys
import re
from pathlib import Path

def get_version():
    """Get version from pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path) as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")

def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/release.py <version>")
        print("Example: python scripts/release.py 0.1.0")
        sys.exit(1)
    
    version = sys.argv[1]
    current_version = get_version()
    
    if version != current_version:
        print(f"Error: Version {version} doesn't match pyproject.toml version {current_version}")
        print("Please update the version in pyproject.toml first")
        sys.exit(1)
    
    tag_name = f"v{version}"
    
    print(f"Creating release for version {version}")
    
    # Check if tag already exists
    result = run_command(f"git tag -l {tag_name}", check=False)
    if tag_name in result.stdout:
        print(f"Error: Tag {tag_name} already exists")
        sys.exit(1)
    
    # Check if we're on main branch
    result = run_command("git branch --show-current")
    current_branch = result.stdout.strip()
    if current_branch != "main":
        print(f"Warning: You're on branch '{current_branch}', not 'main'")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Check if working directory is clean
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("Error: Working directory is not clean")
        print("Please commit or stash your changes first")
        sys.exit(1)
    
    # Create and push tag
    run_command(f"git tag {tag_name}")
    run_command(f"git push origin {tag_name}")
    
    print(f"Created and pushed tag {tag_name}")
    print("The release workflow will now automatically build and publish to PyPI")
    print(f"Check the Actions tab in GitHub to monitor the release progress")

if __name__ == "__main__":
    main()
