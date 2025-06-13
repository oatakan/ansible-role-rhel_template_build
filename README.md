# oatakan.rhel_template_build

[![CI](https://github.com/oatakan/ansible-role-rhel_template_build/actions/workflows/ci.yml/badge.svg)](https://github.com/oatakan/ansible-role-rhel_template_build/actions/workflows/ci.yml)
[![VM Tests](https://github.com/oatakan/ansible-role-rhel_template_build/actions/workflows/vm-test.yml/badge.svg)](https://github.com/oatakan/ansible-role-rhel_template_build/actions/workflows/vm-test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ansible Role](https://img.shields.io/ansible/role/d/oatakan/rhel_template_build)](https://galaxy.ansible.com/oatakan/rhel_template_build)

This role turns a minimal Red Hat Enterprise Linux (RHEL) or CentOS system into a golden image that can be safely cloned.  It installs common utilities, configures networking and SSH, enables cloud-init and guest agents, and then cleans the machine so copies boot as if fresh.  You can run the role with the Packer Ansible provisioner or combine it with roles like `oatakan.rhel_vcenter_template` and `oatakan.rhel_ovirt_template` when provisioning directly against your virtualization platform.

## Requirements

* Ansible 2.9 or newer
* Root privileges on the target RHEL/CentOS system
* Optional: access to the virtualization platform (VMware, VirtualBox, Parallels or oVirt) if the associated guest tools should be installed

## Role Variables

The most common variables are listed below. See `defaults/main.yml` for the full list and their default values.

| Variable | Default | Description |
|----------|---------|-------------|
| `target_vagrant` | `false` | When set to `true`, the Vagrant public key is installed for the local user. |
| `target_ovirt` | `false` | Enables cloud-init setup and installs the oVirt/QEMU guest agent. |
| `local_account_username` | `ansible` | User name that owns downloaded ISOs and receives the Vagrant key. |
| `permit_root_login_with_password` | `true` | Allows password based root logins in cloud-init configuration. |
| `parallels_tools_role` | `oatakan.linux_parallels_tools` | Role used to install Parallels guest tools when Parallels is detected. |

## Dependencies

If Parallels guest tools are required, ensure the [`oatakan.linux_parallels_tools`](https://galaxy.ansible.com/oatakan/linux_parallels_tools) role is available. No other external roles are required.

## Example Playbook

```yaml
- name: Build RHEL template
  hosts: build_host
  become: true
  roles:
    - role: oatakan.rhel_template_build
      vars:
        target_vagrant: true
        target_ovirt: false
```

## Testing the role

An automated GitHub Actions workflow runs `ansible-lint` and performs a playbook
syntax check whenever changes are pushed. You can run the same checks locally by
setting `ANSIBLE_ROLES_PATH` to point at the test roles directory:

```bash
ANSIBLE_ROLES_PATH=$(pwd)/tests/roles ansible-lint --offline
ANSIBLE_ROLES_PATH=$(pwd)/tests/roles ansible-playbook -i tests/inventory tests/test.yml --syntax-check
```

To execute integration tests in a containerized environment, install Molecule
and its Docker plugin, then install the required Ansible collection before
running the tests:

```bash
pip install molecule molecule-plugins[docker]
ansible-galaxy collection install community.docker
ANSIBLE_ROLES_PATH=$(pwd)/tests/roles molecule test
```

Docker must be installed and the Docker daemon should be running before
executing the Molecule scenario.

The scenario uses an `ansible.cfg` that sets `remote_tmp` to `/tmp` so
temporary files can be created inside the container. Molecule sets the
`ANSIBLE_CONFIG` environment variable so Ansible loads this configuration.

The Molecule scenario builds a container from `quay.io/rockylinux/rockylinux:9`
and installs `systemd` and Python so the role can run in a Docker container.

## License

MIT

## Author Information

Orcun Atakan
