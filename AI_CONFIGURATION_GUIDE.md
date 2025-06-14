# AI Configuration Guide

This guide explains how to configure and customize the AI-powered automation system for optimal price/performance.

## 🎯 Recommended Models for Price/Performance

### OpenAI Models
- **GPT-4o mini** - Best choice for most tasks (~$0.15 per 1M input tokens)
  - Excellent code analysis and understanding
  - Good at following structured prompts
  - 15x cheaper than GPT-4
- **GPT-4o** - For complex reasoning tasks (~$2.50 per 1M input tokens)
  - Use only when mini isn't sufficient

### Anthropic Models
- **Claude 3.5 Haiku** - Fastest and cheapest (~$0.25 per 1M input tokens)
  - Great for simple analysis and documentation tasks
  - Very fast response times
- **Claude 3.5 Sonnet** - Better reasoning (~$3.00 per 1M input tokens)
  - Use for complex code review and analysis

## 📁 File Structure

```
.github/scripts/
├── ai_config.yml           # Main configuration file
├── ai_utils.py             # AI client utility class
├── prompts/                # Prompt templates directory
│   ├── release_analysis.yml
│   ├── pr_analysis.yml
│   ├── code_review.yml
│   └── release_notes.yml
└── requirements.txt        # Python dependencies
```

## ⚙️ Configuration File (ai_config.yml)

### Provider Priority
```yaml
provider_priority:
  - openai      # Try OpenAI first
  - anthropic   # Fallback to Anthropic
```

### Model Selection by Task Complexity
```yaml
providers:
  openai:
    models:
      simple: "gpt-4o-mini"     # Documentation, simple analysis
      standard: "gpt-4o-mini"   # PR analysis, code review
      complex: "gpt-4o"         # Complex reasoning tasks
```

### Task-Specific Configuration
```yaml
task_models:
  release_analysis:
    complexity: standard    # Uses gpt-4o-mini
  pr_analysis:
    complexity: standard    # Uses gpt-4o-mini
  code_review:
    complexity: standard    # Uses gpt-4o-mini
```

## 📝 Prompt Templates

### Template Structure
```yaml
# prompts/example.yml
system_prompt: |
  You are an expert in...

user_prompt: |
  Analyze this code:
  {code_content}
  
  Provide feedback on:
  {criteria}

variables:
  - code_content
  - criteria

complexity: standard

parameters:
  temperature: 0.3
  max_tokens: 1500
```

### Template Variables
Variables in prompts use `{variable_name}` syntax and are replaced when the template is rendered.

## 💰 Cost Optimization

### Current Estimated Costs (per 1M tokens)

| Provider | Model | Input Cost | Output Cost | Best For |
|----------|-------|------------|-------------|----------|
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | Most tasks ⭐ |
| OpenAI | gpt-4o | $2.50 | $10.00 | Complex reasoning |
| Anthropic | Claude 3.5 Haiku | $0.25 | $1.25 | Simple tasks ⭐ |
| Anthropic | Claude 3.5 Sonnet | $3.00 | $15.00 | Complex analysis |

### Monthly Cost Estimates
- **Small project** (< 50 PRs): ~$2-5/month with mini models
- **Medium project** (50-200 PRs): ~$10-25/month with mini models
- **Large project** (> 200 PRs): ~$30-75/month with mini models

## 🚀 Usage Examples

### Basic Usage in Scripts
```python
from ai_utils import AIClient

# Initialize client
ai = AIClient()

# Use a prompt template
result = ai.call_ai('release_analysis', {
    'commit_text': "feat: add new feature\nfix: bug fix",
    'changes_summary': "tasks: 2 files changed",
    'task_files': "tasks/main.yml\ntasks/setup.yml"
})

if result['content']:
    analysis = json.loads(result['content'])
    print(f"Version bump: {analysis['version_bump']}")
```

### Creating Custom Prompt Templates
1. Create a new YAML file in `.github/scripts/prompts/`
2. Define system_prompt, user_prompt, and variables
3. Set complexity level and parameters
4. Use in scripts with `ai.call_ai('your_template_name', variables)`

## 🔧 Customization Options

### Changing Default Models
Edit `ai_config.yml`:
```yaml
providers:
  openai:
    default_model: "gpt-4o-mini"  # Change to gpt-4o for better quality
    models:
      simple: "gpt-4o-mini"
      standard: "gpt-4o"          # Upgrade standard tasks
      complex: "gpt-4o"
```

### Adding New Tasks
1. Add to `task_models` in config:
```yaml
task_models:
  my_custom_task:
    complexity: standard
    description: "Custom analysis task"
```

2. Create prompt template: `prompts/my_custom_task.yml`

3. Use in scripts: `ai.call_ai('my_custom_task', variables)`

### Model Parameters
Customize per model:
```yaml
parameters:
  "gpt-4o-mini":
    max_tokens: 1500
    temperature: 0.2    # Lower for more consistent output
    timeout: 30
```

## 🐛 Debugging and Monitoring

### Enable Debug Logging
```yaml
debug:
  log_tokens: true           # Log token usage
  log_prompts: false         # Log full prompts (security risk)
  log_responses: false       # Log AI responses
  estimate_costs: true       # Show cost estimates
```

### Usage Tracking
The AI client automatically tracks:
- Number of requests
- Total tokens used
- Estimated costs
- Active provider

Access with: `ai.get_usage_summary()`

## 🔒 Security Considerations

1. **API Keys**: Store in GitHub Secrets, never in code
2. **Prompt Logging**: Disable `log_prompts` in production
3. **Response Logging**: Disable `log_responses` to avoid sensitive data leaks
4. **Rate Limiting**: Configure `requests_per_minute` to stay within API limits

## 🎛️ Advanced Configuration

### Provider-Specific Settings
```yaml
providers:
  openai:
    # OpenAI-specific settings
    organization: "your-org-id"  # Optional
    base_url: "https://api.openai.com/v1"  # Custom endpoint
    
  anthropic:
    # Anthropic-specific settings
    max_retries: 3
    timeout: 60
```

### Fallback Behavior
```yaml
fallback:
  on_failure: "rule_based"  # Options: rule_based, skip, error
  max_retries: 2
  retry_delay: 5
  requests_per_minute: 20
```

## 🔄 Migration from Old Scripts

To migrate existing AI scripts:

1. **Install new dependencies**: `pip install -r requirements.txt`
2. **Replace AI initialization**:
   ```python
   # Old way
   openai.api_key = os.environ.get('OPENAI_API_KEY')
   
   # New way
   from ai_utils import AIClient
   ai = AIClient()
   ```

3. **Replace API calls**:
   ```python
   # Old way
   response = openai.ChatCompletion.create(...)
   
   # New way
   result = ai.call_ai('task_name', template_variables)
   ```

4. **Create prompt templates** for your existing prompts

5. **Update configuration** to match your needs

## 📊 Performance Tips

1. **Use appropriate models**: Don't use GPT-4o for simple tasks
2. **Optimize prompts**: Shorter, clearer prompts use fewer tokens
3. **Batch requests**: Process multiple items in single requests when possible
4. **Cache results**: Avoid re-analyzing the same content
5. **Set reasonable limits**: Use `max_tokens` to control costs

## 🆘 Troubleshooting

### Common Issues

**"No AI providers available"**
- Check API keys are set in GitHub Secrets
- Verify requirements.txt installation

**"Prompt template not found"**
- Ensure template file exists in `prompts/` directory
- Check YAML syntax in template file

**"JSON parsing failed"**
- Review prompt template for clear JSON instructions
- Consider using `response_format: {"type": "json_object"}` for OpenAI

**High costs**
- Review `debug.estimate_costs` output
- Consider switching to cheaper models
- Optimize prompt length and token usage

### Getting Help

1. Check GitHub Actions logs for detailed error messages
2. Enable debug logging temporarily
3. Test locally with environment variables set
4. Review cost estimates in usage summary

This configuration system makes the AI automation more maintainable, cost-effective, and customizable for your specific needs.