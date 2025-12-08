# Debug Modes Implementation

## Overview

Implemented comprehensive debug modes for the Foundry Local provider, following the same pattern used in other Amplifier providers (Anthropic, Ollama, Azure OpenAI, vLLM).

## Implementation Summary

### 1. Configuration Options Added

Three new configuration options in `__init__.py`:

```python
self.debug = self.config.get("debug", False)  # Enable full request/response logging
self.raw_debug = self.config.get("raw_debug", False)  # Enable ultra-verbose raw API I/O logging
self.debug_truncate_length = self.config.get("debug_truncate_length", DEFAULT_DEBUG_TRUNCATE_LENGTH)
```

**Default**: `debug=False`, `raw_debug=False`, `debug_truncate_length=180`

### 2. Helper Method: `_truncate_values()`

Added recursive string truncation method for debug output:
- Preserves structure (dicts, lists, primitives)
- Only truncates leaf string values longer than `debug_truncate_length`
- Adds `"... (N chars total)"` suffix to truncated strings
- Used for `llm:request:debug` and `llm:response:debug` events

**Location**: `__init__.py:727-755`

### 3. Event Emission - Request Events

Three levels of request events emitted before API call:

#### INFO Level: `llm:request` (always emitted)
```python
{
    "provider": "foundry-local",
    "model": "qwen2.5-7b-instruct-generic-gpu:4",
    "message_count": 3,
    "has_tools": true,
    "tool_count": 2
}
```

#### DEBUG Level: `llm:request:debug` (when `debug: true`)
```python
{
    "lvl": "DEBUG",
    "provider": "foundry-local",
    "request": {
        "model": "qwen2.5-7b-instruct-generic-gpu:4",
        "messages": [
            {"role": "system", "content": "You are a helpful... (512 chars total)"},
            {"role": "user", "content": "What is the capital... (28 chars total)"}
        ],
        "max_tokens": 2048,
        "temperature": 0.7,
        "tools": [...] // truncated
    }
}
```

#### RAW Level: `llm:request:raw` (when `debug: true` AND `raw_debug: true`)
```python
{
    "lvl": "DEBUG",
    "provider": "foundry-local",
    "params": {
        // Complete untruncated request params
        // Exact data sent to OpenAI-compatible API
    }
}
```

**Location**: `__init__.py:495-529`

### 4. Event Emission - Response Events

Three levels of response events emitted after API call:

#### INFO Level: `llm:response` (always emitted)
```python
{
    "provider": "foundry-local",
    "model": "qwen2.5-7b-instruct-generic-gpu:4",
    "usage": {
        "input": 128,
        "output": 45
    },
    "status": "ok",
    "duration_ms": 1234
}
```

#### DEBUG Level: `llm:response:debug` (when `debug: true`)
```python
{
    "lvl": "DEBUG",
    "provider": "foundry-local",
    "response": {
        "id": "chatcmpl-xyz",
        "model": "qwen2.5-7b-instruct-generic-gpu:4",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "The capital of France... (245 chars total)",
                "tool_calls": null
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 128,
            "completion_tokens": 45,
            "total_tokens": 173
        }
    },
    "status": "ok",
    "duration_ms": 1234
}
```

#### RAW Level: `llm:response:raw` (when `debug: true` AND `raw_debug: true`)
```python
{
    "lvl": "DEBUG",
    "provider": "foundry-local",
    "response": {
        // Complete untruncated response object
        // Exact data received from OpenAI-compatible API
    }
}
```

**Location**: `__init__.py:549-661`

## Usage Examples

### Standard Debug (Recommended for Development)

```yaml
providers:
  - module: provider-foundry-local
    config:
      base_url: "http://127.0.0.1:59114/v1"
      default_model: "qwen2.5-7b-instruct-generic-gpu:4"
      debug: true                      # Enable debug events
      debug_truncate_length: 180       # Truncate strings to 180 chars
```

**What you'll see**:
- Summary events (`llm:request`, `llm:response`)
- Debug events with truncated content (`llm:request:debug`, `llm:response:debug`)
- Readable output for development

### Raw Debug (Deep Troubleshooting)

```yaml
providers:
  - module: provider-foundry-local
    config:
      base_url: "http://127.0.0.1:59114/v1"
      default_model: "qwen2.5-7b-instruct-generic-gpu:4"
      debug: true                      # Required for raw_debug
      raw_debug: true                  # Enable raw API I/O capture
      debug_truncate_length: 1000      # Higher limit for more context
```

**What you'll see**:
- All standard and debug events
- Raw events with complete, untruncated data (`llm:request:raw`, `llm:response:raw`)
- Extreme verbosity - exact API I/O

## Event Hierarchy

```
Always Emitted:
├── llm:request (INFO)
└── llm:response (INFO)

When debug: true:
├── llm:request:debug (DEBUG, truncated)
└── llm:response:debug (DEBUG, truncated)

When debug: true AND raw_debug: true:
├── llm:request:raw (RAW, complete)
└── llm:response:raw (RAW, complete)
```

## Files Modified

1. **`amplifier_module_provider_foundry_local/__init__.py`**
   - Added `raw_debug` config option (line 134)
   - Added `_truncate_values()` method (lines 727-755)
   - Added request debug events (lines 495-529)
   - Added response debug events (lines 549-661)

2. **`README.md`**
   - Added debug configuration options to table (lines 123-125)
   - Added comprehensive "Debug Mode" section (lines 210-266)
   - Included usage examples and best practices

## Pattern Consistency

This implementation follows the exact pattern used in:
- `amplifier-module-provider-anthropic`
- `amplifier-module-provider-ollama`
- `amplifier-module-provider-azure-openai`
- `amplifier-module-provider-vllm`

### Common Patterns:
1. Three-tier event system (INFO, DEBUG, RAW)
2. `_truncate_values()` helper for readable debug output
3. `debug` flag for standard debugging
4. `raw_debug` flag for complete API I/O (requires `debug: true`)
5. Consistent event names: `llm:request`, `llm:request:debug`, `llm:request:raw`

## Benefits

1. **Development**: Use `debug: true` for readable, truncated debug output
2. **Troubleshooting**: Use `raw_debug: true` to see exact API I/O
3. **Performance**: No overhead when debug disabled (default)
4. **Consistency**: Matches other Amplifier providers
5. **Flexibility**: Configurable truncation length

## Testing

To test the debug modes:

```bash
# Standard debug
amplifier run --profile foundry-standalone "test prompt" --debug

# Raw debug (modify profile to add raw_debug: true)
amplifier run --profile foundry-standalone "test prompt"
```

Look for events in the output:
- `llm:request` - Basic request info
- `llm:request:debug` - Truncated request details
- `llm:request:raw` - Complete request params
- `llm:response` - Basic response info
- `llm:response:debug` - Truncated response details
- `llm:response:raw` - Complete response object
