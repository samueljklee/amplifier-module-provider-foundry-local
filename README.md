# amplifier-module-provider-foundry-local

Microsoft Foundry Local provider for Amplifier - privacy-first local AI inference.

## Overview

This provider integrates Microsoft Foundry Local with Amplifier, enabling:

- **🔒 Privacy-First AI**: 100% offline inference, data never leaves your device
- **⚡ Hardware Optimization**: Automatic CPU/GPU/NPU optimization
- **🛠️ Full Tool Calling**: Complete OpenAI-compatible tool calling support
- **💰 Zero Cloud Costs**: Free inference after hardware investment

## Quick Start

> **Note**: The provider auto-installs via Amplifier's module resolution. No manual installation needed!

### Step 1: Install Prerequisites

1. **Install UV** (required for both CLI and Playground):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Foundry Local**:
   ```bash
   # Windows
   winget install Microsoft.FoundryLocal

   # macOS
   brew tap microsoft/foundrylocal
   brew install foundrylocal
   ```

### Step 2: Start Foundry and Copy Profile

1. **Start Foundry Local with a model**:
   ```bash
   foundry model run qwen2.5-7b
   # Output will show:
   # 🟢 Service is Started on http://127.0.0.1:59114/, PID 34414!
   # Downloading qwen2.5-7b-instruct-generic-gpu:4...
   ```

   **⚠️ IMPORTANT**: The port number changes each time you start Foundry Local. Note your port (e.g., `59114`) - you'll need it in the next step.

   The model will download on first run. Wait for download to complete before proceeding.

2. **Copy and configure the profile**:
   ```bash
   # Create profiles directory
   mkdir -p .amplifier/profiles
   
   # Copy example profile
   cp examples/profiles/foundry-standalone.md .amplifier/profiles/
   ```

3. **Update the port** in `.amplifier/profiles/foundry-standalone.md`:
   
   Change the `base_url` to match your Foundry Local port:
   ```yaml
   providers:
     - module: provider-foundry-local
       config:
         base_url: http://127.0.0.1:59114/v1  # Replace 59114 with YOUR port
   ```

### Step 3: Run It!

**Option A: Amplifier CLI**

1. **Install Amplifier**:
   ```bash
   uv tool install git+https://github.com/microsoft/amplifier
   ```

2. **Run the profile**:
   ```bash
   # Validate profile is recognized (optional)
   amplifier profile list

   # Run in chat mode
   amplifier run --profile foundry-standalone "What model are you using?" --mode chat
   ```

**Option B: Amplifier Playground**

No Amplifier CLI installation needed! Just run:

```bash
uvx --from git+https://github.com/samueljklee/amplifier-playground amplay
```

Then select `foundry-standalone` from the "Select Configuration" menu.

> **Note**: The Playground uses `uvx` to run without installing Amplifier CLI.

---

## Available Example Profiles

This repository includes ready-to-use profiles in `examples/profiles/`:

- **foundry-standalone** - Comprehensive profile with all tools and 2-minute timeout
- **foundry-minimal** - Minimal profile for simple testing
- **foundry-tools-focused** - Development-focused with essential tools

📖 **See `examples/profiles/README.md` for detailed usage instructions.**

---

## Configuration Reference

### Provider Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_model` | string | `"qwen2.5-7b-instruct-generic-gpu"` | Primary model to use (use exact ID from `foundry model list`) |
| `base_url` | string | `"http://127.0.0.1:[PORT]/v1"` | Foundry Local endpoint (port changes each run) |
| `auto_hardware_optimization` | boolean | `true` | Auto-detect CPU/GPU/NPU |
| `timeout` | float | `30.0` | Request timeout in seconds |
| `temperature` | float | `0.7` | Sampling temperature |
| `debug` | boolean | `false` | Enable standard debug events |
| `raw_debug` | boolean | `false` | Enable ultra-verbose raw API I/O logging (requires `debug: true`) |
| `debug_truncate_length` | int | `180` | Maximum string length in debug logs |

### Example Profile Configuration

```yaml
providers:
  - module: provider-foundry-local
    source: git+https://github.com/samueljklee/amplifier-module-provider-foundry-local@main
    config:
      default_model: "qwen2.5-7b-instruct-generic-gpu"
      auto_hardware_optimization: true
      base_url: "http://127.0.0.1:59114/v1"  # Use YOUR port here
      timeout: 30
      temperature: 0.7
```

---

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

---

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

4. **"No module named 'anthropic'" or similar module errors** (Amplifier CLI only):
   
   This typically occurs when running Amplifier CLI. Install missing dependencies in Amplifier's environment:
   
   ```bash
   # Activate the Amplifier environment
   source $(uv tool dir)/amplifier/bin/activate
   
   # Install required packages
   uv pip install anthropic openai
   ```
   
   The full error looks like:
   ```
   Failed to load module 'provider-anthropic': Module 'provider-anthropic' failed validation: 
   FAILED: 0/1 checks passed (1 errors, 0 warnings). 
   Errors: module_importable: Failed to import module: No module named 'anthropic'
   ```
   
   **Note**: This issue is specific to Amplifier CLI. The Amplifier Playground typically doesn't encounter this error.

5. **Can't connect to Foundry Local**:
   - Verify Foundry is running: `curl http://127.0.0.1:[YOUR_PORT]/v1/models`
   - Check you're using the correct port from the Foundry startup output
   - Ensure the model finished downloading

### Debug Mode

The provider supports multiple debug levels for troubleshooting and monitoring:

#### Standard Debug (`debug: true`)
- Emits `llm:request:debug` and `llm:response:debug` events
- Contains request/response summaries with message counts, model info, usage stats
- Long values automatically truncated for readability
- Moderate log volume, suitable for development

#### Raw Debug (`debug: true, raw_debug: true`)
- Emits `llm:request:raw` and `llm:response:raw` events
- Contains complete, unmodified request params and response objects
- Extreme log volume, use only for deep provider integration debugging
- Captures the exact data sent to/from Foundry Local API before any processing

#### Configuration Examples

**Standard Debug** (recommended for development):
```yaml
providers:
  - module: provider-foundry-local
    source: git+https://github.com/samueljklee/amplifier-module-provider-foundry-local@main
    config:
      default_model: "qwen2.5-7b-instruct-generic-gpu"
      base_url: "http://127.0.0.1:59114/v1"
      debug: true                      # Enable debug events
      debug_truncate_length: 180       # Truncate strings to 180 chars
```

**Raw Debug** (for deep debugging):
```yaml
providers:
  - module: provider-foundry-local
    source: git+https://github.com/samueljklee/amplifier-module-provider-foundry-local@main
    config:
      default_model: "qwen2.5-7b-instruct-generic-gpu"
      base_url: "http://127.0.0.1:59114/v1"
      debug: true                      # Enable debug events
      raw_debug: true                  # Enable raw API I/O capture
      debug_truncate_length: 1000      # Higher limit for more context
```

Or enable debug mode per command:

```bash
amplifier run --profile foundry-standalone "Your prompt here" --debug
```

#### Debug Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `debug` | boolean | `false` | Enable standard debug events (llm:request:debug, llm:response:debug) |
| `raw_debug` | boolean | `false` | Enable raw API I/O logging (requires `debug: true`) |
| `debug_truncate_length` | int | `180` | Maximum string length in debug logs (does not apply to raw_debug) |

---

## Advanced Usage

### Python API

For programmatic usage outside of profiles:

```python
from amplifier_core import AmplifierSession

config = {
    "session": {"orchestrator": "loop-basic"},
    "providers": [{
        "module": "provider-foundry-local",
        "source": "git+https://github.com/samueljklee/amplifier-module-provider-foundry-local@main",
        "config": {
            "default_model": "qwen2.5-7b-instruct-generic-gpu",
            "auto_hardware_optimization": True,
            "base_url": "http://127.0.0.1:59114/v1"  # Use YOUR port
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

### Local Development

```bash
# Clone repository
git clone https://github.com/samueljklee/amplifier-module-provider-foundry-local.git
cd amplifier-module-provider-foundry-local

# Install in development mode
uv add -e .

# Test with Amplifier
amplifier run --profile foundry-standalone "Hello, Foundry Local!"
```

---

## Reference

### Privacy Use Cases

Perfect for scenarios where data privacy is critical:

- **Healthcare**: HIPAA-compliant processing of patient data
- **Legal**: Attorney-client privileged document analysis
- **Finance**: PCI-DSS compliant financial data processing
- **Government**: Classified document processing
- **Edge Computing**: Field operations with no internet connectivity

### Hardware Optimization

Foundry Local automatically detects and optimizes for available hardware:
- **NVIDIA GPUs**: CUDA-optimized models
- **AMD GPUs**: ROCm-optimized models
- **Intel NPUs**: NPU-accelerated models
- **Apple Silicon**: Metal-optimized models
- **CPU**: CPU-optimized models (fallback)

For detailed hardware optimization guidance, see the [Foundry Local CLI Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/reference/reference-cli?view=foundry-classic).

---

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
