#!/bin/bash
# Release helper script for rhel_template_build role

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}!${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    print_error "You must be on main/master branch to release"
    exit 1
fi

# Ensure working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    print_error "Working directory is not clean. Commit or stash changes."
    exit 1
fi

# Pull latest changes
print_warning "Pulling latest changes..."
git pull origin "$CURRENT_BRANCH"

# Get current version
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
print_success "Current version: $LATEST_TAG"

# Prompt for release type
echo ""
echo "Select release type:"
echo "  1) Patch (bug fixes)"
echo "  2) Minor (new features, backwards compatible)"
echo "  3) Major (breaking changes)"
echo "  4) Custom version"
read -p "Enter choice [1-4]: " choice

# Calculate new version
case $choice in
    1|2|3)
        LATEST_VERSION=${LATEST_TAG#v}
        IFS='.' read -r MAJOR MINOR PATCH <<< "$LATEST_VERSION"

        case $choice in
            1) PATCH=$((PATCH + 1)) ;;
            2) MINOR=$((MINOR + 1)); PATCH=0 ;;
            3) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
        esac

        NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
        ;;
    4)
        read -p "Enter version (without v prefix): " NEW_VERSION
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

NEW_TAG="v${NEW_VERSION}"
print_success "New version will be: $NEW_TAG"

# Confirmation
echo ""
read -p "Continue with release $NEW_TAG? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Release cancelled"
    exit 0
fi

# Run tests
echo ""
print_warning "Running tests..."
if command -v molecule &> /dev/null; then
    print_warning "Running molecule tests (this may take a while)..."
    if ! molecule test; then
        print_error "Tests failed! Fix issues before releasing."
        exit 1
    fi
else
    print_warning "Molecule not installed, skipping integration tests"
fi

if command -v ansible-lint &> /dev/null; then
    print_warning "Running ansible-lint..."
    if ! ansible-lint; then
        print_error "Linting failed! Fix issues before releasing."
        exit 1
    fi
fi

print_success "All tests passed!"

# Update CHANGELOG if it exists
if [ -f CHANGELOG.md ]; then
    print_warning "Don't forget to update CHANGELOG.md!"
    read -p "Have you updated CHANGELOG.md? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please update CHANGELOG.md before releasing"
        exit 1
    fi
fi

# Create and push tag
print_warning "Creating tag $NEW_TAG..."
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"

print_warning "Pushing tag to origin..."
git push origin "$NEW_TAG"

print_success "Release $NEW_TAG created successfully!"

echo ""
echo "Next steps:"
echo "1. Check GitHub Actions for automated Galaxy deployment"
echo "2. Verify release on https://galaxy.ansible.com/oatakan/rhel_template_build"
echo "3. Check GitHub releases page"

# Check if we have the Galaxy API key configured
if [ -z "$ANSIBLE_GALAXY_API_KEY" ]; then
    echo ""
    print_warning "Note: ANSIBLE_GALAXY_API_KEY not set locally."
    print_warning "Ensure it's configured in GitHub Secrets for automatic deployment."
fi