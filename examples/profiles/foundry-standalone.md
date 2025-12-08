---
profile:
  name: foundry-standalone
  version: 1.0.0
  description: Standalone Foundry Local profile with comprehensive tools and 2-minute timeout

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
      timeout: 120
      temperature: 0.7
      max_tokens: 4096

tools:
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
  - module: tool-bash
    source: git+https://github.com/microsoft/amplifier-module-tool-bash@main
  - module: tool-web
    source: git+https://github.com/microsoft/amplifier-module-tool-web@main
  - module: tool-search
    source: git+https://github.com/microsoft/amplifier-module-tool-search@main
  - module: tool-todo
    source: git+https://github.com/microsoft/amplifier-module-tool-todo@main
  - module: tool-task
    source: git+https://github.com/microsoft/amplifier-module-tool-task@main

hooks:
  - module: hooks-status-context
    source: git+https://github.com/microsoft/amplifier-module-hooks-status-context@main
    config:
      include_datetime: true
      datetime_include_timezone: false
  - module: hooks-redaction
    source: git+https://github.com/microsoft/amplifier-module-hooks-redaction@main
    config:
      allowlist:
        - session_id
        - turn_id
        - span_id
        - parent_span_id
  - module: hooks-logging
    source: git+https://github.com/microsoft/amplifier-module-hooks-logging@main
    config:
      mode: session-only
      session_log_template: ~/.amplifier/projects/{project}/sessions/{session_id}/events.jsonl
  - module: hooks-todo-reminder
    source: git+https://github.com/microsoft/amplifier-module-hooks-todo-reminder@main
    config:
      inject_role: user
      priority: 10
  - module: hooks-streaming-ui
    source: git+https://github.com/microsoft/amplifier-module-hooks-streaming-ui@main

agents: all

---

You are an AI assistant powered by Microsoft Foundry Local for privacy-first AI inference. All processing happens locally on your device.

**Available Capabilities:**
- 🛠️ File system operations (read, write, list files)
- ⌨️ Bash command execution
- 🌐 Web browsing and content retrieval
- 🔍 Web search functionality
- 📝 Todo list management
- 📋 Task coordination and management
- 📊 Comprehensive logging and observability

**Usage Example:**
```bash
# Copy this profile to ~/.amplifier/profiles/
cp examples/profiles/foundry-standalone.md ~/.amplifier/profiles/

# Run with Amplifier
export PATH="/Users/samule/.local/share/uv/tools/amplifier/bin:$PATH" && \
amplifier run --profile foundry-standalone "Analyze the current directory structure" --mode single
```