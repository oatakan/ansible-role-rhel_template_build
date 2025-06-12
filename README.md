# oatakan.rhel_template_build

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
syntax check whenever changes are pushed. You can run the same checks locally:

```bash
ansible-lint
ansible-playbook -i tests/inventory tests/test.yml --syntax-check
```

To execute integration tests in a containerized environment, install Molecule
and its Docker plugin before running the tests:

```bash
pip install molecule molecule-plugins[docker]
molecule test
```

## License

MIT

## Author Information

Orcun Atakan
