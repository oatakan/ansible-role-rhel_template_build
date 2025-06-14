#!/usr/bin/env python3
"""
AI-powered release analyzer that determines version bumps and generates release content
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import subprocess

try:
    import openai
    from anthropic import Anthropic
    import git
    import semver
    import yaml
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Install with: pip install openai anthropic GitPython semver pyyaml")
    sys.exit(1)


class AIReleaseAnalyzer:
    def __init__(self):
        self.repo = git.Repo('.')
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')

        # Initialize AI clients
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.ai_client = 'openai'
        elif self.anthropic_api_key:
            self.anthropic = Anthropic(api_key=self.anthropic_api_key)
            self.ai_client = 'anthropic'
        else:
            print("Warning: No AI API keys found. Using rule-based analysis.")
            self.ai_client = None

    def get_latest_tag(self) -> str:
        """Get the latest version tag"""
        try:
            tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)
            for tag in reversed(tags):
                if re.match(r'^v?\d+\.\d+\.\d+$', tag.name):
                    return tag.name
        except:
            pass
        return 'v0.0.0'

    def get_commits_since_tag(self, tag: str) -> List[git.Commit]:
        """Get all commits since the last tag"""
        try:
            if tag == 'v0.0.0':
                # First release, get all commits
                return list(self.repo.iter_commits('main'))
            return list(self.repo.iter_commits(f'{tag}..HEAD'))
        except:
            return []

    def get_changed_files(self, commits: List[git.Commit]) -> Dict[str, List[str]]:
        """Categorize changed files"""
        changes = {
            'tasks': [],
            'vars': [],
            'defaults': [],
            'meta': [],
            'tests': [],
            'docs': [],
            'ci': [],
            'other': []
        }

        for commit in commits:
            for item in commit.diff(commit.parents[0] if commit.parents else None):
                path = item.a_path or item.b_path

                if path.startswith('tasks/'):
                    changes['tasks'].append(path)
                elif path.startswith('vars/') or path.startswith('defaults/'):
                    changes['vars'].append(path)
                elif path.startswith('meta/'):
                    changes['meta'].append(path)
                elif path.startswith('tests/') or path.startswith('molecule/'):
                    changes['tests'].append(path)
                elif path.endswith('.md') or path.startswith('docs/'):
                    changes['docs'].append(path)
                elif path.startswith('.github/'):
                    changes['ci'].append(path)
                else:
                    changes['other'].append(path)

        # Deduplicate
        for key in changes:
            changes[key] = list(set(changes[key]))

        return changes

    def analyze_with_ai(self, commits: List[git.Commit], changed_files: Dict[str, List[str]]) -> Dict:
        """Use AI to analyze commits and determine version bump"""

        # Prepare commit data
        commit_messages = [f"- {c.summary}" for c in commits[:50]]  # Limit to 50 most recent
        commit_text = "\n".join(commit_messages)

        # Prepare file changes summary
        changes_summary = []
        for category, files in changed_files.items():
            if files:
                changes_summary.append(f"{category}: {len(files)} files changed")

        prompt = f"""Analyze these changes to an Ansible role and determine the appropriate semantic version bump.

Recent commits:
{commit_text}

File changes by category:
{chr(10).join(changes_summary)}

Changed files in tasks (core functionality):
{chr(10).join(changed_files.get('tasks', [])[:10])}

Rules for semantic versioning:
- PATCH: Bug fixes, documentation, minor improvements
- MINOR: New features, new variables (with defaults), new OS support
- MAJOR: Breaking changes, removed features, changed defaults, dropped OS support

Analyze the commits for:
1. Breaking changes (removed vars, changed behavior, dropped support)
2. New features (new functionality, new OS support)
3. Bug fixes
4. Whether a release is warranted

Respond with a JSON object:
{{
    "should_release": true/false,
    "version_bump": "major/minor/patch",
    "reasoning": "Brief explanation",
    "breaking_changes": ["list of breaking changes if any"],
    "new_features": ["list of new features"],
    "bug_fixes": ["list of bug fixes"],
    "changelog_entry": "Formatted changelog entry text"
}}"""

        try:
            if self.ai_client == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": "You are an expert in semantic versioning and Ansible development."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                result = json.loads(response.choices[0].message.content)

            elif self.ai_client == 'anthropic':
                response = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    temperature=0.3,
                    system="You are an expert in semantic versioning and Ansible development.",
                    messages=[{"role": "user", "content": prompt}]
                )
                result = json.loads(response.content[0].text)

            else:
                # Fallback to rule-based analysis
                result = self.rule_based_analysis(commits, changed_files)

            return result

        except Exception as e:
            print(f"AI analysis failed: {e}")
            return self.rule_based_analysis(commits, changed_files)

    def rule_based_analysis(self, commits: List[git.Commit], changed_files: Dict[str, List[str]]) -> Dict:
        """Fallback rule-based analysis"""
        version_bump = 'patch'
        breaking_changes = []
        new_features = []
        bug_fixes = []

        # Check commit messages for keywords
        for commit in commits:
            msg = commit.message.lower()

            if any(word in msg for word in ['breaking', 'remove', 'drop support']):
                version_bump = 'major'
                breaking_changes.append(commit.summary)
            elif any(word in msg for word in ['feat:', 'feature', 'add support', 'new']):
                if version_bump != 'major':
                    version_bump = 'minor'
                new_features.append(commit.summary)
            elif any(word in msg for word in ['fix:', 'bug', 'repair', 'correct']):
                bug_fixes.append(commit.summary)

        # Check file changes
        if changed_files.get('vars') or changed_files.get('defaults'):
            if version_bump == 'patch':
                version_bump = 'minor'  # Assume new vars are added with defaults

        should_release = len(commits) > 0

        # Build changelog entry
        changelog_parts = []
        if breaking_changes:
            changelog_parts.append("### Breaking Changes\n" + "\n".join(f"- {c}" for c in breaking_changes[:5]))
        if new_features:
            changelog_parts.append("### Added\n" + "\n".join(f"- {c}" for c in new_features[:5]))
        if bug_fixes:
            changelog_parts.append("### Fixed\n" + "\n".join(f"- {c}" for c in bug_fixes[:5]))

        changelog_entry = "\n\n".join(
            changelog_parts) if changelog_parts else "### Changed\n- Minor updates and improvements"

        return {
            "should_release": should_release,
            "version_bump": version_bump,
            "reasoning": f"Found {len(commits)} commits with {version_bump} level changes",
            "breaking_changes": breaking_changes[:5],
            "new_features": new_features[:5],
            "bug_fixes": bug_fixes[:5],
            "changelog_entry": changelog_entry
        }

    def generate_release_notes(self, analysis: Dict, version: str) -> str:
        """Generate comprehensive release notes"""

        if self.ai_client:
            prompt = f"""Generate engaging release notes for Ansible role version {version}.

Analysis results:
{json.dumps(analysis, indent=2)}

Create release notes that:
1. Start with a brief summary
2. Highlight key changes
3. Include upgrade instructions if breaking changes
4. Add installation command
5. Thank contributors

Keep it concise but informative. Use emoji sparingly for key sections."""

            try:
                if self.ai_client == 'openai':
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a technical writer creating release notes."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7
                    )
                    return response.choices[0].message.content

                elif self.ai_client == 'anthropic':
                    response = self.anthropic.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=1000,
                        temperature=0.7,
                        system="You are a technical writer creating release notes.",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
            except:
                pass

        # Fallback template
        notes = f"""## 🎉 Release {version}

### What's New

{analysis.get('changelog_entry', 'Various improvements and bug fixes')}

### Installation

```bash
ansible-galaxy install oatakan.rhel_template_build,{version}
```

### Compatibility

- Ansible >= 2.9
- RHEL/CentOS/Rocky/Alma Linux 7, 8, 9, 10

**Full Changelog**: https://github.com/oatakan/ansible-role-rhel_template_build/blob/main/CHANGELOG.md
"""
        return notes

    def run(self):
        """Main analysis flow"""
        latest_tag = self.get_latest_tag()
        commits = self.get_commits_since_tag(latest_tag)

        if not commits and os.environ.get('FORCE_RELEASE', '').lower() != 'true':
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("should_release=false\n")
            print("No commits since last release")
            return

        changed_files = self.get_changed_files(commits)
        analysis = self.analyze_with_ai(commits, changed_files)

        # Calculate new version
        current_version = latest_tag.lstrip('v')
        try:
            v = semver.Version.parse(current_version)
            if analysis['version_bump'] == 'major':
                new_version = str(v.bump_major())
            elif analysis['version_bump'] == 'minor':
                new_version = str(v.bump_minor())
            else:
                new_version = str(v.bump_patch())
        except:
            new_version = '0.1.0'

        release_notes = self.generate_release_notes(analysis, f'v{new_version}')

        # Output for GitHub Actions
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"should_release={str(analysis['should_release']).lower()}\n")
            f.write(f"version_bump={analysis['version_bump']}\n")
            f.write(f"analysis_reasoning={analysis['reasoning']}\n")
            f.write(f"changelog_entry<<EOF\n{analysis['changelog_entry']}\nEOF\n")
            f.write(f"release_notes<<EOF\n{release_notes}\nEOF\n")


if __name__ == '__main__':
    analyzer = AIReleaseAnalyzer()
    analyzer.run()