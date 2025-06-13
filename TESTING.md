# Testing Guide for rhel_template_build Role

This document explains the testing strategy and implementation for the `oatakan.rhel_template_build` Ansible role.

## Overview

Since this role is designed to prepare VM templates and includes system-level operations (mounting ISOs, configuring virtualization tools, etc.), testing requires special considerations. We use a multi-layered testing approach:

1. **Static Analysis** - Linting and syntax checking
2. **Container Testing** - Basic functionality testing with limitations
3. **VM Testing** - Full integration testing (requires self-hosted runner)

## Test Types

### 1. Static Analysis (Always Runs)

These tests run on every push and PR:

- **yamllint**: Validates YAML syntax and style
- **ansible-lint**: Checks for Ansible best practices
- **syntax-check**: Verifies playbook syntax

### 2. Container Testing (Default)

Container tests run automatically but have limitations:

- Uses Docker containers with systemd
- Tests basic role functionality
- Skips virtualization-specific tasks
- Validates package installation and basic configuration

**Limitations in containers:**
- Cannot test VM tools (VMware, VirtualBox, Parallels)
- Cannot test actual disk partitioning
- Limited networking capabilities
- No real hardware detection

### 3. VM Testing (Manual/Scheduled)

Full VM testing provides complete validation:

- Uses Vagrant with VirtualBox/VMware
- Tests all role features
- Validates VM tool installation
- Tests disk operations and networking

## Running Tests Locally

### Prerequisites

```bash
# For linting and basic testing
pip install ansible ansible-lint yamllint
ansible-galaxy collection install community.general ansible.posix

# For container testing
pip install molecule molecule-plugins[docker]
docker --version  # Ensure Docker is installed

# For VM testing (additional)
pip install molecule-plugins[vagrant]
vagrant --version  # Ensure Vagrant is installed
```

### Running Container Tests

```bash
# Run all test sequences
molecule test

# Run specific test sequence
molecule converge  # Just run the role
molecule verify    # Run verification
molecule destroy   # Clean up

# Test with different OS
MOLECULE_DISTRO=rockylinux:8 molecule test
```

### Running VM Tests

```bash
cd molecule/vagrant
MOLECULE_VAGRANT_BOX=generic/rocky9 molecule test
```

### Available Test Matrices

**Container images:**
- `rockylinux:8`
- `rockylinux:9` (default)
- `almalinux:8`
- `almalinux:9`

**Vagrant boxes:**
- `generic/rocky8`
- `generic/rocky9`
- `generic/alma8`
- `generic/alma9`
- `generic/centos7`

## Container Testing Details

The container tests use a custom Dockerfile that:

1. Installs systemd and required packages
2. Creates proper user accounts
3. Sets up directories with correct permissions
4. Configures the environment for Ansible

The role detects container environments and automatically:
- Skips virtualization-specific tasks
- Avoids operations that require real hardware
- Adapts cleanup tasks for containers

## CI/CD Integration

### GitHub Actions Workflows

1. **ci.yml** - Main CI workflow
   - Runs on every push and PR
   - Performs linting and container tests
   - Uses matrix strategy for multiple OS versions

2. **vm-test.yml** - VM integration tests
   - Manual trigger or weekly schedule
   - Requires self-hosted runner with virtualization
   - Full role validation

### Setting Up Self-Hosted Runner

For VM testing, you need a self-hosted runner:

```bash
# On a VM or physical machine with virtualization enabled
# Follow GitHub's self-hosted runner setup guide
# Install required software:
sudo apt-get update
sudo apt-get install -y virtualbox vagrant
pip install ansible molecule molecule-plugins[vagrant]
```

## Debugging Failed Tests

### Container Test Failures

```bash
# Keep container running after failure
molecule converge --destroy=never

# Login to container
molecule login

# Check logs
docker logs molecule_instance_1

# Run with verbose output
molecule --debug converge
```

### Common Issues and Solutions

1. **"Failed to create temporary directory" error**
   - Container permissions issue
   - Solution: Ensure Dockerfile creates directories with proper permissions

2. **"Package not found" errors**
   - Missing EPEL or repository issues
   - Solution: Check repository configuration in container

3. **Service startup failures**
   - systemd limitations in containers
   - Solution: Use `failed_when: false` for non-critical services

4. **Network configuration errors**
   - Container networking differs from VMs
   - Solution: Skip or mock network operations in containers

## Best Practices

1. **Use conditional logic**: Always check `is_container` fact before system operations
2. **Fail gracefully**: Use `failed_when: false` for operations that might fail in containers
3. **Mock when necessary**: Create mock files/facts for container testing
4. **Document limitations**: Clearly indicate what cannot be tested in containers
5. **Regular VM testing**: Schedule weekly VM tests to catch regressions

## Contributing

When adding new features:

1. Update container tests if the feature can be tested there
2. Add VM test scenarios for hardware-specific features
3. Update this documentation
4. Ensure CI passes before submitting PR

## Future Improvements

- [ ] Add AWS EC2 testing scenario
- [ ] Implement Azure VM testing
- [ ] Add performance benchmarks
- [ ] Create test report dashboard
- [ ] Add security scanning (ansible-lint security rules)