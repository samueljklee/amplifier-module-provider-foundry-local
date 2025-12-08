"""
Foundry Local provider module for Amplifier.
Integrates with Microsoft Foundry Local for privacy-first AI, audio transcription, and hardware-optimized inference.
"""

__all__ = ["mount", "FoundryLocalProvider"]

import asyncio
import json
import logging
import os
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

logger = logging.getLogger(__name__)

# Import Foundry Local SDK - this is the official Microsoft approach
# Based on: https://learn.microsoft.com/azure/ai-foundry/foundry-local/reference/reference-sdk
FOUNDRY_LOCAL_SDK_AVAILABLE = False
FOUNDRY_LOCAL_CONFIG_AVAILABLE = False
FoundryLocalManager = None
FoundryLocalConfig = None

try:
    # Try to import the main SDK components
    from foundry_local import FoundryLocalManager
    from foundry_local.config import FoundryLocalConfig
    FOUNDRY_LOCAL_SDK_AVAILABLE = True
    FOUNDRY_LOCAL_CONFIG_AVAILABLE = True
    logger.info("✅ FoundryLocalManager SDK and Config found and available")
except ImportError:
    logger.info("ℹ️  FoundryLocalManager SDK not available - using HTTP fallback approach")
    FOUNDRY_LOCAL_SDK_AVAILABLE = False
    FOUNDRY_LOCAL_CONFIG_AVAILABLE = False
except Exception as e:
    logger.warning(f"⚠️  Error importing FoundryLocalManager SDK: {e}")
    FOUNDRY_LOCAL_SDK_AVAILABLE = False
    FOUNDRY_LOCAL_CONFIG_AVAILABLE = False


async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None):
    """Mount the Foundry Local provider."""
    config = config or {}

    # Foundry Local doesn't need API key - it's local
    # But we can check for required model
    model = config.get("default_model", DEFAULT_MODEL)

    provider = FoundryLocalProvider(config=config, coordinator=coordinator)

    # Log successful mount (like Ollama provider - no connection test during mount)
    # Connection issues will be discovered during actual use (list_models, complete, etc.)
    logger.info(f"Mounted FoundryLocalProvider at {provider._discover_foundry_endpoint()}")

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
        """Initialize Foundry Local provider with hybrid SDK/HTTP approach."""
        self.config = config or {}
        self.coordinator = coordinator
        self.manager = None
        self.hardware_capabilities = None
        self.performance_metrics = {}

        # Initialize using hybrid approach
        self._initialize_hybrid_approach()

        # Create OpenAI client pointing to Foundry Local endpoint
        if client is None:
            # Get endpoint from SDK or discover dynamically
            base_url = self._get_endpoint()
            api_key = "foundry-local-key"  # Not required but OpenAI client expects one

            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"🔗 Created OpenAI client for Foundry Local: {base_url}")

            # Test endpoint connectivity
            self._test_endpoint_connectivity(base_url)
        else:
            self.client = client
            logger.info("🔗 Using provided OpenAI client for Foundry Local")

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

        # Log initialization summary
        self._log_initialization_summary()

    def _initialize_hybrid_approach(self):
        """Initialize using hybrid SDK/HTTP approach with full feature detection."""
        if FOUNDRY_LOCAL_SDK_AVAILABLE:
            try:
                logger.info("🚀 Initializing with Foundry Local SDK...")

                # Create SDK configuration if available
                if FOUNDRY_LOCAL_CONFIG_AVAILABLE:
                    self.sdk_config = self._create_sdk_config()
                else:
                    self.sdk_config = None

                # Initialize hardware detection
                self._detect_hardware_capabilities()

                # Initialize manager with model
                model_alias = self.config.get("model_alias", "qwen2.5-7b")

                if FOUNDRY_LOCAL_CONFIG_AVAILABLE:
                    # Use rich configuration
                    self.manager = FoundryLocalManager(
                        model=model_alias,
                        config=self.sdk_config
                    )
                else:
                    # Use simple initialization
                    self.manager = FoundryLocalManager(model_alias)

                logger.info(f"✅ Initialized FoundryLocalManager with model: {model_alias}")

                # Get manager properties
                if hasattr(self.manager, 'endpoint'):
                    logger.info(f"📍 Foundry Local endpoint: {self.manager.endpoint}")
                if hasattr(self.manager, 'model_info'):
                    logger.info(f"🧠 Model info: {self.manager.model_info}")

            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize FoundryLocalManager: {e}")
                logger.info("🔄 Falling back to HTTP approach")
                self.manager = None
                self.sdk_config = None
                self._detect_hardware_capabilities_cli()
        else:
            logger.info("🌐 Using HTTP approach (SDK not available)")
            self.manager = None
            self.sdk_config = None
            self._detect_hardware_capabilities_cli()

    def _create_sdk_config(self) -> Any:
        """Create rich SDK configuration based on user settings."""
        if not FOUNDRY_LOCAL_CONFIG_AVAILABLE:
            return None

        try:
            # Create configuration based on user preferences
            config = FoundryLocalConfig()

            # Hardware optimization settings
            if self.auto_hardware_optimization:
                config.hardware_acceleration = "auto"
                config.memory_optimization = True
                config.performance_mode = "balanced"  # Options: latency, throughput, balanced
            else:
                config.hardware_acceleration = "cpu"
                config.memory_optimization = False
                config.performance_mode = "latency"

            # Model configuration
            config.offline_mode = self.offline_mode
            config.debug_mode = self.debug

            # Performance settings
            config.timeout = self.timeout
            config.max_tokens = self.max_tokens

            logger.debug(f"Created SDK config with hardware_acceleration={config.hardware_acceleration}")
            return config

        except Exception as e:
            logger.warning(f"Failed to create SDK config: {e}")
            return None

    def _detect_hardware_capabilities(self):
        """Detect hardware capabilities using SDK."""
        if self.manager and hasattr(self.manager, 'get_hardware_capabilities'):
            try:
                self.hardware_capabilities = self.manager.get_hardware_capabilities()
                logger.info("🔧 Hardware capabilities detected via SDK:")
                logger.info(f"   GPU Available: {getattr(self.hardware_capabilities, 'has_gpu', False)}")
                logger.info(f"   GPU Memory: {getattr(self.hardware_capabilities, 'gpu_memory_mb', 'Unknown')} MB")
                logger.info(f"   CPU Cores: {getattr(self.hardware_capabilities, 'cpu_cores', 'Unknown')}")
                logger.info(f"   Optimal Batch Size: {getattr(self.hardware_capabilities, 'optimal_batch_size', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Failed to detect hardware capabilities via SDK: {e}")
                self.hardware_capabilities = None
        else:
            self.hardware_capabilities = None

    def _detect_hardware_capabilities_cli(self):
        """Detect hardware capabilities using CLI fallback."""
        try:
            import subprocess
            import platform

            capabilities = {
                "platform": platform.system(),
                "has_gpu": False,
                "gpu_memory_mb": 0,
                "cpu_cores": os.cpu_count(),
                "memory_gb": 0,
                "optimal_batch_size": 1
            }

            # Try to detect GPU
            try:
                # NVIDIA GPU detection
                result = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    capabilities["has_gpu"] = True
                    capabilities["gpu_memory_mb"] = int(result.stdout.strip())
                    logger.info(f"🎮 Detected NVIDIA GPU: {capabilities['gpu_memory_mb']} MB")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass

            # System memory
            try:
                if platform.system() == "Darwin":  # macOS
                    result = subprocess.run(["sysctl", "hw.memsize"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        memory_bytes = int(result.stdout.split(":")[1].strip())
                        capabilities["memory_gb"] = memory_bytes // (1024**3)
                elif platform.system() == "Linux":
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if line.startswith("MemTotal:"):
                                memory_kb = int(line.split()[1])
                                capabilities["memory_gb"] = memory_kb // (1024**2)
                                break
            except Exception:
                pass

            # Set optimal batch size based on hardware
            if capabilities["has_gpu"] and capabilities["gpu_memory_mb"] >= 8000:
                capabilities["optimal_batch_size"] = 4
            elif capabilities["has_gpu"] and capabilities["gpu_memory_mb"] >= 4000:
                capabilities["optimal_batch_size"] = 2
            else:
                capabilities["optimal_batch_size"] = 1

            self.hardware_capabilities = capabilities
            logger.info(f"🔧 Hardware capabilities detected via CLI: {capabilities['cpu_cores']} cores, {capabilities['memory_gb']} GB RAM")

        except Exception as e:
            logger.warning(f"Failed to detect hardware capabilities: {e}")
            self.hardware_capabilities = None

    def _get_endpoint(self) -> str:
        """Get Foundry Local endpoint from SDK or discover dynamically."""
        # Try SDK first
        if self.manager and hasattr(self.manager, 'endpoint'):
            endpoint = self.manager.endpoint
            logger.info(f"✅ Using SDK endpoint: {endpoint}")
            return endpoint

        # Fallback to discovery
        endpoint = self._discover_foundry_endpoint()
        logger.info(f"🔍 Using discovered endpoint: {endpoint}")
        return endpoint

    def _log_initialization_summary(self):
        """Log comprehensive initialization summary."""
        logger.info("📋 Foundry Local Provider Initialization Summary:")
        logger.info(f"   SDK Available: {FOUNDRY_LOCAL_SDK_AVAILABLE}")
        logger.info(f"   Config Available: {FOUNDRY_LOCAL_CONFIG_AVAILABLE}")
        logger.info(f"   Manager Initialized: {self.manager is not None}")
        logger.info(f"   Hardware Optimization: {self.auto_hardware_optimization}")
        logger.info(f"   Offline Mode: {self.offline_mode}")
        logger.info(f"   Default Model: {self.default_model}")

        if self.hardware_capabilities:
            logger.info(f"   Hardware: {self.hardware_capabilities.get('cpu_cores', 'Unknown')} cores")
            if self.hardware_capabilities.get('has_gpu'):
                logger.info(f"   GPU: {self.hardware_capabilities.get('gpu_memory_mb', 'Unknown')} MB")

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
        """Generate completion using Foundry Local with performance monitoring and enhanced error handling."""
        request_id = f"req_{int(time.time() * 1000)}"
        logger.info(f"[PROVIDER] Foundry Local [{request_id}]: Received ChatRequest with {len(request.messages)} messages")

        # Use Foundry Local's model alias and resolve to full model ID
        model_alias = kwargs.get("model", self.default_model)
        actual_model_id = None

        # Enhanced model resolution with SDK
        try:
            actual_model_id = await self._resolve_model_with_sdk(model_alias)
        except Exception as e:
            logger.warning(f"[PROVIDER] [{request_id}] Model resolution failed: {e}")
            actual_model_id = self._resolve_model_alias_to_id(model_alias)

        # Performance tracking
        start_time = time.time()
        request_start = start_time

        # Emit request start event
        if self.coordinator and hasattr(self.coordinator, "hooks"):
            await self._emit_request_start(request_id, actual_model_id, request)

        # Prepare for request
        try:
            # Convert request to OpenAI format
            openai_messages = self._convert_request_to_openai(request)
            params = self._prepare_openai_params(actual_model_id, openai_messages, request, **kwargs)

            # Log request details
            logger.info(f"[PROVIDER] [{request_id}] API call - model: {params['model']}, "
                       f"tools: {len(request.tools) if request.tools else 0}, "
                       f"max_tokens: {params.get('max_tokens', 'default')}")

            # Make the API call
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**params),
                timeout=self.timeout
            )

            # Calculate performance metrics
            elapsed_ms = int((time.time() - start_time) * 1000)
            total_time = time.time() - request_start

            # Update performance metrics
            await self._update_performance_metrics(request_id, actual_model_id, response, elapsed_ms, total_time)

            # Convert OpenAI response to ChatResponse
            chat_response = self._convert_openai_response_to_chat_response(response, elapsed_ms)

            logger.info(f"[PROVIDER] [{request_id}] Response received in {elapsed_ms}ms")

            # Emit request completion event
            if self.coordinator and hasattr(self.coordinator, "hooks"):
                await self._emit_request_complete(request_id, actual_model_id, chat_response, elapsed_ms)

            return chat_response

        except asyncio.TimeoutError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(f"[PROVIDER] [{request_id}] {error_msg}")
            await self._handle_error(request_id, actual_model_id, error_msg, e, elapsed_ms)
            raise

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            error_msg = f"API error: {str(e)}"
            logger.error(f"[PROVIDER] [{request_id}] {error_msg}")
            await self._handle_error(request_id, actual_model_id, error_msg, e, elapsed_ms)
            raise

    def _discover_foundry_endpoint(self) -> str:
        """Discover Foundry Local endpoint using CLI or configuration."""
        # Use configured base_url if provided (highest priority)
        if "base_url" in self.config:
            endpoint = self.config["base_url"].rstrip('/')
            logger.info(f"✅ Using configured Foundry Local endpoint: {endpoint}")
            return endpoint

        # Try to discover via Foundry CLI
        try:
            import subprocess
            result = subprocess.run(
                ["foundry", "service", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and "running on" in result.stdout:
                # Extract endpoint from CLI output
                # Example: "Model management service is running on http://127.0.0.1:65320/openai/status"
                status_line = result.stdout.strip()
                endpoint_start = status_line.find("http://")
                if endpoint_start != -1:
                    # Extract full endpoint and remove /status
                    full_endpoint = status_line[endpoint_start:]
                    endpoint = full_endpoint.replace("/status", "")
                    logger.info(f"✅ Foundry Local endpoint discovered via CLI: {endpoint}")
                    return endpoint
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"CLI endpoint discovery failed: {e}")

        # Default fallback - use standard Foundry Local endpoint
        default_endpoint = "http://127.0.0.1:65320/v1"
        logger.info(f"ℹ️  Using default Foundry Local endpoint: {default_endpoint}")
        return default_endpoint

    def _test_endpoint_connectivity(self, endpoint: str):
        """Test if Foundry Local endpoint is accessible."""
        try:
            # Use synchronous requests for simpler connectivity test
            import requests

            try:
                # Test the models endpoint which validates OpenAI-compatible API
                test_url = f"{endpoint.rstrip('/')}/models"
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ Foundry Local endpoint connectivity verified: {test_url} {response.status_code} OK")
                else:
                    logger.warning(f"⚠️  Foundry Local endpoint returned status {response.status_code} for {test_url}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"⚠️  Foundry Local server not reachable at {endpoint}")
            except requests.exceptions.Timeout:
                logger.warning(f"⚠️  Foundry Local endpoint timeout (10s) at {endpoint}")
            except Exception as e:
                logger.warning(f"⚠️  Foundry Local endpoint test failed: {e}")

        except ImportError:
            # If requests not available, skip connectivity test
            logger.info("ℹ️  requests not available for connectivity test")

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

    # Enhanced helper methods for SDK integration and performance monitoring
    async def _resolve_model_with_sdk(self, model_alias: str) -> str:
        """Resolve model alias using SDK for enhanced model information."""
        if self.manager:
            try:
                # Try SDK model resolution first
                if hasattr(self.manager, 'get_model_info'):
                    model_info = self.manager.get_model_info(model_alias)
                    if model_info and hasattr(model_info, 'id'):
                        logger.debug(f"[SDK] Resolved model {model_alias} -> {model_info.id}")
                        return model_info.id
            except Exception as e:
                logger.debug(f"[SDK] Model resolution failed: {e}")

        # Fallback to alias resolution
        return self._resolve_model_alias_to_id(model_alias)

    async def _emit_request_start(self, request_id: str, model: str, request: ChatRequest):
        """Emit request start event for monitoring."""
        try:
            await self.coordinator.hooks.emit(
                "provider:request_start",
                {
                    "provider": self.name,
                    "request_id": request_id,
                    "model": model,
                    "message_count": len(request.messages),
                    "has_tools": bool(request.tools),
                    "tool_count": len(request.tools) if request.tools else 0,
                    "max_tokens": request.max_output_tokens,
                    "temperature": request.temperature,
                    "timestamp": time.time(),
                    "hardware_capabilities": self.hardware_capabilities,
                }
            )
        except Exception as e:
            logger.debug(f"[{request_id}] Failed to emit request start event: {e}")

    async def _emit_request_complete(self, request_id: str, model: str, response: ChatResponse, elapsed_ms: int):
        """Emit request completion event for monitoring."""
        try:
            await self.coordinator.hooks.emit(
                "provider:request_complete",
                {
                    "provider": self.name,
                    "request_id": request_id,
                    "model": model,
                    "elapsed_ms": elapsed_ms,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                    "input_tokens": response.usage.input_tokens if response.usage else 0,
                    "output_tokens": response.usage.output_tokens if response.usage else 0,
                    "finish_reason": response.finish_reason,
                    "has_tool_calls": bool(response.tool_calls),
                    "tool_call_count": len(response.tool_calls) if response.tool_calls else 0,
                    "timestamp": time.time(),
                }
            )
        except Exception as e:
            logger.debug(f"[{request_id}] Failed to emit request complete event: {e}")

    async def _update_performance_metrics(self, request_id: str, model: str, response, elapsed_ms: int, total_time: float):
        """Update internal performance metrics."""
        try:
            # Calculate tokens per second
            total_tokens = response.usage.total_tokens if response.usage else 0
            tokens_per_second = total_tokens / (total_time) if total_time > 0 else 0

            # Store in performance metrics
            self.performance_metrics[request_id] = {
                "model": model,
                "elapsed_ms": elapsed_ms,
                "total_time": total_time,
                "tokens_used": total_tokens,
                "tokens_per_second": tokens_per_second,
                "timestamp": time.time(),
                "success": True,
            }

            # Log performance if debug mode
            if self.debug and total_tokens > 0:
                logger.info(f"[PERF] {request_id}: {total_tokens} tokens in {elapsed_ms}ms "
                           f"({tokens_per_second:.1f} tokens/sec)")

        except Exception as e:
            logger.debug(f"[{request_id}] Failed to update performance metrics: {e}")

    async def _handle_error(self, request_id: str, model: str, error_msg: str, exception: Exception, elapsed_ms: int):
        """Handle errors with enhanced logging and event emission."""
        try:
            # Store error in performance metrics
            self.performance_metrics[request_id] = {
                "model": model,
                "elapsed_ms": elapsed_ms,
                "error": error_msg,
                "error_type": type(exception).__name__,
                "timestamp": time.time(),
                "success": False,
            }

            # Emit error event
            if self.coordinator and hasattr(self.coordinator, "hooks"):
                await self.coordinator.hooks.emit(
                    "provider:error",
                    {
                        "provider": self.name,
                        "request_id": request_id,
                        "model": model,
                        "error": error_msg,
                        "error_type": type(exception).__name__,
                        "elapsed_ms": elapsed_ms,
                        "timestamp": time.time(),
                        "recoverable": isinstance(exception, (asyncio.TimeoutError, ConnectionError)),
                    }
                )

            # Enhanced error categorization
            if isinstance(exception, asyncio.TimeoutError):
                logger.error(f"[{request_id}] TIMEOUT: {error_msg}")
            elif isinstance(exception, ConnectionError):
                logger.error(f"[{request_id}] CONNECTION: {error_msg}")
            elif "429" in str(exception):
                logger.error(f"[{request_id}] RATE_LIMIT: {error_msg}")
            elif "500" in str(exception):
                logger.error(f"[{request_id}] SERVER_ERROR: {error_msg}")
            else:
                logger.error(f"[{request_id}] UNKNOWN_ERROR: {error_msg}")

        except Exception as e:
            logger.debug(f"[{request_id}] Error handling failed: {e}")

    def _convert_request_to_openai(self, request: ChatRequest) -> list[dict[str, Any]]:
        """Convert Amplifier ChatRequest to OpenAI message format."""
        message_list = list(request.messages)

        # Separate system messages for instructions
        system_msgs = [m for m in message_list if m.role == "system"]
        conversation = [m for m in message_list if m.role in ("user", "assistant", "tool")]

        # Convert to OpenAI chat format
        return self._convert_messages_to_openai(conversation)

    def _prepare_openai_params(self, model: str, openai_messages: list, request: ChatRequest, **kwargs) -> dict[str, Any]:
        """Prepare OpenAI API parameters."""
        message_list = list(request.messages)
        system_msgs = [m for m in message_list if m.role == "system"]

        # Combine system messages as instructions
        instructions = (
            "\n\n".join(m.content if isinstance(m.content, str) else "" for m in system_msgs)
            if system_msgs else None
        )

        # Build parameters
        params = {
            "model": model,
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

        return params

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics summary."""
        if not self.performance_metrics:
            return {}

        # Calculate summary statistics
        successful_requests = [m for m in self.performance_metrics.values() if m.get("success")]
        failed_requests = [m for m in self.performance_metrics.values() if not m.get("success")]

        total_requests = len(self.performance_metrics)
        success_rate = len(successful_requests) / total_requests if total_requests > 0 else 0

        # Calculate averages
        if successful_requests:
            avg_latency = sum(m["elapsed_ms"] for m in successful_requests) / len(successful_requests)
            avg_tokens_per_sec = sum(m.get("tokens_per_second", 0) for m in successful_requests) / len(successful_requests)
        else:
            avg_latency = 0
            avg_tokens_per_sec = 0

        return {
            "total_requests": total_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
            "average_tokens_per_second": avg_tokens_per_sec,
            "hardware_capabilities": self.hardware_capabilities,
            "last_updated": time.time(),
        }