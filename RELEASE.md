# Release Guide

This document explains how to release new versions of WikiGen CLI.

## Prerequisites

1. **PyPI Account**: You need a PyPI account and API token
2. **GitHub Secrets**: Add your PyPI API token to GitHub repository secrets

### Setting up PyPI API Token

1. Go to [PyPI](https://pypi.org) and create an account
2. Go to Account Settings → API tokens
3. Create a new token with scope "Entire account" (or just this project)
4. Copy the token (starts with `pypi-`)

### Adding GitHub Secret

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `PYPI_API_TOKEN`
5. Value: Your PyPI token (paste the `pypi-...` token)

## Release Methods

### Method 1: Manual Git Tag (Recommended)

```bash
# Update version in pyproject.toml
git add pyproject.toml
git commit -m "Bump version to 0.1.0"
git tag v0.1.0
git push origin main
git push origin v0.1.0
```

### Method 2: GitHub Release

1. Go to GitHub repository → Releases
2. Click "Create a new release"
3. Choose tag: `v0.1.0` (create if doesn't exist)
4. Fill in release title and description
5. Click "Publish release"

## What Happens Automatically

Once you create a tag or release, the GitHub Actions workflow will:

1. ✓ **Build** the package (wheel + source)
2. ✓ **Test** the package integrity
3. ✓ **Upload** to PyPI automatically
4. ✓ **Verify** the upload was successful

## Monitoring the Release

- Go to **Actions** tab in GitHub to see the workflow progress
- Check **PyPI** to see your package appear
- Test installation: `pip install wikigen==0.1.0`

## Troubleshooting

### Workflow Fails
- Check the Actions tab for error details
- Verify `PYPI_API_TOKEN` secret is set correctly
- Ensure version number is valid (e.g., `0.1.0` not `v0.1.0` in pyproject.toml)

### Package Already Exists
- PyPI doesn't allow overwriting existing versions
- Increment the version number and try again

### Token Issues
- Regenerate PyPI token if expired
- Update GitHub secret with new token

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., `1.0.0`)
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

Examples:
- `0.1.0` → `0.1.1` (bug fix)
- `0.1.1` → `0.2.0` (new feature)
- `0.2.0` → `1.0.0` (breaking change)
