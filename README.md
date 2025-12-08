# amplifier-module-provider-foundry-local

Microsoft Foundry Local provider for Amplifier - privacy-first local AI inference.

## Overview

This provider integrates Microsoft Foundry Local with Amplifier, enabling:

- **🔒 Privacy-First AI**: 100% offline inference, data never leaves your device
- **⚡ Hardware Optimization**: Automatic CPU/GPU/NPU optimization
- **🛠️ Full Tool Calling**: Complete OpenAI-compatible tool calling support
- **💰 Zero Cloud Costs**: Free inference after hardware investment

## Installation

### Prerequisites

1. **Install Amplifier**:
   ```bash
   # Install UV (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install Amplifier
   uv tool install git+https://github.com/microsoft/amplifier@next
   ```

2. **Install Foundry Local**:
   ```bash
   # Windows
   winget install Microsoft.FoundryLocal

   # macOS
   brew tap microsoft/foundrylocal
   brew install foundrylocal
   ```

3. **Start Foundry Local with a model**:
   ```bash
   foundry model run qwen2.5-7b
   # This starts Foundry Local on default port 65320
   # Confirm it's running: http://127.0.0.1:65320/v1
   ```

### Install Provider

```bash
uv add git+https://github.com/samueljklee/amplifier-module-provider-foundry-local@main
```

## Quick Start

### Basic Configuration

Add to your Amplifier profile:

```yaml
providers:
  - module: provider-foundry-local
    source: git+https://github.com/samueljklee/amplifier-module-provider-foundry-local@main
    config:
      default_model: "qwen2.5-7b-instruct-generic-gpu"
      auto_hardware_optimization: true
      base_url: "http://127.0.0.1:65320/v1"
      timeout: 30
      temperature: 0.7
```

### Usage Example

```python
from amplifier_core import AmplifierSession

config = {
    "session": {"orchestrator": "loop-basic"},
    "providers": [{
        "module": "provider-foundry-local",
        "source": "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main",
        "config": {
            "default_model": "qwen2.5-7b-instruct-generic-gpu",
            "auto_hardware_optimization": True
        }
    }],
    "tools": [{"module": "tool-filesystem"}]
}

async with AmplifierSession(config=config) as session:
    response = await session.execute(
        "List the files in the current directory and explain what each contains."
    )
    print(response)
```

### Verification

To verify your installation is working correctly:

1. **Check Foundry Local is running**:
   ```bash
   curl http://127.0.0.1:65320/v1/models
   # Should return a JSON list of available models
   ```

2. **Test provider connection**:
   ```bash
   amplifier run --profile foundry-minimal "What model are you using?" --mode chat
   # Should respond with the Foundry Local model name
   ```

3. **Check provider logs**:
   Look for these success indicators in the output:
   - `✅ Using configured Foundry Local endpoint: http://127.0.0.1:65320/v1`
   - `✅ Foundry Local endpoint is reachable`
   - `✅ Found valid model: [model-name]`

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_model` | string | `"qwen2.5-7b-instruct-generic-gpu"` | Primary model to use (use exact ID from `foundry model list`) |
| `base_url` | string | `"http://127.0.0.1:65320/v1"` | Foundry Local endpoint |
| `auto_hardware_optimization` | boolean | `true` | Auto-detect CPU/GPU/NPU |
| `timeout` | float | `30.0` | Request timeout in seconds |
| `temperature` | float | `0.7` | Sampling temperature |

## Available Models

Check what models are available on your system:

```bash
foundry model list  # See all available models
```

Common models include:
- `qwen2.5-7b-instruct-generic-gpu` - General purpose (7B parameters)
- `qwen2.5-0.5b-instruct-generic-onnx` - Fast responses (0.5B parameters)
- `phi-4-mini-instruct-generic-gpu` - Efficient inference (3.8B parameters)
- `gpt-oss-20b-instruct-generic-gpu` - Complex tasks (20B parameters, requires 16GB+ VRAM)

**Important**: Use the exact model IDs returned by `foundry model list` in your configuration. The model IDs include variant information (like `-instruct-generic-gpu`) that specifies the optimization type.

**For the complete and up-to-date model list, see the [Foundry Local CLI Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/reference/reference-cli?view=foundry-classic)**

## Privacy Use Cases

Perfect for scenarios where data privacy is critical:

- **Healthcare**: HIPAA-compliant processing of patient data
- **Legal**: Attorney-client privileged document analysis
- **Finance**: PCI-DSS compliant financial data processing
- **Government**: Classified document processing
- **Edge Computing**: Field operations with no internet connectivity

## Hardware Optimization

Foundry Local automatically detects and optimizes for available hardware:
- **NVIDIA GPUs**: CUDA-optimized models
- **AMD GPUs**: ROCm-optimized models
- **Intel NPUs**: NPU-accelerated models
- **Apple Silicon**: Metal-optimized models
- **CPU**: CPU-optimized models (fallback)

For detailed hardware optimization guidance, see the [Foundry Local CLI Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/reference/reference-cli?view=foundry-classic).

## Troubleshooting

### Common Issues

1. **"Foundry Local not found"**:
   ```bash
   foundry --version
   # If not found, install Foundry Local first
   ```

2. **"Model not available"**:
   ```bash
   foundry model list
   # Download required model
   foundry model run qwen2.5-7b
   ```

3. **"Hardware acceleration not working"**:
   ```bash
   # Check driver support
   nvidia-smi  # NVIDIA
   rocm-smi   # AMD
   ```

### Debug Mode

Enable detailed logging in your Amplifier profile:

```yaml
providers:
  - module: provider-foundry-local
    source: git+https://github.com/samueljklee/amplifier-module-provider-foundry-local@main
    config:
      default_model: "qwen2.5-7b"
      base_url: "http://127.0.0.1:65320/v1"
      debug: true
      raw_debug: true
      debug_truncate_length: 1000
```

Or enable debug mode per command:

```bash
amplifier run --profile foundry-minimal "Your prompt here" --debug
```

## Development

### Local Development

```bash
# Clone repository
git clone https://github.com/samueljklee/amplifier-module-provider-foundry-local.git
cd amplifier-module-provider-foundry-local

# Install in development mode
uv add -e .

# Test with Amplifier
amplifier run --profile foundry-minimal "Hello, Foundry Local!"
```

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/microsoft/amplifier-module-provider-foundry-local/issues)
- **Foundry Local**: [Microsoft Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/)
- **Amplifier**: [Amplifier Documentation](https://github.com/microsoft/amplifier)

---

**🔒 Privacy-first AI that never leaves your device!**