#!/bin/bash
# Setup script for AI-powered automation

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
print_header() { echo -e "\n${BLUE}=== $1 ===${NC}\n"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}!${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

# Check if running from repo root
if [ ! -f "meta/main.yml" ]; then
    print_error "This script must be run from the repository root"
    exit 1
fi

print_header "AI-Powered Automation Setup"

# Step 1: Check for required files
print_header "Checking repository structure"

required_files=(
    ".github/workflows/auto-release.yml"
    ".github/workflows/pr-enrichment.yml"
    ".github/scripts/ai_release_analyzer.py"
    ".github/scripts/ai_pr_analyzer.py"
    ".github/scripts/ai_pr_assistant.py"
    ".github/scripts/update_changelog.py"
    ".github/scripts/ai_doc_updater.py"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found $file"
    else
        missing_files+=("$file")
        print_warning "Missing $file"
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    print_error "Missing required files. Please ensure all automation files are present."
    exit 1
fi

# Step 2: Make scripts executable
print_header "Setting script permissions"

find .github/scripts -name "*.py" -exec chmod +x {} \;
find scripts -name "*.sh" -exec chmod +x {} \;
print_success "Scripts are now executable"

# Step 3: Check Python dependencies
print_header "Checking Python environment"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

print_info "Python version: $(python3 --version)"

# Create requirements file for automation
cat > .github/scripts/requirements.txt << 'EOF'
openai>=1.0.0
anthropic>=0.18.0
PyGithub>=2.1.0
GitPython>=3.1.40
semver>=3.0.0
pyyaml>=6.0
EOF

print_success "Created requirements.txt for automation scripts"

# Step 4: Check GitHub secrets
print_header "GitHub Secrets Configuration"

echo "You need to configure the following secrets in your GitHub repository:"
echo ""
echo "1. ${GREEN}ANSIBLE_GALAXY_API_KEY${NC} (Required)"
echo "   - Get from: https://galaxy.ansible.com/me/preferences"
echo "   - Add at: Settings → Secrets and variables → Actions"
echo ""
echo "2. ${YELLOW}OPENAI_API_KEY${NC} (Optional but recommended)"
echo "   - Get from: https://platform.openai.com/api-keys"
echo "   - Enables GPT-4 powered analysis"
echo ""
echo "3. ${YELLOW}ANTHROPIC_API_KEY${NC} (Optional alternative)"
echo "   - Get from: https://console.anthropic.com/settings/keys"
echo "   - Enables Claude powered analysis"
echo ""

read -p "Have you configured at least ANSIBLE_GALAXY_API_KEY? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Please configure the required secrets before using automation"
fi

# Step 5: Initialize changelog if needed
print_header "Checking documentation"

if [ ! -f "CHANGELOG.md" ]; then
    print_info "Creating initial CHANGELOG.md"
    cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- AI-powered release automation
- Automated changelog generation
- PR enhancement with AI insights

[Unreleased]: https://github.com/oatakan/ansible-role-rhel_template_build/compare/v1.0.0...HEAD
EOF
    print_success "Created CHANGELOG.md"
else
    print_success "CHANGELOG.md exists"
fi

# Step 6: Git configuration
print_header "Git Configuration"

# Check if we have any tags
if ! git describe --tags --abbrev=0 &> /dev/null; then
    print_warning "No git tags found"
    read -p "Create initial tag v1.0.0? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -a v1.0.0 -m "Initial release"
        print_success "Created tag v1.0.0"
        print_info "Remember to push tags: git push origin v1.0.0"
    fi
else
    current_tag=$(git describe --tags --abbrev=0)
    print_success "Current version: $current_tag"
fi

# Step 7: Test automation locally
print_header "Testing Automation Setup"

print_info "You can test the automation locally:"
echo ""
echo "1. Test AI analysis (dry run):"
echo "   export GITHUB_OUTPUT=/tmp/github_output"
echo "   python3 .github/scripts/ai_release_analyzer.py"
echo ""
echo "2. Test PR analysis:"
echo "   python3 .github/scripts/ai_pr_analyzer.py --pr-number <PR_NUMBER>"
echo ""

# Step 8: Summary
print_header "Setup Complete! 🎉"

echo "Next steps:"
echo ""
echo "1. ${GREEN}Configure GitHub Secrets${NC}"
echo "   - Add ANSIBLE_GALAXY_API_KEY (required)"
echo "   - Add AI API keys (recommended)"
echo ""
echo "2. ${GREEN}Enable GitHub Actions${NC}"
echo "   - Should be enabled by default"
echo "   - Check: Settings → Actions → General"
echo ""
echo "3. ${GREEN}Make your first automated release${NC}"
echo "   - Commit changes to main branch"
echo "   - AI will analyze and create release automatically"
echo ""
echo "4. ${GREEN}Try PR enhancement${NC}"
echo "   - Create a PR and watch AI analyze it"
echo "   - Use /ai commands in PR comments"
echo ""

print_info "For more information, see AI_AUTOMATION.md"

# Optional: Show cost estimate
print_header "Cost Estimate"

echo "Estimated monthly costs for AI features:"
echo "- Small project (< 50 PRs): ~\$5-10"
echo "- Medium project (50-200 PRs): ~\$20-40"
echo "- Large project (> 200 PRs): ~\$50-100"
echo ""
echo "Note: Costs only apply if using AI APIs (OpenAI/Anthropic)"
echo "System works without AI using rule-based analysis (free)"

print_success "Setup complete! Your repository is ready for AI-powered automation."