# Foundry Local Profile Examples

This directory contains ready-to-use Amplifier profiles for the Foundry Local provider.

## Available Profiles

### 🚀 foundry-standalone.md
**Comprehensive profile** with all tools and capabilities
- All 6 tools: filesystem, bash, web, search, todo, task
- Full hooks suite for logging, redaction, and monitoring
- 2-minute timeout for complex tasks
- **Best for:** Complete privacy-first AI assistant setup

### ⚡ foundry-minimal.md
**Minimal profile** with just the basics
- No tools, just local AI processing
- Basic logging only
- 30-second timeout
- **Best for:** Simple chat, testing, learning

### 🛠️ foundry-tools-focused.md
**Development-focused profile** with essential dev tools
- Core tools: filesystem, bash, todo
- Development-optimized settings
- 60-second timeout
- **Best for:** Code analysis, project management, development workflows

## Quick Start

1. **Copy a profile to your Amplifier profiles directory:**
   ```bash
   cp examples/profiles/foundry-standalone.md ~/.amplifier/profiles/
   ```

2. **Install required dependencies:**
   ```bash
   export PATH="/Users/samule/.local/share/uv/tools/amplifier/bin:$PATH"
   uv pip install anthropic openai
   ```

3. **Run with Amplifier:**
   ```bash
   amplifier run --profile foundry-standalone "Hello, Foundry Local!" --mode single
   ```

## Profile Customization

Each profile can be customized by editing the YAML configuration:

### Change Model
```yaml
providers:
  - module: provider-foundry-local
    config:
      default_model: qwen2.5-0.5b-instruct-generic-onnx  # Faster model
```

### Adjust Timeout
```yaml
providers:
  - module: provider-foundry-local
    config:
      timeout: 180  # 3 minutes for complex tasks
```

### Add/Remove Tools
```yaml
tools:
  - module: tool-filesystem
  - module: tool-web
  # Add or remove tools as needed
```

## Requirements

- **Foundry Local**: Running on `http://127.0.0.1:65320/v1`
- **Amplifier**: Installed with proper PATH configuration
- **Dependencies**: `anthropic` and `openai` packages

## Troubleshooting

### Common Issues

1. **Profile not found**: Ensure you copied the profile to `~/.amplifier/profiles/`
2. **Timeout errors**: Increase the `timeout` value in the provider config
3. **Tool not working**: Check that the tool module source is correct
4. **Foundry Local not reachable**: Verify Foundry Local is running on the correct port

### Validation Commands

```bash
# Check Foundry Local is running
curl http://127.0.0.1:65320/v1/models

# Test model availability
curl http://127.0.0.1:65320/v1/models | python3 -m json.tool | grep toolCalling

# Test basic provider
amplifier run --profile foundry-minimal "What model are you using?" --mode single

# Test tools
amplifier run --profile foundry-standalone "List files in current directory" --mode single
```

---

🔒 **Privacy-first AI that never leaves your device!**