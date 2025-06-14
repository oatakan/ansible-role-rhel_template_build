# Release Process and Versioning Guide

This document describes the release process and versioning strategy for the `oatakan.rhel_template_build` Ansible role.

## Overview

The release process is **fully automated** using AI-powered GitHub Actions:

### 🤖 Automated AI-Powered Pipeline (Recommended)
1. **Development** → Feature branches → Pull Requests → Main branch
2. **AI Analysis** → Automatically determines version bump and changelog
3. **Release** → Automatic tag creation, GitHub release, and Galaxy deployment

No manual steps required! Just push to main and the AI handles everything.

### 📝 Manual Process (Fallback)
The semi-automated manual process is still available as a fallback:
1. **Development** → Feature branches → Pull Requests → Main branch
2. **Release Preparation** → GitHub Action creates release PR with changelog
3. **Release** → Tag creation triggers automatic Galaxy deployment

See [AI_AUTOMATION.md](AI_AUTOMATION.md) for detailed information about the AI-powered automation.

## Versioning Strategy

We follow [Semantic Versioning](https://semver.org/) (SemVer):

- **MAJOR** (X.0.0): Incompatible API changes
  - Removing variables
  - Changing default behavior significantly
  - Dropping support for OS versions
  
- **MINOR** (0.X.0): Backwards-compatible functionality
  - Adding new features
  - Adding new variables (with defaults)
  - Adding support for new OS versions
  
- **PATCH** (0.0.X): Backwards-compatible bug fixes
  - Fixing bugs
  - Security updates
  - Documentation improvements

## Release Workflow

### 1. Prepare Release

Run the Release workflow from GitHub Actions:

```bash
# From GitHub UI: Actions → Release → Run workflow
# Select release type: patch, minor, major, or custom
```

This creates a PR with:
- Updated CHANGELOG.md template
- Version bump preparation

### 2. Update the Release PR

1. Review the auto-generated PR
2. Update CHANGELOG.md with actual changes:
   ```markdown
   ## [v1.0.1] - 2025-01-15
   
   ### Added
   - Support for RHEL 10
   
   ### Changed
   - Improved container detection logic
   
   ### Fixed
   - Fixed hostname reset in containers
   ```

3. Ensure all CI checks pass
4. Get PR reviewed and merge

### 3. Create Release Tag

After PR is merged, create and push the tag:

```bash
git checkout main
git pull origin main
git tag v1.0.1
git push origin v1.0.1
```

The tag push automatically:
- Triggers Galaxy import
- Creates GitHub release
- Updates Ansible Galaxy

### 4. Verify Release

1. Check [GitHub Releases](https://github.com/oatakan/ansible-role-rhel_template_build/releases)
2. Verify on [Ansible Galaxy](https://galaxy.ansible.com/oatakan/rhel_template_build)
3. Test installation:
   ```bash
   ansible-galaxy install oatakan.rhel_template_build,v1.0.1
   ```

## Setup Requirements

### 1. Ansible Galaxy API Token

1. Log in to [galaxy.ansible.com](https://galaxy.ansible.com)
2. Go to Preferences → API Key
3. Copy your API key
4. Add to GitHub repository secrets:
   - Go to Settings → Secrets and variables → Actions
   - Add secret named `ANSIBLE_GALAXY_API_KEY`

### 2. Repository Settings

Ensure these settings in your GitHub repository:
- Branch protection on `main` (require PR reviews)
- Allow GitHub Actions to create PRs
- Tag protection rules (optional, for release tags)

## Manual Release (Alternative)

If automation fails, you can manually release:

```bash
# 1. Create and push tag
git tag v1.0.1
git push origin v1.0.1

# 2. Import to Galaxy manually
ansible-galaxy role import \
  --api-key="your-api-key" \
  --branch="v1.0.1" \
  oatakan rhel_template_build

# 3. Create GitHub release via UI
```

## Best Practices

### 1. Changelog Maintenance

- Keep CHANGELOG.md updated with each PR
- Use clear, user-focused language
- Link to PRs/issues for context
- Follow [Keep a Changelog](https://keepachangelog.com/) format

### 2. Testing Before Release

- Ensure all CI checks pass
- Test on all supported platforms
- Run molecule tests locally if needed:
  ```bash
  molecule test
  ```

### 3. Version Pinning

Advise users to pin versions in requirements.yml:

```yaml
roles:
  - name: oatakan.rhel_template_build
    version: v1.0.1  # Pin to specific version
```

### 4. Deprecation Policy

- Announce deprecations in MINOR releases
- Remove deprecated features in MAJOR releases
- Provide migration guides in changelog

### 5. Release Frequency

- PATCH releases: As needed for bug fixes
- MINOR releases: Monthly or when features accumulate
- MAJOR releases: Yearly or for significant changes

## Troubleshooting

### Galaxy Import Fails

1. Check Galaxy import status: https://galaxy.ansible.com/my-imports
2. Verify API token is valid
3. Ensure meta/main.yml is valid:
   ```bash
   ansible-galaxy role info .
   ```

### Tag Already Exists

```bash
# Delete local tag
git tag -d v1.0.1

# Delete remote tag
git push origin :refs/tags/v1.0.1

# Recreate tag
git tag v1.0.1
git push origin v1.0.1
```

### Release Workflow Issues

- Check GitHub Actions permissions
- Verify GITHUB_TOKEN has write access
- Check branch protection rules

## Version History Tracking

The role version appears in:
1. Git tags (source of truth)
2. GitHub releases
3. Ansible Galaxy
4. CHANGELOG.md

No need to maintain version in meta/main.yml as Galaxy uses git tags.