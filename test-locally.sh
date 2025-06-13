#!/bin/bash
# Enhanced local testing script for the rhel_template_build role

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Check if running from role directory
if [ ! -f "meta/main.yml" ]; then
    print_error "This script must be run from the role directory"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
MOLECULE_DISTRO="${2:-rockylinux:9}"
VERBOSE="${3:-false}"

# Set debug flag
if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "debug" ]; then
    set -x
    export ANSIBLE_DEBUG=1
    export MOLECULE_DEBUG=1
fi

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    print_debug "Docker version: $(docker --version)"
    print_debug "Docker info: $(docker system df)"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed"
        exit 1
    fi

    print_debug "Python version: $(python3 --version)"

    # Check available disk space
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    if [ "$AVAILABLE_SPACE" -lt 2000000 ]; then  # Less than 2GB
        print_warning "Low disk space available: ${AVAILABLE_SPACE}KB"
        print_status "Cleaning up Docker to free space..."
        docker system prune -f
    fi
}

# Function to run linting
run_lint() {
    print_status "Running static analysis (linting)..."

    print_status "Running YAML lint..."
    if command -v yamllint &> /dev/null; then
        yamllint . || {
            print_warning "YAML lint found issues"
            return 1
        }
    else
        print_warning "yamllint not installed, skipping"
    fi

    print_status "Running Ansible lint..."
    if command -v ansible-lint &> /dev/null; then
        # Ensure collections are installed before linting
        ansible-galaxy collection install community.general ansible.posix --force
        ansible-lint . || {
            print_warning "Ansible lint found issues"
            return 1
        }
    else
        print_warning "ansible-lint not installed, skipping"
    fi

    print_status "✓ Linting completed successfully"
}

# Function to run syntax check
run_syntax() {
    print_status "Running Ansible syntax check..."

    # Create temporary role structure
    TEMP_ROLES_DIR="/tmp/test-roles-$$"
    mkdir -p "$TEMP_ROLES_DIR"
    ln -sf "$(pwd)" "$TEMP_ROLES_DIR/oatakan.rhel_template_build"

    # Ensure collections are available
    ansible-galaxy collection install community.general ansible.posix --force

    ANSIBLE_ROLES_PATH="$TEMP_ROLES_DIR" ansible-playbook \
        -i tests/inventory tests/test.yml --syntax-check

    # Cleanup
    rm -rf "$TEMP_ROLES_DIR"

    print_status "✓ Syntax check passed"
}

# Function to run molecule tests
run_molecule() {
    print_status "Running Molecule tests with $MOLECULE_DISTRO..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    # Clean up any existing molecule instances
    print_status "Cleaning up any existing molecule instances..."
    cd molecule/default
    molecule destroy || true
    cd ../..

    # Export the distro
    export MOLECULE_DISTRO

    # Set additional environment variables for better debugging
    export ANSIBLE_FORCE_COLOR=1
    export PY_COLORS=1
    export ANSIBLE_HOST_KEY_CHECKING=false

    if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "debug" ]; then
        export MOLECULE_DEBUG=1
        export ANSIBLE_VERBOSITY=3
    fi

    print_status "Starting molecule test sequence..."
    print_debug "Using distro: $MOLECULE_DISTRO"
    print_debug "Working directory: $(pwd)"

    # Run molecule with error handling
    cd molecule/default

    # Run each step individually for better error reporting
    print_status "Step 1/8: Dependency resolution..."
    molecule dependency

    print_status "Step 2/8: Syntax check..."
    molecule syntax

    print_status "Step 3/8: Creating instances..."
    molecule create

    print_status "Step 4/8: Preparing instances..."
    molecule prepare

    print_status "Step 5/8: Running role..."
    molecule converge

    print_status "Step 6/8: Testing idempotence..."
    molecule idempotence

    print_status "Step 7/8: Running verification..."
    molecule verify

    print_status "Step 8/8: Destroying instances..."
    molecule destroy

    cd ../..

    print_status "✓ Molecule tests completed successfully"
}

# Function to install dependencies
install_deps() {
    print_status "Installing Python dependencies..."
    python3 -m pip install --upgrade pip
    pip3 install \
        'ansible-core>=2.14,<2.17' \
        ansible-lint \
        yamllint \
        molecule \
        'molecule-plugins[docker]'

    print_status "Installing Ansible collections..."
    ansible-galaxy collection install \
        community.general \
        community.docker \
        ansible.posix \
        --force

    print_status "✓ Dependencies installed successfully"
}

# Function to run debug mode
run_debug() {
    print_status "Running in debug mode..."
    export MOLECULE_DEBUG=1
    export ANSIBLE_DEBUG=1
    export ANSIBLE_VERBOSITY=4

    print_status "Available Docker images:"
    docker images | head -10

    print_status "Docker system info:"
    docker system df

    print_status "Available collections:"
    ansible-galaxy collection list

    print_status "Running molecule create and login..."
    cd molecule/default
    export MOLECULE_DISTRO
    molecule create

    print_status "Container is running. You can now:"
    echo "  molecule login    # to enter the container"
    echo "  molecule converge # to run the role"
    echo "  molecule verify   # to run tests"
    echo "  molecule destroy  # to clean up"

    cd ../..
}

# Function to clean up everything
cleanup() {
    print_status "Cleaning up test environment..."

    # Clean up molecule
    if [ -d "molecule/default" ]; then
        cd molecule/default
        molecule destroy || true
        cd ../..
    fi

    # Clean up Docker
    docker system prune -f

    # Clean up temporary files
    rm -rf /tmp/test-roles-*

    print_status "✓ Cleanup completed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [command] [distro] [verbose]"
    echo ""
    echo "Commands:"
    echo "  lint      - Run yamllint and ansible-lint"
    echo "  syntax    - Run Ansible syntax check"
    echo "  molecule  - Run Molecule tests"
    echo "  debug     - Run molecule create and enter debug mode"
    echo "  install   - Install dependencies"
    echo "  cleanup   - Clean up test environment"
    echo "  all       - Run all tests (default)"
    echo ""
    echo "Distro options for molecule tests:"
    echo "  rockylinux:8"
    echo "  rockylinux:9 (default)"
    echo "  almalinux:8"
    echo "  almalinux:9"
    echo ""
    echo "Verbose options:"
    echo "  false     - Normal output (default)"
    echo "  true      - Verbose output"
    echo "  debug     - Maximum debug output"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Run all tests with defaults"
    echo "  $0 molecule rockylinux:8  # Test specific distro"
    echo "  $0 debug rockylinux:9 true # Debug mode with verbose output"
    echo "  $0 cleanup               # Clean up everything"
}

# Trap to cleanup on exit
trap cleanup EXIT

# Main execution
print_status "Starting tests for rhel_template_build role"
print_debug "Command: $TEST_TYPE, Distro: $MOLECULE_DISTRO, Verbose: $VERBOSE"

case "$TEST_TYPE" in
    lint)
        check_prerequisites
        run_lint
        ;;
    syntax)
        check_prerequisites
        run_syntax
        ;;
    molecule)
        check_prerequisites
        run_molecule
        ;;
    debug)
        check_prerequisites
        run_debug
        # Don't exit, let user interact
        trap - EXIT
        exit 0
        ;;
    install)
        install_deps
        ;;
    cleanup)
        cleanup
        ;;
    all)
        check_prerequisites
        run_lint
        echo ""
        run_syntax
        echo ""
        run_molecule
        ;;
    help|--help|-h)
        show_usage
        exit 0
        ;;
    *)
        print_error "Unknown command: $TEST_TYPE"
        show_usage
        exit 1
        ;;
esac

print_status "✓ All tests completed successfully!"
print_status "Your role is ready for production use."