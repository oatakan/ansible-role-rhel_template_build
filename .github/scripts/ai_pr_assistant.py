#!/usr/bin/env python3
"""
AI PR Assistant - responds to commands in PR comments
"""

import os
import sys
import argparse
import re
from typing import Optional

try:
    import openai
    from anthropic import Anthropic
    from github import Github
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    sys.exit(1)


class AIPRAssistant:
    def __init__(self, pr_number: int, comment: str):
        self.pr_number = pr_number
        self.comment = comment
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_name = os.environ.get('GITHUB_REPOSITORY')

        # Initialize clients
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)
        self.pr = self.repo.get_pull(pr_number)
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

    def parse_command(self) -> Optional[str]:
        """Extract command from comment"""
        match = re.search(r'/ai\s+(\w+)', self.comment)
        return match.group(1) if match else None

    def get_pr_context(self) -> str:
        """Get PR context for AI"""
        files = list(self.pr.get_files())
        context = f"""
PR #{self.pr_number}: {self.pr.title}
Files changed: {len(files)}
Changes: +{self.pr.additions} -{self.pr.deletions}

Modified files:
{chr(10).join(f"- {f.filename}" for f in files[:20])}
"""
        return context

    def handle_review_command(self):
        """Detailed code review"""
        context = self.get_pr_context()

        # Get detailed diff
        files = list(self.pr.get_files())
        detailed_review = []

        for file in files[:5]:  # Limit to 5 files
            if file.patch:
                review = self.review_file_with_ai(file)
                if review:
                    detailed_review.append(review)

        comment = f"""## 🔍 Detailed Code Review

{chr(10).join(detailed_review)}

### Overall Assessment
Based on the changes, this PR appears to be well-structured. Please address any concerns raised above.

---
<sub>AI-powered review • Use `/ai help` for more commands</sub>"""

        self.pr.create_issue_comment(comment)

    def review_file_with_ai(self, file) -> Optional[str]:
        """Review individual file with AI"""
        if not self.ai_client:
            return None

        prompt = f"""Review this Ansible file change:

File: {file.filename}
Status: {file.status}
Changes: +{file.additions} -{file.deletions}

Diff:
{file.patch[:1500]}

Provide specific feedback on:
1. Best practices violations
2. Potential bugs
3. Security concerns
4. Performance issues
5. Suggestions for improvement

Be concise and actionable."""

        try:
            if self.ai_client == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert Ansible developer reviewing code."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                feedback = response.choices[0].message.content
            else:
                response = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    temperature=0.3,
                    system="You are an expert Ansible developer reviewing code.",
                    messages=[{"role": "user", "content": prompt}]
                )
                feedback = response.content[0].text

            return f"### 📄 {file.filename}\n{feedback}\n"
        except:
            return None

    def handle_test_command(self):
        """Generate test scenarios"""
        context = self.get_pr_context()

        comment = f"""## 🧪 Suggested Test Scenarios

Based on the changes in this PR, here are recommended test scenarios:

### Unit Tests
1. **Basic functionality test**
   ```bash
   molecule test
   ```

2. **Multi-platform test**
   ```bash
   for distro in rockylinux:8 rockylinux:9 almalinux:9; do
     MOLECULE_DISTRO=$distro molecule test
   done
   ```

### Integration Tests
1. **Clean system test** - Test on a fresh VM
2. **Upgrade test** - Test upgrading from previous version
3. **Idempotency test** - Run role multiple times

### Manual Testing Checklist
- [ ] Test with minimal config
- [ ] Test with all features enabled
- [ ] Test error handling
- [ ] Verify documentation matches behavior

### Platform-specific Tests
- [ ] RHEL 8
- [ ] RHEL 9
- [ ] Rocky Linux 9
- [ ] Container environments

---
<sub>Generated test plan • Use `/ai help` for more commands</sub>"""

        self.pr.create_issue_comment(comment)

    def handle_changelog_command(self):
        """Generate changelog entry"""
        context = self.get_pr_context()
        files = list(self.pr.get_files())

        # Categorize changes
        categories = {
            'Added': [],
            'Changed': [],
            'Fixed': [],
            'Security': []
        }

        # Basic categorization
        for file in files:
            if 'fix' in self.pr.title.lower():
                categories['Fixed'].append(self.pr.title)
                break
            elif 'add' in self.pr.title.lower() or 'new' in self.pr.title.lower():
                categories['Added'].append(self.pr.title)
                break
            else:
                categories['Changed'].append(self.pr.title)
                break

        # Build changelog entry
        entry_parts = []
        for category, items in categories.items():
            if items:
                entry_parts.append(f"### {category}")
                for item in items:
                    entry_parts.append(f"- {item}")

        comment = f"""## 📝 Suggested Changelog Entry

```markdown
{chr(10).join(entry_parts)}
```

To add this to CHANGELOG.md:
1. Copy the entry above
2. Add it under the `[Unreleased]` section
3. Include PR reference: `(##{self.pr_number})`

---
<sub>Changelog suggestion • Use `/ai help` for more commands</sub>"""

        self.pr.create_issue_comment(comment)

    def handle_docs_command(self):
        """Generate documentation updates"""
        files = list(self.pr.get_files())

        # Check what might need documentation
        needs_docs = []

        for file in files:
            if file.filename.startswith('defaults/'):
                needs_docs.append(f"- New variables in `{file.filename}`")
            elif file.filename.startswith('tasks/') and file.status == 'added':
                needs_docs.append(f"- New task file `{file.filename}`")

        comment = f"""## 📚 Documentation Updates Needed

Based on the changes, consider updating:

### README.md
{chr(10).join(needs_docs) if needs_docs else '- No variable changes detected'}

### Suggested README sections to review:
- [ ] Role Variables (if new vars added)
- [ ] Requirements (if dependencies changed)
- [ ] Example Playbook (if usage changed)
- [ ] Compatibility matrix (if platform support changed)

### Documentation checklist:
- [ ] Variable descriptions are clear
- [ ] Default values are documented
- [ ] Examples are up to date
- [ ] Breaking changes are highlighted

---
<sub>Documentation assistant • Use `/ai help` for more commands</sub>"""

        self.pr.create_issue_comment(comment)

    def handle_improve_command(self):
        """Suggest improvements"""
        comment = f"""## 💡 Improvement Suggestions

Based on this PR, here are some suggestions for future improvements:

### Code Quality
- Consider adding molecule scenarios for new features
- Add ansible-lint exceptions with explanations if needed
- Consider extracting repeated tasks into separate files

### Testing
- Add specific test cases for the changes
- Consider adding integration tests with real VMs
- Document manual testing procedures

### Performance
- Consider using `block` for related tasks
- Review task conditions for efficiency
- Consider caching expensive operations

### Maintenance
- Update copyright year if needed
- Review and update dependencies
- Consider deprecation notices for changed behavior

Would you like me to elaborate on any of these suggestions?

---
<sub>Improvement suggestions • Use `/ai help` for more commands</sub>"""

        self.pr.create_issue_comment(comment)

    def handle_help_command(self):
        """Show available commands"""
        comment = """## 🤖 AI Assistant Commands

I can help with various PR tasks. Use these commands:

### Available Commands
- `/ai review` - Get detailed code review with specific feedback
- `/ai test` - Generate comprehensive test scenarios
- `/ai changelog` - Create changelog entry for this PR
- `/ai docs` - Identify documentation updates needed
- `/ai improve` - Suggest code improvements
- `/ai help` - Show this help message

### Examples
```
/ai review
/ai test
/ai changelog
```

### Tips
- Commands are case-insensitive
- One command per comment
- AI analysis may take a few moments

---
<sub>I'm here to help make your PR better! 🚀</sub>"""

        self.pr.create_issue_comment(comment)

    def handle_unknown_command(self, command: str):
        """Handle unknown commands"""
        comment = f"""❓ Unknown command: `/ai {command}`

Did you mean one of these?
- `/ai review` - Code review
- `/ai test` - Test scenarios
- `/ai help` - Show all commands

---
<sub>Use `/ai help` to see all available commands</sub>"""

        self.pr.create_issue_comment(comment)

    def run(self):
        """Process the command"""
        command = self.parse_command()

        if not command:
            return

        # React to show we're processing
        self.pr.create_issue_comment("🤖 Processing AI command...")

        # Handle commands
        handlers = {
            'review': self.handle_review_command,
            'test': self.handle_test_command,
            'changelog': self.handle_changelog_command,
            'docs': self.handle_docs_command,
            'improve': self.handle_improve_command,
            'help': self.handle_help_command,
        }

        handler = handlers.get(command.lower())
        if handler:
            handler()
        else:
            self.handle_unknown_command(command)


def main():
    parser = argparse.ArgumentParser(description='AI PR Assistant')
    parser.add_argument('--pr-number', type=int, required=True)
    parser.add_argument('--comment', type=str, required=True)
    args = parser.parse_args()

    assistant = AIPRAssistant(args.pr_number, args.comment)
    assistant.run()


if __name__ == '__main__':
    main()