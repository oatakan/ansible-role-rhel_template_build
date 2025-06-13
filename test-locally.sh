#!/bin/bash
# Local testing script for the rhel_template_build role

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if running from role directory
if [ ! -f "meta/main.yml" ]; then
    print_error "This script must be run from the role directory"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
MOLECULE_DISTRO="${2:-rockylinux:9}"

# Function to run linting
run_lint() {
    print_status "Running YAML lint..."
    if command -v yamllint &> /dev/null; then
        yamllint . || print_warning "YAML lint found issues"
    else
        print_warning "yamllint not installed, skipping"
    fi

    print_status "Running Ansible lint..."
    if command -v ansible-lint &> /dev/null; then
        # Ensure collections are installed before linting
        ansible-galaxy collection install community.general ansible.posix --force
        ansible-lint || print_warning "Ansible lint found issues"
    else
        print_warning "ansible-lint not installed, skipping"
    fi
}

# Function to run syntax check
run_syntax() {
    print_status "Running syntax check..."

    # Create temporary role structure
    mkdir -p /tmp/test-roles
    ln -sf "$(pwd)" /tmp/test-roles/oatakan.rhel_template_build

    ANSIBLE_ROLES_PATH=/tmp/test-roles ansible-playbook -i tests/inventory tests/test.yml --syntax-check

    # Cleanup
    rm -rf /tmp/test-roles
}

# Function to run molecule tests
run_molecule() {
    print_status "Running Molecule tests with $MOLECULE_DISTRO..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    # Export the distro
    export MOLECULE_DISTRO

    # Run molecule
    cd molecule/default
    molecule test
    cd ../..
}

# Function to install dependencies
install_deps() {
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install ansible ansible-lint yamllint molecule molecule-plugins[docker]

    print_status "Installing Ansible collections..."
    ansible-galaxy collection install community.general community.docker ansible.posix
}

# Main execution
case "$TEST_TYPE" in
    lint)
        run_lint
        ;;
    syntax)
        run_syntax
        ;;
    molecule)
        run_molecule
        ;;
    install)
        install_deps
        ;;
    all)
        run_lint
        echo ""
        run_syntax
        echo ""
        run_molecule
        ;;
    *)
        echo "Usage: $0 [lint|syntax|molecule|install|all] [distro]"
        echo "  lint     - Run yamllint and ansible-lint"
        echo "  syntax   - Run Ansible syntax check"
        echo "  molecule - Run Molecule tests"
        echo "  install  - Install dependencies"
        echo "  all      - Run all tests (default)"
        echo ""
        echo "Distro options for molecule tests:"
        echo "  rockylinux:8"
        echo "  rockylinux:9 (default)"
        echo "  almalinux:8"
        echo "  almalinux:9"
        echo ""
        echo "Example: $0 molecule rockylinux:8"
        exit 1
        ;;
esac

print_status "Testing completed!"