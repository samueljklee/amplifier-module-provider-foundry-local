"""
Foundry Local provider module for Amplifier.
Integrates with Microsoft Foundry Local for privacy-first AI, audio transcription, and hardware-optimized inference.
"""

__all__ = ["mount", "FoundryLocalProvider"]

import asyncio
import json
import logging
import time
from typing import Any
from typing import cast

from amplifier_core import ConfigField
from amplifier_core import ModelInfo
from amplifier_core import ModuleCoordinator
from amplifier_core import ProviderInfo
from amplifier_core.content_models import TextContent
from amplifier_core.content_models import ThinkingContent
from amplifier_core.content_models import ToolCallContent
from amplifier_core.message_models import ChatRequest
from amplifier_core.message_models import ChatResponse
from amplifier_core.message_models import ToolCall
from openai import AsyncOpenAI

from ._constants import DEFAULT_DEBUG_TRUNCATE_LENGTH
from ._constants import DEFAULT_MAX_TOKENS
from ._constants import DEFAULT_MODEL
from ._constants import DEFAULT_TIMEOUT
from ._constants import DEFAULT_TEMPERATURE

# Import Foundry Local SDK - this is the official Microsoft approach
try:
    from foundry_local import FoundryLocalManager
    FOUNDRY_LOCAL_SDK_AVAILABLE = True
except ImportError:
    FoundryLocalManager = None
    FOUNDRY_LOCAL_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None):
    """Mount the Foundry Local provider."""
    config = config or {}

    # Foundry Local doesn't need API key - it's local
    # But we can check for required model
    model = config.get("default_model", DEFAULT_MODEL)

    provider = FoundryLocalProvider(config=config, coordinator=coordinator)

    # Test connection but don't fail mount (like Ollama provider)
    try:
        # Simple connection test by trying to list models
        if hasattr(provider.client, 'models'):
            await provider.client.models.list()
            logger.info(f"Mounted FoundryLocalProvider at {provider._discover_foundry_endpoint()}")
        else:
            logger.warning(f"Foundry Local provider mounted but client initialization may have issues")
    except Exception as e:
        logger.warning(f"Foundry Local server is not reachable: {e}. Provider mounted but will fail on use.")

    await coordinator.mount("providers", provider, name="foundry-local")

    # Return cleanup function
    async def cleanup():
        if hasattr(provider.client, "close"):
            await provider.client.close()
        if hasattr(provider, "manager") and provider.manager:
            # Clean up Foundry Local manager
            try:
                # Note: FoundryLocalManager doesn't have explicit stop/cleanup methods
                # The OpenAI client can be closed, manager will cleanup on garbage collection
                pass
            except Exception as e:
                logger.debug(f"Error stopping Foundry Local manager: {e}")

    return cleanup


class FoundryLocalProvider:
    """Microsoft Foundry Local integration with privacy-first AI, audio transcription, and hardware optimization."""

    name = "foundry-local"
    api_label = "Foundry Local"

    def __init__(
        self,
        config: dict[str, Any],
        coordinator: ModuleCoordinator | None = None,
        client: AsyncOpenAI | None = None,
    ):
        """Initialize Foundry Local provider using official Microsoft FoundryLocalManager."""
        self.config = config or {}
        self.coordinator = coordinator
        self.manager = None

        # Initialize Foundry Local manager using official SDK
        self._initialize_foundry_manager()

        # Create OpenAI client pointing to Foundry Local endpoint
        if client is None:
            # Discover Foundry Local endpoint dynamically
            base_url = self._discover_foundry_endpoint()
            api_key = "foundry-local-key"  # Not required but OpenAI client expects one

            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"Connecting to Foundry Local OpenAI-compatible API at: {base_url}")
        else:
            self.client = client

        # Configuration with sensible defaults
        self.default_model = self.config.get("default_model", DEFAULT_MODEL)
        self.max_tokens = self.config.get("max_tokens", DEFAULT_MAX_TOKENS)
        self.temperature = self.config.get("temperature", DEFAULT_TEMPERATURE)
        self.debug = self.config.get("debug", False)
        self.debug_truncate_length = self.config.get("debug_truncate_length", DEFAULT_DEBUG_TRUNCATE_LENGTH)
        self.timeout = self.config.get("timeout", DEFAULT_TIMEOUT)

        # Foundry Local specific settings
        self.auto_hardware_optimization = self.config.get("auto_hardware_optimization", True)
        self.offline_mode = self.config.get("offline_mode", True)

        # Provider priority for selection (higher priority = preferred for privacy)
        self.priority = self.config.get("priority", 100)  # Higher than cloud providers for privacy

    def _initialize_foundry_manager(self):
        """Initialize Foundry Local manager using official Microsoft SDK if available."""
        if FOUNDRY_LOCAL_SDK_AVAILABLE:
            try:
                # Use FoundryLocalManager from official Microsoft SDK
                # Based on Microsoft docs: https://learn.microsoft.com/azure/ai-foundry/foundry-local/how-to/how-to-integrate-with-inference-sdks

                # Get default model alias - use alias instead of full model ID for automatic hardware selection
                model_alias = self.config.get("model_alias", "qwen2.5-7b")

                # Create FoundryLocalManager instance
                # This will start the Foundry Local service if not already running
                self.manager = FoundryLocalManager(model_alias)

                logger.info(f"Initialized FoundryLocalManager with model alias: {model_alias}")
                logger.info(f"Foundry Local endpoint: {self.manager.endpoint}")

            except Exception as e:
                logger.warning(f"Failed to initialize FoundryLocalManager: {e}")
                # Fallback to None - will use basic endpoint detection
                self.manager = None
        else:
            logger.info("FoundryLocalManager SDK not available, using OpenAI client directly")
            self.manager = None

    def get_info(self) -> ProviderInfo:
        """Get provider metadata."""
        return ProviderInfo(
            id="foundry-local",
            display_name="Microsoft Foundry Local",
            credential_env_vars=[],  # No credentials required - it's local!
            capabilities=["streaming", "tools", "offline", "hardware_optimized"],
            defaults={
                "model": "qwen2.5-7b-instruct-generic-gpu:4",
                "max_tokens": 2048,
                "temperature": 0.7,
                "timeout": 30.0,
                "offline_only": True,
            },
            config_fields=[
                ConfigField(
                    id="default_model",
                    display_name="Default Model",
                    field_type="choice",
                    prompt="Select default model",
                    choices=["qwen2.5-7b-instruct-generic-gpu:4", "qwen2.5-0.5b-instruct-generic-gpu:4", "phi-4-mini-instruct-generic-gpu:5", "gpt-oss-20b-generic-cpu:1"],
                    default="qwen2.5-7b-instruct-generic-gpu:4",
                ),
                ConfigField(
                    id="auto_hardware_optimization",
                    display_name="Hardware Optimization",
                    field_type="boolean",
                    prompt="Automatically optimize for CPU/GPU/NPU",
                    default=True,
                ),
                ConfigField(
                    id="offline_mode",
                    display_name="Offline Only",
                    field_type="boolean",
                    prompt="Require offline operation (no cloud fallback)",
                    default=True,
                ),
            ],
        )

    async def list_models(self) -> list[ModelInfo]:
        """
        List available Foundry Local models using dynamic discovery.

        Returns models that support tool calling and available hardware variants.
        """
        models = []

        try:
            # Use FoundryLocalManager to discover available models
            if self.manager:
                # Try to get model info from the manager
                # Based on Microsoft docs: manager.get_model_info(alias)
                common_aliases = [
                    "qwen2.5-7b", "qwen2.5-0.5b", "phi-4-mini", "qwen2.5-14b",
                    "phi-3.5-mini", "phi-3-mini-128k", "phi-3-mini-4k",
                    "mistral-7b-v0.2", "deepseek-r1-14b", "deepseek-r1-7b",
                    "qwen2.5-coder-0.5b", "qwen2.5-coder-1.5b", "qwen2.5-coder-7b",
                    "qwen2.5-coder-14b", "phi-4-mini-reasoning", "gpt-oss-20b"
                ]

                for alias in common_aliases:
                    try:
                        model_info = self.manager.get_model_info(alias)
                        if model_info:
                            # Determine capabilities based on model characteristics
                            capabilities = ["tools", "streaming", "offline", "hardware_optimized"]

                            # Add "fast" for smaller models
                            if any(size in alias for size in ["0.5b", "1.5b", "mini"]):
                                capabilities.append("fast")

                            models.append(
                                ModelInfo(
                                    id=alias,  # Use alias for automatic hardware selection
                                    display_name=model_info.display_name or alias,
                                    context_window=32768,  # Standard context window for most models
                                    max_output_tokens=2048 if "7b" in alias or "14b" in alias else 1024,
                                    capabilities=capabilities,
                                    defaults={"max_tokens": 1024, "temperature": 0.7},
                                )
                            )
                    except Exception:
                        # Model alias not available, skip
                        continue
            else:
                # Fallback to static models if manager is not available
                logger.warning("FoundryLocalManager not available, using static model list")
                static_models = {
                    "qwen2.5-7b": {
                        "display_name": "Qwen 2.5 (7B)",
                        "context_window": 32768,
                        "max_output_tokens": 2048,
                        "capabilities": ["tools", "streaming", "offline", "hardware_optimized"],
                    },
                    "qwen2.5-0.5b": {
                        "display_name": "Qwen 2.5 (0.5B)",
                        "context_window": 32768,
                        "max_output_tokens": 1024,
                        "capabilities": ["tools", "streaming", "offline", "fast", "hardware_optimized"],
                    },
                    "phi-4-mini": {
                        "display_name": "Phi-4 Mini",
                        "context_window": 4096,
                        "max_output_tokens": 1024,
                        "capabilities": ["tools", "streaming", "offline", "fast", "hardware_optimized"],
                    },
                }

                for model_id, info in static_models.items():
                    models.append(
                        ModelInfo(
                            id=model_id,
                            display_name=info["display_name"],
                            context_window=info["context_window"],
                            max_output_tokens=info["max_output_tokens"],
                            capabilities=info["capabilities"],
                            defaults={"max_tokens": 1024, "temperature": 0.7},
                        )
                    )

        except Exception as e:
            logger.error(f"Error discovering Foundry Local models: {e}")
            # Return empty list on error

        return models

    async def complete(self, request: ChatRequest, **kwargs) -> ChatResponse:
        """Generate completion using Foundry Local's OpenAI-compatible API."""
        logger.info(f"[PROVIDER] Foundry Local: Received ChatRequest with {len(request.messages)} messages")

        # Use Foundry Local's model alias and resolve to full model ID
        model_alias = kwargs.get("model", self.default_model)

        try:
            # Get actual model ID from Foundry Local manager if available
            if self.manager:
                model_info = self.manager.get_model_info(model_alias)
                if model_info:
                    actual_model_id = model_info.id
                    logger.debug(f"[PROVIDER] Using model variant: {actual_model_id}")
                else:
                    actual_model_id = self._resolve_model_alias_to_id(model_alias)
            else:
                actual_model_id = self._resolve_model_alias_to_id(model_alias)

        except Exception as e:
            logger.debug(f"[PROVIDER] Could not get model info from Foundry Local: {e}")
            actual_model_id = self._resolve_model_alias_to_id(model_alias)

        # Convert request to OpenAI format (reuse from OpenAI provider patterns)
        message_list = list(request.messages)

        # Separate system messages for instructions
        system_msgs = [m for m in message_list if m.role == "system"]
        conversation = [m for m in message_list if m.role in ("user", "assistant", "tool")]

        # Combine system messages as instructions
        instructions = (
            "\n\n".join(m.content if isinstance(m.content, str) else "" for m in system_msgs)
            if system_msgs else None
        )

        # Convert to OpenAI chat format
        openai_messages = self._convert_messages_to_openai(conversation)

        # Prepare request parameters
        params = {
            "model": actual_model_id,
            "messages": openai_messages,
        }

        if instructions:
            params["system"] = instructions

        if request.max_output_tokens:
            params["max_tokens"] = request.max_output_tokens
        elif max_tokens := kwargs.get("max_tokens", self.max_tokens):
            params["max_tokens"] = max_tokens

        if request.temperature is not None:
            params["temperature"] = request.temperature
        elif temperature := kwargs.get("temperature", self.temperature):
            params["temperature"] = temperature

        # Add tools if provided
        if request.tools:
            params["tools"] = self._convert_tools_from_request(request.tools)
            params["tool_choice"] = kwargs.get("tool_choice", "auto")
            params["parallel_tool_calls"] = kwargs.get("parallel_tool_calls", True)

        logger.info(f"[PROVIDER] Foundry Local API call - model: {params['model']}, tools: {len(request.tools) if request.tools else 0}")

        start_time = time.time()

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**params),
                timeout=self.timeout
            )
            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(f"[PROVIDER] Foundry Local response received in {elapsed_ms}ms")

            # Convert OpenAI response to ChatResponse
            return self._convert_openai_response_to_chat_response(response, elapsed_ms)

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[PROVIDER] Foundry Local API error: {e}")

            # Emit error event
            if self.coordinator and hasattr(self.coordinator, "hooks"):
                await self.coordinator.hooks.emit(
                    "provider:error",
                    {
                        "provider": self.name,
                        "model": params["model"],
                        "error": str(e),
                        "duration_ms": elapsed_ms,
                    },
                )
            raise

    def _discover_foundry_endpoint(self) -> str:
        """Discover Foundry Local endpoint dynamically."""
        # Try FoundryLocalManager first if available
        if self.manager and hasattr(self.manager, 'endpoint'):
            endpoint = self.manager.endpoint.rstrip('/') + '/v1'
            logger.info(f"Using endpoint from FoundryLocalManager: {endpoint}")
            return endpoint

        # Fallback to simple port detection using config or default
        # For now, use configured base_url or default to standard Foundry Local port
        if "base_url" in self.config:
            return self.config["base_url"].rstrip('/') + '/v1'

        # Default fallback - only warn on first call
        default_endpoint = self.config.get("base_url", "http://127.0.0.1:65320/v1")
        if not hasattr(self, '_endpoint_warning_shown'):
            logger.warning(f"Could not auto-detect Foundry Local endpoint, using default: {default_endpoint}")
            self._endpoint_warning_shown = True
        return default_endpoint

    def _resolve_model_alias_to_id(self, model_alias: str) -> str:
        """Resolve model alias to full Foundry Local model ID.

        This maps user-friendly aliases to the exact model IDs that Foundry Local expects.
        Based on the output from 'foundry model list'.
        """
        # Mapping from aliases to full model IDs (prefer GPU variants when available)
        alias_to_id = {
            # Qwen models
            "qwen2.5-7b": "qwen2.5-7b-instruct-generic-gpu:4",
            "qwen2.5-0.5b": "qwen2.5-0.5b-instruct-generic-gpu:4",
            "qwen2.5-1.5b": "qwen2.5-1.5b-instruct-generic-gpu:4",
            "qwen2.5-14b": "qwen2.5-14b-instruct-generic-gpu:4",
            "qwen2.5-coder-0.5b": "qwen2.5-coder-0.5b-instruct-generic-gpu:4",
            "qwen2.5-coder-1.5b": "qwen2.5-coder-1.5b-instruct-generic-gpu:4",
            "qwen2.5-coder-7b": "qwen2.5-coder-7b-instruct-generic-gpu:4",
            "qwen2.5-coder-14b": "qwen2.5-coder-14b-instruct-generic-gpu:4",

            # Phi models
            "phi-4": "phi-4-generic-gpu:1",
            "phi-4-mini": "phi-4-mini-instruct-generic-gpu:5",
            "phi-4-mini-reasoning": "phi-4-mini-reasoning-generic-gpu:3",
            "phi-3.5-mini": "phi-3.5-mini-instruct-generic-gpu:1",
            "phi-3-mini-128k": "phi-3-mini-128k-instruct-generic-gpu:1",
            "phi-3-mini-4k": "phi-3-mini-4k-instruct-generic-gpu:1",

            # Other models
            "mistral-7b-v0.2": "mistralai-Mistral-7B-Instruct-v0-2-generic-gpu:1",
            "deepseek-r1-14b": "deepseek-r1-distill-qwen-14b-generic-gpu:3",
            "deepseek-r1-7b": "deepseek-r1-distill-qwen-7b-generic-gpu:3",
            "gpt-oss-20b": "gpt-oss-20b-generic-cpu:1",  # CPU-only
        }

        # Return the full model ID if we have a mapping, otherwise use the alias as-is
        return alias_to_id.get(model_alias, model_alias)

    def _convert_messages_to_openai(self, messages: list) -> list[dict[str, Any]]:
        """Convert Amplifier messages to OpenAI format."""
        openai_messages = []

        for msg in messages:
            msg_dict = msg.model_dump() if hasattr(msg, "model_dump") else msg

            if isinstance(msg_dict, dict):
                role = msg_dict.get("role")
                content = msg_dict.get("content", "")

                # Handle different message types
                if role == "system":
                    continue  # System messages handled separately
                elif role == "tool":
                    # Convert tool results to user message format
                    tool_name = msg_dict.get("tool_name", "unknown")
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": msg_dict.get("tool_call_id", ""),
                        "content": f"[Tool: {tool_name}]\n{content}"
                    })
                elif role in ["user", "assistant"]:
                    # Standard messages
                    openai_messages.append({
                        "role": role,
                        "content": content if isinstance(content, str) else str(content)
                    })

        return openai_messages

    def _convert_tools_from_request(self, tools: list) -> list[dict[str, Any]]:
        """Convert ToolSpec objects to OpenAI format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.parameters,
                },
            })
        return openai_tools

    def _convert_openai_response_to_chat_response(self, response, elapsed_ms: int) -> ChatResponse:
        """Convert OpenAI response to Amplifier ChatResponse."""
        from amplifier_core.message_models import TextBlock
        from amplifier_core.message_models import ToolCallBlock
        from amplifier_core.message_models import Usage

        choice = response.choices[0]
        message = choice.message

        # Extract content blocks
        content_blocks = []
        tool_calls = []

        # Text content
        if message.content:
            content_blocks.append(TextBlock(text=message.content))

        # Tool calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_call_block = ToolCallBlock(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    input=json.loads(tool_call.function.arguments)
                )
                content_blocks.append(tool_call_block)
                tool_calls.append(ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments)
                ))

        # Usage information
        usage = Usage(
            input_tokens=response.usage.input_tokens if response.usage else 0,
            output_tokens=response.usage.output_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

        return ChatResponse(
            content=content_blocks,
            tool_calls=tool_calls if tool_calls else None,
            usage=usage,
            finish_reason=choice.finish_reason,
        )

    def parse_tool_calls(self, response: ChatResponse) -> list[ToolCall]:
        """Parse tool calls from ChatResponse."""
        if not response.tool_calls:
            return []
        return response.tool_calls