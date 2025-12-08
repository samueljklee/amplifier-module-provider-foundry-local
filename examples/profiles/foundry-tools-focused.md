---
profile:
  name: foundry-tools-focused
  version: 1.0.0
  description: Foundry Local profile focused on development tools

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
      timeout: 60
      temperature: 0.3
      max_tokens: 4096

tools:
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
  - module: tool-bash
    source: git+https://github.com/microsoft/amplifier-module-tool-bash@main
  - module: tool-todo
    source: git+https://github.com/microsoft/amplifier-module-tool-todo@main

hooks:
  - module: hooks-logging
    source: git+https://github.com/microsoft/amplifier-module-hooks-logging@main
    config:
      mode: session-only
  - module: hooks-todo-reminder
    source: git+https://github.com/microsoft/amplifier-module-hooks-todo-reminder@main
    config:
      inject_role: user
      priority: 10

---

You are an AI development assistant powered by Microsoft Foundry Local with access to filesystem, bash, and todo tools.

**Development Tools Available:**
- 📁 File system operations
- ⌨️ Command execution
- 📝 Task management
- 📊 Session logging

**Perfect For:**
- Code analysis
- Project management
- File operations
- Development workflows

**Usage:**
```bash
cp examples/profiles/foundry-tools-focused.md ~/.amplifier/profiles/
export PATH="/Users/samule/.local/share/uv/tools/amplifier/bin:$PATH" && \
amplifier run --profile foundry-tools-focused "Analyze this Python project structure" --mode single
```