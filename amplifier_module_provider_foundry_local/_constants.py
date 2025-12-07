"""Constants for Foundry Local provider."""

# Default model configuration - use the actual model ID from Foundry Local
DEFAULT_MODEL = "qwen2.5-7b-instruct-generic-gpu:4"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TIMEOUT = 30.0

# Debug configuration
DEFAULT_DEBUG_TRUNCATE_LENGTH = 500

# Foundry Local specific constants
# Note: Audio transcription is not a built-in capability of Foundry Local

# Hardware optimization
MIN_MEMORY_GB = 8
RECOMMENDED_MEMORY_GB = 16