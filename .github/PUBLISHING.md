# Publishing to PyPI via GitHub Actions

This repository is set up to automatically publish to PyPI when you create a release tag.

## Setup Steps

### 1. Enable GitHub Environments

1. Go to your repository on GitHub
2. Go to **Settings** → **Environments**
3. Create two environments:
   - `pypi` (for production releases)
   - `testpypi` (for testing releases)

### 2. Configure PyPI Publishing

GitHub Actions uses **Trusted Publishing** (no API keys needed):

#### For PyPI (production):
1. Go to [PyPI](https://pypi.org) and log in
2. Go to **Your Account** → **Publishing** 
3. Add a new **Trusted Publisher**:
   - **Owner**: `hamedbh` (your GitHub username)
   - **Repository name**: `piicleaner`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`

#### For TestPyPI (testing):
1. Go to [TestPyPI](https://test.pypi.org) and log in
2. Go to **Your Account** → **Publishing**
3. Add a new **Trusted Publisher**:
   - **Owner**: `hamedbh`
   - **Repository name**: `piicleaner`
   - **Workflow name**: `test-release.yml`
   - **Environment name**: `testpypi`

## How to Release

### Test Release (TestPyPI)
```bash
# Create a test release tag
git tag v0.1.0-test1
git push origin v0.1.0-test1
```

This will:
- Build wheels for Linux x86_64 only (faster)
- Publish to TestPyPI
- Test installation: `pip install -i https://test.pypi.org/simple/ piicleaner`

### Production Release (PyPI)
```bash
# Create a production release tag
git tag v0.1.0
git push origin v0.1.0
```

This will:
- Build wheels for all platforms (Linux, Windows, macOS)
- Build for all architectures (x86_64, ARM64, etc.)
- Publish to PyPI
- Users can install: `pip install piicleaner`

## Workflows Explained

### `ci.yml`
- Runs on every push/PR
- Tests on multiple OS and Python versions
- Ensures code quality before release

### `test-release.yml`
- Triggered by tags like `v*-test*`
- Quick build for testing
- Publishes to TestPyPI

### `release.yml`
- Triggered by tags like `v*` (but not `v*-test*`)
- Full multi-platform build
- Publishes to PyPI

## Version Bumping

Update version in `Cargo.toml`:
```toml
[package]
version = "0.1.1"
```

The Python package version is automatically synced from Cargo.toml.

## Troubleshooting

- **Build failures**: Check the Actions tab for detailed logs
- **Publishing failures**: Ensure Trusted Publishers are configured correctly
- **Version conflicts**: Each version can only be published once