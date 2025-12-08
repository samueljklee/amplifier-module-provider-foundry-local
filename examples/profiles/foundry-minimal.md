---
profile:
  name: foundry-minimal
  version: 1.0.0
  description: Minimal Foundry Local profile with basic configuration

session:
  orchestrator:
    module: loop-streaming
    source: git+https://github.com/microsoft/amplifier-module-loop-streaming@main
  context:
    module: context-simple
    source: git+https://github.com/microsoft/amplifier-module-context-simple@main

providers:
  - module: provider-foundry-local
    source: git+https://github.com/samueljklee/amplifier-module-provider-foundry-local@main
    config:
      default_model: qwen2.5-7b-instruct-generic-gpu:4
      base_url: http://127.0.0.1:65320/v1
      timeout: 30
      temperature: 0.7
      max_tokens: 4096

hooks:
  - module: hooks-logging
    source: git+https://github.com/microsoft/amplifier-module-hooks-logging@main
    config:
      mode: session-only

---

You are an AI assistant powered by Microsoft Foundry Local for privacy-first AI inference.

**Minimal Setup:** No tools included, just basic local AI processing.

**Usage:**
```bash
cp examples/profiles/foundry-minimal.md ~/.amplifier/profiles/
export PATH="/Users/samule/.local/share/uv/tools/amplifier/bin:$PATH" && \
amplifier run --profile foundry-minimal "Hello, Foundry Local!" --mode single
```