#!/usr/bin/env python3
"""
AI-powered PR analyzer that enriches pull requests with intelligent insights
"""

import os
import sys
import argparse
import json
import re
from typing import Dict, List, Optional

try:
    import openai
    from anthropic import Anthropic
    from github import Github
    import git
    import yaml
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    sys.exit(1)


class AIPRAnalyzer:
    def __init__(self, pr_number: int):
        self.pr_number = pr_number
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_name = os.environ.get('GITHUB_REPOSITORY')

        # Initialize GitHub client
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)
        self.pr = self.repo.get_pull(pr_number)

        # Initialize AI clients
        self.setup_ai_clients()

    def setup_ai_clients(self):
        """Setup AI clients based on available API keys"""
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

    def get_pr_diff(self) -> str:
        """Get the PR diff"""
        files = self.pr.get_files()
        diff_content = []

        for file in files:
            if file.patch:
                diff_content.append(f"File: {file.filename}")
                diff_content.append(file.patch[:2000])  # Limit size
                diff_content.append("---")

        return "\n".join(diff_content)

    def analyze_pr_with_ai(self, diff: str) -> Dict:
        """Use AI to analyze the PR"""

        prompt = f"""Analyze this Ansible role pull request and provide insights.

PR Title: {self.pr.title}
PR Description: {self.pr.body or 'No description provided'}

Changed Files:
{chr(10).join([f.filename for f in self.pr.get_files()])}

Sample Diff:
{diff[:3000]}

Provide a comprehensive analysis including:
1. Summary of changes (2-3 sentences)
2. Type of change (feature/bugfix/enhancement/breaking)
3. Risk assessment (low/medium/high)
4. Testing recommendations
5. Code quality observations
6. Compatibility concerns
7. Documentation needs

Format as JSON with these keys:
- summary: str
- change_type: str
- risk_level: str
- testing_recommendations: list[str]
- code_quality_notes: list[str]
- compatibility_notes: list[str]
- documentation_needs: list[str]
- suggested_reviewers: list[str] (based on expertise needed)
- estimated_review_time: str (in minutes)"""

        try:
            if self.ai_client == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert Ansible developer and code reviewer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                return json.loads(response.choices[0].message.content)

            elif self.ai_client == 'anthropic':
                response = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1500,
                    temperature=0.3,
                    system="You are an expert Ansible developer and code reviewer.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return json.loads(response.content[0].text)
        except:
            return self.basic_analysis()

    def basic_analysis(self) -> Dict:
        """Fallback basic analysis without AI"""
        files = list(self.pr.get_files())

        # Determine change type
        change_type = 'enhancement'
        if 'fix' in self.pr.title.lower():
            change_type = 'bugfix'
        elif 'feat' in self.pr.title.lower():
            change_type = 'feature'

        # Risk assessment based on files changed
        risk_level = 'low'
        if any('tasks/main.yml' in f.filename for f in files):
            risk_level = 'medium'
        if any(f.filename.startswith('defaults/') for f in files):
            risk_level = 'high'

        return {
            'summary': f"PR modifies {len(files)} files",
            'change_type': change_type,
            'risk_level': risk_level,
            'testing_recommendations': ['Run molecule tests', 'Test on target platforms'],
            'code_quality_notes': ['Manual review required'],
            'compatibility_notes': [],
            'documentation_needs': ['Update README if needed'],
            'suggested_reviewers': [],
            'estimated_review_time': '15-30'
        }

    def generate_pr_comment(self, analysis: Dict) -> str:
        """Generate a comprehensive PR comment"""

        # Risk emoji
        risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(analysis['risk_level'], '⚪')

        comment = f"""## 🤖 AI Pull Request Analysis

### Summary
{analysis['summary']}

### Metadata
- **Change Type:** {analysis['change_type'].title()}
- **Risk Level:** {risk_emoji} {analysis['risk_level'].title()}
- **Estimated Review Time:** {analysis['estimated_review_time']} minutes

### Testing Recommendations
{chr(10).join(f'- {rec}' for rec in analysis['testing_recommendations'])}

### Code Quality Notes
{chr(10).join(f'- {note}' for note in analysis['code_quality_notes']) if analysis['code_quality_notes'] else '✅ No issues identified'}

### Compatibility Considerations
{chr(10).join(f'- {note}' for note in analysis['compatibility_notes']) if analysis['compatibility_notes'] else '✅ No compatibility concerns identified'}

### Documentation Needs
{chr(10).join(f'- {need}' for need in analysis['documentation_needs']) if analysis['documentation_needs'] else '✅ Documentation appears complete'}

---

<details>
<summary>💡 AI Assistant Commands</summary>

You can interact with the AI assistant using these commands in comments:

- `/ai review` - Request a detailed code review
- `/ai test` - Generate test scenarios
- `/ai docs` - Generate documentation updates
- `/ai changelog` - Generate changelog entry
- `/ai improve` - Suggest improvements

</details>

<sub>This analysis was performed by AI and should be verified by human reviewers.</sub>"""

        return comment

    def update_pr_description(self, analysis: Dict):
        """Enhance PR description with structured data"""

        current_body = self.pr.body or ""

        # Don't update if already has our metadata
        if "<!-- ai-metadata" in current_body:
            return

        metadata = f"""
<!-- ai-metadata
change_type: {analysis['change_type']}
risk_level: {analysis['risk_level']}
auto_generated: true
-->

## AI-Enhanced Description

{analysis['summary']}

### Changes Made
{current_body}

### Testing
{chr(10).join(f'- [ ] {rec}' for rec in analysis['testing_recommendations'])}

### Checklist
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Changelog entry added (if needed)
- [ ] Breaking changes documented (if any)
"""

        self.pr.edit(body=metadata)

    def add_labels(self, analysis: Dict):
        """Add appropriate labels based on analysis"""

        labels_to_add = []

        # Change type labels
        if analysis['change_type'] == 'bugfix':
            labels_to_add.append('bug')
        elif analysis['change_type'] == 'feature':
            labels_to_add.append('enhancement')
        elif analysis['change_type'] == 'breaking':
            labels_to_add.append('breaking-change')

        # Risk labels
        if analysis['risk_level'] == 'high':
            labels_to_add.append('needs-careful-review')

        # Documentation labels
        if analysis['documentation_needs']:
            labels_to_add.append('documentation')

        # Add labels if they exist in the repo
        try:
            repo_labels = {label.name for label in self.repo.get_labels()}
            for label in labels_to_add:
                if label in repo_labels:
                    self.pr.add_to_labels(label)
        except:
            pass

    def run(self):
        """Main execution flow"""
        print(f"Analyzing PR #{self.pr_number}")

        # Get PR diff
        diff = self.get_pr_diff()

        # Analyze with AI
        analysis = self.analyze_pr_with_ai(diff)

        # Generate and post comment
        comment = self.generate_pr_comment(analysis)
        self.pr.create_issue_comment(comment)

        # Update PR description
        self.update_pr_description(analysis)

        # Add labels
        self.add_labels(analysis)

        print(f"✅ Successfully enriched PR #{self.pr_number}")


def main():
    parser = argparse.ArgumentParser(description='AI PR Analyzer')
    parser.add_argument('--pr-number', type=int, required=True, help='PR number to analyze')
    args = parser.parse_args()

    analyzer = AIPRAnalyzer(args.pr_number)
    analyzer.run()


if __name__ == '__main__':
    main()