# AI-Generated Documentation and Debug Files

This directory contains AI-generated documentation and debugging files created during the development of the Foundry Local provider for Amplifier.

## Files

### Documentation
- **`AMPLIFIER_CORE_COMPATIBILITY_ISSUE.md`** - Detailed analysis of the OpenAI client `_set_private_attributes` error during provider validation
- **`INTEGRATION_EXAMPLES.md`** - Various integration examples and configuration patterns for using Foundry Local with other Amplifier modules

### Debug Scripts
- **`amplifier_foundry_workaround.py`** - Direct OpenAI client interface to bypass provider validation issues
- **`test_direct_openai.py`** - Test script for direct OpenAI API calls to Foundry Local
- **`test_provider_direct.py`** - Test script for direct provider testing
- **`test_provider_validation.py`** - Test script to capture RuntimeWarnings during provider validation
- **`test_runtime_warning.py`** - Test script for runtime warning analysis

## Purpose

These files were generated during development to:
- Document compatibility issues between Amplifier core and Foundry Local
- Provide debugging and testing utilities
- Explore integration patterns and use cases
- Work around validation issues during development

## Status

These files are preserved for reference but are not part of the core provider functionality. The main provider implementation is in the `amplifier_module_provider_foundry_local/` directory.

## Note

The `_set_private_attributes` error documented in `AMPLIFIER_CORE_COMPATIBILITY_ISSUE.md` is a cosmetic issue that doesn't affect functionality. The provider works correctly despite the warning message during mounting.