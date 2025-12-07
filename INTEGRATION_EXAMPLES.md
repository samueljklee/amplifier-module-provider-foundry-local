# Foundry Local Integration Examples with Other Amplifier Modules

## 1. Hybrid Cloud-Local Provider Configuration

```yaml
# profiles/hybrid-privacy.yaml
session:
  orchestrator: "loop-streaming"  # For real-time responses
  context: "context-persistent"    # Maintain conversation state

providers:
  # Primary: Foundry Local for privacy-sensitive tasks
  - module: "provider-foundry-local"
    source: "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main"
    config:
      default_model: "qwen2.5-7b"
      priority: 10  # High priority for sensitive data
      auto_hardware_optimization: true
      offline_mode: true

  # Fallback: Anthropic for complex reasoning
  - module: "provider-anthropic"
    source: "git+https://github.com/microsoft/amplifier-module-provider-anthropic@main"
    config:
      default_model: "claude-sonnet-4-5"
      priority: 100  # Lower priority
      api_key: "${ANTHROPIC_API_KEY}"

tools:
  - module: "tool-filesystem"    # Local file operations
  - module: "tool-bash"          # System commands
  - module: "tool-web"           # Web search (uses cloud)

hooks:
  - module: "hooks-logging"      # Log all operations
    config:
      log_file: "foundry-local.log"
  - module: "hooks-approval"      # Require approval for sensitive operations
    config:
      require_approval_for: ["file_delete", "system_modify"]
```

## 2. Privacy-First Document Analysis

```yaml
# profiles/document-privacy.yaml
session:
  orchestrator: "loop-basic"
  context: "context-simple"

providers:
  - module: "provider-foundry-local"
    source: "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main"
    config:
      default_model: "qwen2.5-7b"
      offline_mode: true  # Force offline - never use cloud

tools:
  - module: "tool-filesystem"
  - module: "tool-bash"

hooks:
  - module: "hooks-redaction"     # Redact sensitive information
  - module: "hooks-logging"
    config:
      include_sensitive: false  # Don't log sensitive content
```

## 3. Edge/Offline Field Operations

```yaml
# profiles/field-service.yaml
session:
  orchestrator: "loop-events"    # Event-driven for intermittent connectivity
  context: "context-simple"

providers:
  - module: "provider-foundry-local"
    source: "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main"
    config:
      default_model: "qwen2.5-0.5b"  # Smaller model for edge hardware
      hardware_optimization: true
      memory_limit: "8GB"
      auto_hardware_optimization: true

tools:
  - module: "tool-filesystem"
  - module: "tool-bash"

hooks:
  - module: "hooks-scheduler-heuristic"  # Optimize for battery/power
    config:
      power_optimization: true
      batch_processing: true
```

## 4. Audio-First Voice Assistant

```python
# examples/voice_assistant.py
import asyncio
from amplifier_core import AmplifierSession

AUDIO_ENHANCED_CONFIG = {
    "session": {
        "orchestrator": "loop-streaming",  # Real-time processing
        "context": "context-simple",
    },
    "providers": [
        {
            "module": "provider-foundry-local",
            "source": "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main",
            "config": {
                "default_model": "qwen2.5-7b",
                "audio": {
                    "enabled": True,
                    "transcription_model": "whisper",
                    "streaming_audio": True,
                },
                "hardware_optimization": True,
            }
        }
    ],
    "tools": [
        {"module": "tool-filesystem"},
        {"module": "tool-bash"},
    ],
    "hooks": [
        {
            "module": "hooks-logging",
            "config": {"log_audio_transcriptions": True}
        }
    ]
}

async def voice_assistant():
    """Voice-first assistant with Foundry Local."""
    async with AmplifierSession(config=AUDIO_ENHANCED_CONFIG) as session:
        # Process voice input (future capability)
        # transcription = await session.provider.transcribe_audio(audio_data, "wav")

        # Execute command with voice input
        response = await session.execute(
            "Read the meeting_notes from today and summarize the key decisions."
        )

        print(f"Summary: {response}")
```

## 5. Cost-Optimized Batch Processing

```yaml
# profiles/cost-optimized.yaml
session:
  orchestrator: "loop-basic"
  context: "context-simple"

providers:
  - module: "provider-foundry-local"
    source: "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main"
    config:
      default_model: "qwen2.5-0.5b"  # Fast, efficient model
      batch_processing: true
      hardware_optimization: true

tools:
  - module: "tool-filesystem"
  - module: "tool-bash"

hooks:
  - module: "hooks-scheduler-heuristic"
    config:
      batch_size: 10
      cost_optimization: true
```

## 6. Multi-Provider Intelligent Routing

```python
# examples/intelligent_routing.py
import asyncio
from amplifier_core import AmplifierSession

INTELLIGENT_ROUTING_CONFIG = {
    "session": {
        "orchestrator": "loop-events",
        "context": "context-persistent",
    },
    "providers": [
        # Privacy-first - highest priority
        {
            "module": "provider-foundry-local",
            "source": "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main",
            "config": {
                "default_model": "qwen2.5-7b",
                "priority": 1,  # Highest priority
                "privacy_first": True,
                "triggers": ["sensitive_data", "privacy_required", "offline_only"],
            }
        },
        # Cloud fallback
        {
            "module": "provider-anthropic",
            "source": "git+https://github.com/microsoft/amplifier-module-provider-anthropic@main",
            "config": {
                "default_model": "claude-sonnet-4-5",
                "priority": 100,
                "triggers": ["complex_reasoning", "large_context", "multimodal"],
            }
        }
    ],
    "tools": [
        {"module": "tool-filesystem"},
        {"module": "tool-bash"},
        {"module": "tool-web"},
    ],
    "hooks": [
        {
            "module": "hooks-logging",
            "config": {"track_provider_routing": True}
        },
        {
            "module": "hooks-approval",
            "config": {
                "approve_cloud_usage": True,  # Ask before using cloud
                "approve_sensitive_operations": True,
            }
        }
    ]
}

async def intelligent_processing():
    """Demonstrate intelligent provider routing."""
    async with AmplifierSession(config=INTELLIGENT_ROUTING_CONFIG) as session:
        # This will route to Foundry Local (privacy-first)
        response1 = await session.execute(
            "Analyze this patient's medical record for potential drug interactions: [sensitive data]"
        )

        # This might route to cloud (complex reasoning)
        response2 = await session.execute(
            "Explain quantum computing in detail with multiple examples and analogies"
        )

        print(f"Privacy-aware response: {response1}")
        print(f"Complex reasoning response: {response2}")
```

## 7. Compliance and Audit Configuration

```yaml
# profiles/compliance.yaml
session:
  orchestrator: "loop-basic"
  context: "context-persistent"

providers:
  - module: "provider-foundry-local"
    source: "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main"
    config:
      default_model: "qwen2.5-7b"
      offline_mode: true  # Required for compliance
      audit_logging: true

tools:
  - module: "tool-filesystem"
  - module: "tool-bash"

hooks:
  - module: "hooks-logging"
    config:
      audit_trail: true
      log_all_operations: true
      log_file: "compliance-audit.log"
  - module: "hooks-approval"
    config:
      require_approval_for: ["file_access", "system_modify", "data_export"]
      audit_approvals: true
```

## 8. Testing and Validation Script

```python
# test_integration.py
"""Test Foundry Local integration with various modules."""

import asyncio
from amplifier_core import AmplifierSession

async def test_tool_integration():
    """Test Foundry Local with different tools."""
    config = {
        "session": {"orchestrator": "loop-basic"},
        "providers": [{
            "module": "provider-foundry-local",
            "source": "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main",
            "config": {"default_model": "qwen2.5-0.5b"}
        }],
        "tools": [
            {"module": "tool-filesystem"},
            {"module": "tool-bash"},
            {"module": "tool-web"}
        ]
    }

    async with AmplifierSession(config=config) as session:
        # Test filesystem tool
        await session.execute("List the files in the current directory.")

        # Test bash tool
        await session.execute("What's the current date and time?")

        # Test web tool
        await session.execute("Search for information about Microsoft Foundry Local.")

async def test_hooks_integration():
    """Test Foundry Local with various hooks."""
    config = {
        "session": {"orchestrator": "loop-basic"},
        "providers": [{
            "module": "provider-foundry-local",
            "source": "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main"
        }],
        "hooks": [
            {"module": "hooks-logging"},
            {"module": "hooks-redaction"},
            {"module": "hooks-approval"}
        ]
    }

    async with AmplifierSession(config=config) as session:
        await session.execute("Test privacy-aware processing with hooks.")

if __name__ == "__main__":
    asyncio.run(test_tool_integration())
    asyncio.run(test_hooks_integration())
```

## Key Integration Benefits

### 1. **Seamless Tool Integration**
- Works with all existing Amplifier tools (filesystem, bash, web, search)
- No changes needed to tool implementations
- Privacy-first tool execution (everything runs locally)

### 2. **Hook System Compatibility**
- All existing hooks work with Foundry Local
- Special hooks for privacy and compliance scenarios
- Audit trail for sensitive operations

### 3. **Orchestrator Flexibility**
- Works with all orchestrators (loop-basic, loop-streaming, loop-events)
- Supports real-time streaming for voice applications
- Event-driven processing for edge scenarios

### 4. **Context Management**
- Compatible with all context managers
- Local state persistence for offline scenarios
- Privacy-preserving context compaction

### 5. **Multi-Provider Scenarios**
- Intelligent routing between local and cloud providers
- Cost optimization through provider selection
- Compliance-aware provider choices

The Foundry Local provider is **fully compatible** with the existing Amplifier ecosystem and enables unique privacy-first use cases that complement cloud-based providers.