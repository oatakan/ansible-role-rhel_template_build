#!/usr/bin/env python3
"""
AI-powered documentation updater
"""

import os
import sys
import argparse
import re
from datetime import datetime
from typing import Dict, List
import subprocess

try:
    import openai
    from anthropic import Anthropic
    import yaml
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    sys.exit(1)


class AIDocUpdater:
    def __init__(self, version: str):
        self.version = version
        self.setup_ai_clients()

    def setup_ai_clients(self):
        """Setup AI clients"""
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')

        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.ai_client = 'openai'
        elif self.anthropic_api_key:
            self.anthropic = Anthropic(api_key=self.anthropic_api_key)
            self.ai_client = 'anthropic'
        else:
            self.ai_client = None

    def get_recent_changes(self) -> Dict:
        """Get recent changes from git"""
        try:
            # Get commits since last tag
            last_tag = subprocess.check_output(
                ['git', 'describe', '--tags', '--abbrev=0'],
                text=True
            ).strip()

            commits = subprocess.check_output(
                ['git', 'log', f'{last_tag}..HEAD', '--oneline'],
                text=True
            ).strip().split('\n')

            # Get changed files
            changed_files = subprocess.check_output(
                ['git', 'diff', '--name-only', f'{last_tag}..HEAD'],
                text=True
            ).strip().split('\n')

            return {
                'commits': commits,
                'changed_files': changed_files
            }
        except:
            return {'commits': [], 'changed_files': []}

    def analyze_variable_changes(self) -> Dict[str, List[str]]:
        """Analyze changes to variables"""
        changes = {'added': [], 'modified': [], 'removed': []}

        # Check defaults/main.yml
        defaults_file = 'defaults/main.yml'
        if os.path.exists(defaults_file):
            try:
                # Get current variables
                with open(defaults_file, 'r') as f:
                    current_vars = yaml.safe_load(f) or {}

                # Try to get previous version
                try:
                    last_tag = subprocess.check_output(
                        ['git', 'describe', '--tags', '--abbrev=0'],
                        text=True
                    ).strip()

                    old_content = subprocess.check_output(
                        ['git', 'show', f'{last_tag}:{defaults_file}'],
                        text=True
                    )
                    old_vars = yaml.safe_load(old_content) or {}

                    # Compare
                    for var in current_vars:
                        if var not in old_vars:
                            changes['added'].append(var)
                        elif current_vars[var] != old_vars[var]:
                            changes['modified'].append(var)

                    for var in old_vars:
                        if var not in current_vars:
                            changes['removed'].append(var)
                except:
                    # If can't get old version, all are new
                    changes['added'] = list(current_vars.keys())
            except:
                pass

        return changes

    def update_readme_with_ai(self, var_changes: Dict[str, List[str]]) -> bool:
        """Update README.md with AI assistance"""

        if not self.ai_client or not any(var_changes.values()):
            return False

        readme_path = 'README.md'
        if not os.path.exists(readme_path):
            return False

        with open(readme_path, 'r') as f:
            readme_content = f.read()

        # Load current variables
        with open('defaults/main.yml', 'r') as f:
            current_vars = yaml.safe_load(f) or {}

        prompt = f"""Update the Role Variables section of this README with these changes:

New variables added:
{chr(10).join(f'- {var}: {current_vars.get(var, "...")}' for var in var_changes['added'])}

Modified variables:
{chr(10).join(f'- {var}' for var in var_changes['modified'])}

Removed variables:
{chr(10).join(f'- {var}' for var in var_changes['removed'])}

Current README excerpt:
{readme_content[readme_content.find('## Role Variables'):readme_content.find('## Dependencies')] if '## Role Variables' in readme_content else 'No variables section found'}

Provide the updated Role Variables section in markdown format. Include:
1. Variable name
2. Default value
3. Brief description
4. Mark new variables with '(New in v{self.version})'

Keep the existing format and style."""

        try:
            if self.ai_client == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a technical documentation writer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                updated_section = response.choices[0].message.content
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    temperature=0.3,
                    system="You are a technical documentation writer.",
                    messages=[{"role": "user", "content": prompt}]
                )
                updated_section = response.content[0].text

            # Replace the variables section
            if '## Role Variables' in readme_content and '## Dependencies' in readme_content:
                start = readme_content.find('## Role Variables')
                end = readme_content.find('## Dependencies')
                new_readme = readme_content[:start] + updated_section + '\n\n' + readme_content[end:]

                with open(readme_path, 'w') as f:
                    f.write(new_readme)

                return True
        except:
            pass

        return False

    def add_version_badge(self):
        """Update version badge in README"""
        readme_path = 'README.md'
        if not os.path.exists(readme_path):
            return

        with open(readme_path, 'r') as f:
            content = f.read()

        # Update or add version badge
        version_badge = f"[![Galaxy Version](https://img.shields.io/badge/galaxy-v{self.version}-blue.svg)](https://galaxy.ansible.com/oatakan/rhel_template_build)"

        # Replace existing version badge or add after title
        if 'img.shields.io/badge/galaxy-v' in content:
            content = re.sub(
                r'\[!\[Galaxy Version\]\(https://img\.shields\.io/badge/galaxy-v[\d.]+-blue\.svg\)\]\([^)]+\)',
                version_badge,
                content
            )
        else:
            # Add after first line (title)
            lines = content.split('\n')
            lines.insert(2, version_badge)
            content = '\n'.join(lines)

        with open(readme_path, 'w') as f:
            f.write(content)

    def run(self):
        """Main execution"""
        print(f"📚 Updating documentation for version {self.version}")

        # Get recent changes
        changes = self.get_recent_changes()

        # Analyze variable changes
        var_changes = self.analyze_variable_changes()

        # Update README
        if var_changes['added'] or var_changes['modified'] or var_changes['removed']:
            print("Found variable changes, updating README...")
            if self.update_readme_with_ai(var_changes):
                print("✅ Updated README.md variable section")
            else:
                print("⚠️  Could not update variables section automatically")

        # Update version badge
        self.add_version_badge()
        print("✅ Updated version badge")

        # Update copyright year if needed
        current_year = str(datetime.now().year)
        for file in ['LICENSE', 'README.md']:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    content = f.read()

                if current_year not in content and 'Copyright' in content:
                    content = re.sub(
                        r'Copyright \(c\) \d{4}',
                        f'Copyright (c) {current_year}',
                        content
                    )
                    with open(file, 'w') as f:
                        f.write(content)
                    print(f"✅ Updated copyright year in {file}")


def main():
    parser = argparse.ArgumentParser(description='AI Documentation Updater')
    parser.add_argument('--version', required=True, help='Version number')
    args = parser.parse_args()

    updater = AIDocUpdater(args.version)
    updater.run()


if __name__ == '__main__':
    main()