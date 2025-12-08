# Fix Summary: OpenAI SDK System Parameter Error

## Problem

```
Error: AsyncCompletions.create() got an unexpected keyword argument 'system'
```

## Root Cause

The code was incorrectly passing `system` as a keyword argument to `AsyncCompletions.create()`:

```python
# INCORRECT (old code)
params = {
    "model": model,
    "messages": openai_messages,
}
if instructions:
    params["system"] = instructions  # ❌ Not supported by OpenAI SDK
```

**OpenAI SDK 2.9.0+ does not accept `system` as a separate parameter.** System messages must be included in the `messages` array with `role: "system"`.

## Solution

Changed `_prepare_openai_params()` method in `__init__.py` to include system messages in the messages array:

```python
# CORRECT (new code)
messages_with_system = []
if instructions:
    messages_with_system.append({"role": "system", "content": instructions})
messages_with_system.extend(openai_messages)

params = {
    "model": model,
    "messages": messages_with_system,  # ✅ System message included here
}
```

## Files Modified

1. **`amplifier_module_provider_foundry_local/__init__.py`** (lines 878-887)
   - Modified `_prepare_openai_params()` to build messages array with system message

2. **`tests/test_foundry_local_provider.py`** (lines 186-193)
   - Updated test to verify system message is in messages array, not as separate parameter

3. **`tests/test_integration.py`** (lines 331-338)
   - Updated test to verify system message is in messages array, not as separate parameter

## Validation

Created validation tests to confirm the fix:

1. **`test_system_param_validation.py`** - Static code analysis
   - ✅ Confirms no `params["system"]` in code
   - ✅ Confirms system messages are added to messages array

2. **`test_complete_flow.py`** - OpenAI SDK integration test
   - ✅ Confirms correct format works
   - ✅ Confirms incorrect format fails with expected error

Run validation:
```bash
python test_system_param_validation.py
uv run python test_complete_flow.py
```

## OpenAI SDK Version

- **Current version in cache**: `2.9.0`
- **Requirement**: `>=1.0.0` (from pyproject.toml)
- **Verification**: `grep -A 5 "name = \"openai\"" uv.lock`

## API Compatibility

The fix ensures compatibility with the OpenAI Chat Completions API standard:

```python
# Standard OpenAI format (compatible with all versions)
client.chat.completions.create(
    model="model-name",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)
```

## Reinstallation

After applying the fix, reinstall the module:

```bash
uv sync
# or
uv pip install -e . --force-reinstall --no-deps
```

## References

- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [System Instructions in Chat Completions](https://platform.openai.com/docs/guides/text-generation/chat-completions-api)
- OpenAI SDK version: 2.9.0 (verified in uv.lock)
