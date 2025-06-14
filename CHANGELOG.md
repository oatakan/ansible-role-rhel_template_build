# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Automated Galaxy deployment via GitHub Actions
- Comprehensive CI/CD pipeline with container and VM testing
- Support for RHEL 10, Rocky Linux 10, and AlmaLinux 10
- Enhanced container detection and compatibility
- Molecule testing framework with multiple OS support

### Changed
- Improved error handling for container environments
- Updated package installation logic for RHEL 10 compatibility
- Enhanced documentation with testing guides

### Fixed
- Hostname reset issues in containerized environments
- Package installation failures in restricted environments

## [v0.0.1] - 2025-06-14

### Changed
- Minor updates and improvements

## [v1.0.0] - 2025-01-01

### Added
- Initial release of rhel_template_build role
- Support for RHEL/CentOS 7, 8, 9
- VMware, VirtualBox, and Parallels guest tools installation
- Cloud-init configuration
- Automatic partition growth
- System cleanup and preparation for templating
- Vagrant box support
- oVirt/RHV integration

### Security
- SSH hardening (disabled DNS lookups, GSSAPI)
- SELinux relabeling on boot

[Unreleased]: https://github.com/oatakan/ansible-role-rhel_template_build/compare/v0.0.1...HEAD
[v1.0.0]: https://github.com/oatakan/ansible-role-rhel_template_build/releases/tag/v1.0.0
[v0.0.1]: https://github.com/oatakan/ansible-role-rhel_template_build/compare/v1.0.0...v0.0.1
