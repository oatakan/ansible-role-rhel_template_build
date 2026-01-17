# oatakan.rhel_template_build

[![Ansible Role Version](https://img.shields.io/github/v/tag/oatakan/ansible-role-rhel_template_build?label=version)](https://galaxy.ansible.com/oatakan/rhel_template_build)
[![CI](https://github.com/oatakan/ansible-role-rhel_template_build/workflows/CI/badge.svg)](https://github.com/oatakan/ansible-role-rhel_template_build/actions/workflows/ci.yml)
[![CI](https://github.com/oatakan/ansible-role-rhel_template_build/workflows/VM%20Integration%20Tests/badge.svg)](https://github.com/oatakan/ansible-role-rhel_template_build/actions/workflows/vm-test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Role Downloads](https://img.shields.io/ansible/role/d/oatakan/rhel_template_build?label=downloads&logo=ansible)](https://galaxy.ansible.com/oatakan/rhel_template_build)

This role transforms a minimal **Red Hat Enterprise Linux (RHEL)** system into a golden image template that can be safely cloned. Designed primarily for RHEL environments, it installs common utilities, configures networking and SSH, enables cloud-init and guest agents, and cleans the system so cloned instances boot with fresh identities.

You can use this role with the Packer Ansible provisioner or combine it with roles like `oatakan.rhel_vcenter_template` and `oatakan.rhel_ovirt_template` when provisioning directly against your virtualization platform.

> ⚠️ **RHEL 7 is deprecated**: it is no longer part of the automated test matrix and will be removed in a future release. Use RHEL 8+ whenever possible.

## Supported Systems

This role is designed and tested for **Red Hat Enterprise Linux**:

### Primary Target
- ✅ **RHEL 8** (tested via Red Hat Universal Base Images)
- ✅ **RHEL 9** (tested via Red Hat Universal Base Images)  
- ✅ **RHEL 10** (tested via Red Hat Universal Base Images)

### Additional Compatibility
Also tested for compatibility with RHEL-based distributions:
- ✅ **Rocky Linux** 8, 9, 10
- ✅ **AlmaLinux** 8, 9, 10

*Testing is performed using both containerized environments and virtual machine scenarios.*

RHEL 7 might still function for some scenarios, but it is untested and no longer supported for new deployments.

## Requirements

* Ansible 2.9 or newer
* Root privileges on the target RHEL system
* **Red Hat Enterprise Linux** 8, 9, or 10 (RHEL-based distributions also supported)
* Optional: access to virtualization platform (VMware, VirtualBox, Parallels, or oVirt) for guest tools installation

## Role Variables

The most common variables are listed below. See `defaults/main.yml` for the full list and their default values.

| Variable | Default | Description |
|----------|---------|-------------|
| `target_vagrant` | `false` | When set to `true`, the Vagrant public key is installed for the local user. |
| `target_ovirt` | `false` | Enables cloud-init setup and installs the oVirt/QEMU guest agent. |
| `target_tart` | `false` | Installs and enables the guest agent suitable for Tart-built images (defaults to `qemu-guest-agent`). |
| `local_account_username` | `ansible` | User name that owns downloaded ISOs and receives the Vagrant key. |
| `permit_root_login_with_password` | `true` | Allows password based root logins in cloud-init configuration. |
| `parallels_tools_role` | `oatakan.linux_parallels_tools` | Role used to install Parallels guest tools when Parallels is detected. |

### Tart guest agent options

When `target_tart: true`, the role can install the agent in one of the following ways:

- `tart_guest_agent_install_method: repo` (default) installs `qemu-guest-agent` from standard repos.
- `tart_guest_agent_install_method: github` installs CirrusLabs `tart-guest-agent` from GitHub releases.
- `tart_guest_agent_install_method: auto` tries GitHub first, then falls back to repo.

Relevant variables:

- `tart_guest_agent_install_method` (`repo|github|auto`)
- `tart_guest_agent_package_name` / `tart_guest_agent_service_name` (repo path)
- `tart_guest_agent_github_repo` (default `cirruslabs/tart-guest-agent`)
- `tart_guest_agent_github_release` (default `latest`)
- `tart_guest_agent_base_url_override` (skip GitHub API)
- `tart_guest_agent_github_service_name` (default `tart-guest-agent`)

## Dependencies

If Parallels guest tools are required, ensure the [`oatakan.linux_parallels_tools`](https://galaxy.ansible.com/oatakan/linux_parallels_tools) role is available. No other external roles are required.

## Example Playbook

```yaml
- name: Build RHEL template
  hosts: rhel_hosts
  become: true
  roles:
    - role: oatakan.rhel_template_build
      vars:
        target_vagrant: true
        target_ovirt: false
        target_tart: false
```

## Testing

The role includes comprehensive automated testing to ensure functionality across supported systems.

### Local Testing

Run lint and syntax validation:

```bash
ANSIBLE_ROLES_PATH=$(pwd)/tests/roles ansible-lint --offline
ANSIBLE_ROLES_PATH=$(pwd)/tests/roles ansible-playbook -i tests/inventory tests/test.yml --syntax-check
```

### Integration Testing

Execute integration tests using Molecule:

```bash
pip install molecule molecule-plugins[docker]
ansible-galaxy collection install community.docker
ANSIBLE_ROLES_PATH=$(pwd)/tests/roles molecule test
```

**Requirements**: Docker must be installed and running. The test scenario validates role functionality across multiple RHEL and RHEL-compatible distributions using containerized environments.

The test suite uses an optimized `ansible.cfg` configuration with `remote_tmp` set to `/tmp` for container compatibility. Molecule automatically handles environment configuration.

### Testing Coverage

The automated testing validates functionality across:

- **RHEL** (using Red Hat Universal Base Images)
- **Rocky Linux** (RHEL compatibility)  
- **AlmaLinux** (RHEL compatibility)
- **Multiple deployment scenarios** (bare metal, VMs, containers)

## License

MIT

## Author Information

Orcun Atakan
