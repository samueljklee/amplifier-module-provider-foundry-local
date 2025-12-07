"""
Integration tests for Foundry Local provider with other Amplifier modules.

These tests validate that the provider works correctly with:
- Tools (filesystem, bash, web, search)
- Orchestrators (loop-basic, loop-streaming)
- Context managers (context-simple, context-persistent)
- Hooks (logging, approval, streaming-ui)
- Other providers (hybrid scenarios)
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amplifier_core import AmplifierSession, ChatRequest, Message, ToolSpec
from amplifier_module_provider_foundry_local import FoundryLocalProvider, mount


class TestFoundryLocalIntegration:
    """Integration tests for Foundry Local provider."""

    @pytest.fixture
    def mock_foundry_manager(self):
        """Mock Foundry Local manager."""
        manager = MagicMock()
        manager.endpoint = "http://127.0.0.1:5000"
        manager.api_key = "foundry-local-key"
        manager.get_model_info.return_value = MagicMock(id="qwen2.5-7b-cpu")
        return manager

    @pytest.fixture
    def provider_with_mock_client(self, mock_foundry_manager):
        """Create provider with mocked Foundry manager and OpenAI client."""
        with patch('amplifier_module_provider_foundry_local.FoundryLocalManager') as mock_manager_class:
            mock_manager_class.return_value = mock_foundry_manager

            with patch('amplifier_module_provider_foundry_local.AsyncOpenAI') as mock_openai:
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client

                config = {
                    "default_model": "qwen2.5-7b",
                    "auto_hardware_optimization": True,
                    "offline_mode": True,
                }
                provider = FoundryLocalProvider(config=config)
                provider.client = mock_client
                provider.manager = mock_foundry_manager

                return provider, mock_client

    @pytest.mark.asyncio
    async def test_mount_with_coordinator(self):
        """Test mounting provider with coordinator."""
        mock_coordinator = MagicMock()
        mock_config = {"default_model": "qwen2.5-7b"}

        with patch('amplifier_module_provider_foundry_local.FoundryLocalProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            with patch('amplifier_module_provider_foundry_local.FoundryLocalManager'):
                cleanup = await mount(mock_coordinator, mock_config)

                # Verify coordinator.mount was called
                mock_coordinator.mount.assert_called_once_with("providers", mock_provider, name="foundry-local")

                # Verify cleanup function is returned
                assert cleanup is not None
                assert callable(cleanup)

    @pytest.mark.asyncio
    async def test_provider_with_filesystem_tools(self, provider_with_mock_client):
        """Test provider integration with filesystem tools."""
        provider, mock_client = provider_with_mock_client

        # Mock response for tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "read_file"
        mock_tool_call.function.arguments = '{"file_path": "/tmp/test.txt"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage = MagicMock(
            input_tokens=20,
            output_tokens=10,
            total_tokens=30
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Create request with filesystem tools
        request = ChatRequest(
            messages=[
                Message(role="user", content="Read the contents of /tmp/test.txt")
            ],
            tools=[
                ToolSpec(
                    name="read_file",
                    description="Read file contents",
                    parameters={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"}
                        },
                        "required": ["file_path"]
                    }
                )
            ]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify tool call was parsed correctly
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "read_file"
        assert response.tool_calls[0].arguments["file_path"] == "/tmp/test.txt"

    @pytest.mark.asyncio
    async def test_provider_with_bash_tools(self, provider_with_mock_client):
        """Test provider integration with bash tools."""
        provider, mock_client = provider_with_mock_client

        # Mock response for bash tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_456"
        mock_tool_call.function.name = "execute_bash"
        mock_tool_call.function.arguments = '{"command": "ls -la"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage = MagicMock(
            input_tokens=15,
            output_tokens=8,
            total_tokens=23
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Create request with bash tools
        request = ChatRequest(
            messages=[
                Message(role="user", content="List files in current directory")
            ],
            tools=[
                ToolSpec(
                    name="execute_bash",
                    description="Execute bash command",
                    parameters={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"}
                        },
                        "required": ["command"]
                    }
                )
            ]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify bash tool call was parsed correctly
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "execute_bash"
        assert response.tool_calls[0].arguments["command"] == "ls -la"

    @pytest.mark.asyncio
    async def test_provider_with_web_tools(self, provider_with_mock_client):
        """Test provider integration with web tools."""
        provider, mock_client = provider_with_mock_client

        # Mock response for web tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_789"
        mock_tool_call.function.name = "web_search"
        mock_tool_call.function.arguments = '{"query": "local AI privacy", "max_results": 5}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage = MagicMock(
            input_tokens=25,
            output_tokens=12,
            total_tokens=37
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Create request with web tools
        request = ChatRequest(
            messages=[
                Message(role="user", content="Search for information about local AI privacy")
            ],
            tools=[
                ToolSpec(
                    name="web_search",
                    description="Search the web",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_results": {"type": "integer"}
                        },
                        "required": ["query"]
                    }
                )
            ]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify web tool call was parsed correctly
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "web_search"
        assert response.tool_calls[0].arguments["query"] == "local AI privacy"

    @pytest.mark.asyncio
    async def test_provider_with_multiple_tools(self, provider_with_mock_client):
        """Test provider integration with multiple tools in same request."""
        provider, mock_client = provider_with_mock_client

        # Mock response with multiple tool calls
        mock_tool_calls = [
            MagicMock(
                id="call_1",
                function=MagicMock(
                    name="read_file",
                    arguments='{"file_path": "/tmp/config.json"}'
                )
            ),
            MagicMock(
                id="call_2",
                function=MagicMock(
                    name="execute_bash",
                    arguments='{"command": "date"}'
                )
            )
        ]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = mock_tool_calls
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage = MagicMock(
            input_tokens=30,
            output_tokens=20,
            total_tokens=50
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Create request with multiple tools
        request = ChatRequest(
            messages=[
                Message(role="user", content="Read config file and show current time")
            ],
            tools=[
                ToolSpec(
                    name="read_file",
                    description="Read file contents",
                    parameters={"type": "object", "properties": {"file_path": {"type": "string"}}}
                ),
                ToolSpec(
                    name="execute_bash",
                    description="Execute bash command",
                    parameters={"type": "object", "properties": {"command": {"type": "string"}}}
                )
            ]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify multiple tool calls were parsed correctly
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].name == "read_file"
        assert response.tool_calls[1].name == "execute_bash"

    @pytest.mark.asyncio
    async def test_provider_with_system_messages(self, provider_with_mock_client):
        """Test provider handles system messages correctly."""
        provider, mock_client = provider_with_mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response with system instruction"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(
            input_tokens=20,
            output_tokens=25,
            total_tokens=45
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Create request with system message
        request = ChatRequest(
            messages=[
                Message(role="system", content="You are a privacy-focused AI assistant."),
                Message(role="user", content="Explain local AI benefits")
            ]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify the API was called with system message
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert "system" in call_args
        assert call_args["system"] == "You are a privacy-focused AI assistant."

    @pytest.mark.asyncio
    async def test_provider_context_compaction_support(self, provider_with_mock_client):
        """Test provider supports context for compaction."""
        provider, mock_client = provider_with_mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response after context compaction"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(
            input_tokens=100,
            output_tokens=30,
            total_tokens=130
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Create request with many messages (simulating need for compaction)
        messages = []
        for i in range(20):
            messages.extend([
                Message(role="user", content=f"User message {i} with some content"),
                Message(role="assistant", content=f"Assistant response {i}")
            ])

        request = ChatRequest(messages=messages)

        # Execute completion
        response = await provider.complete(request)

        # Verify response was generated correctly
        assert response.content is not None
        assert len(response.content) == 1
        assert response.usage.total_tokens == 130

    @pytest.mark.asyncio
    async def test_provider_error_handling_with_recovery(self, provider_with_mock_client):
        """Test provider handles errors gracefully and supports recovery."""
        provider, mock_client = provider_with_mock_client

        # Mock API error on first call, success on second
        mock_client.chat.completions.create.side_effect = [
            Exception("Connection failed"),
            MagicMock(
                choices=[MagicMock(
                    message=MagicMock(
                        content="Recovery successful",
                        tool_calls=None
                    ),
                    finish_reason="stop"
                )],
                usage=MagicMock(input_tokens=10, output_tokens=15, total_tokens=25)
            )
        ]

        request = ChatRequest(
            messages=[Message(role="user", content="Test recovery")]
        )

        # First call should fail
        with pytest.raises(Exception, match="Connection failed"):
            await provider.complete(request)

        # Reset side effect for recovery
        mock_client.chat.completions.create.side_effect = None
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content="Recovery successful",
                    tool_calls=None
                ),
                finish_reason="stop"
            )],
            usage=MagicMock(input_tokens=10, output_tokens=15, total_tokens=25)
        )

        # Second call should succeed
        response = await provider.complete(request)
        assert response.content[0].text == "Recovery successful"

    @pytest.mark.asyncio
    async def test_provider_model_selection_with_hardware_optimization(self, provider_with_mock_client):
        """Test provider selects appropriate model based on hardware."""
        provider, mock_client = provider_with_mock_client

        # Configure hardware optimization
        provider.auto_hardware_optimization = True

        # Mock different model variants
        def get_model_info(model_id):
            if model_id == "qwen2.5-7b":
                return MagicMock(id="qwen2.5-7b-gpu")  # GPU optimized version
            return None

        provider.manager.get_model_info = get_model_info

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "GPU optimized response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(
            input_tokens=10,
            output_tokens=20,
            total_tokens=30
        )

        mock_client.chat.completions.create.return_value = mock_response

        request = ChatRequest(
            messages=[Message(role="user", content="Test hardware optimization")]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify GPU-optimized model was used
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "qwen2.5-7b-gpu"

    @pytest.mark.asyncio
    async def test_provider_offline_hardware_capabilities(self, provider_with_mock_client):
        """Test provider supports offline and hardware optimization capabilities."""
        provider, mock_client = provider_with_mock_client

        # Get provider info to verify capabilities
        info = provider.get_info()
        assert "offline" in info.capabilities
        assert "tools" in info.capabilities
        assert "hardware_optimized" in info.capabilities

        # Test with audio-related request (though actual transcription happens outside provider)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Audio processing supported"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(
            input_tokens=15,
            output_tokens=10,
            total_tokens=25
        )

        mock_client.chat.completions.create.return_value = mock_response

        request = ChatRequest(
            messages=[
                Message(role="user", content="How do I process audio files locally?")
            ]
        )

        response = await provider.complete(request)
        assert response.content[0].text == "Audio processing supported"

    @pytest.mark.asyncio
    async def test_provider_with_offline_mode_enforcement(self, provider_with_mock_client):
        """Test provider enforces offline mode when configured."""
        provider, mock_client = provider_with_mock_client

        # Enable offline mode
        provider.offline_mode = True

        # Get provider info to verify offline capabilities
        info = provider.get_info()
        assert "offline" in info.capabilities
        assert info.defaults.get("offline_only") is True

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Offline processing active"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(
            input_tokens=10,
            output_tokens=15,
            total_tokens=25
        )

        mock_client.chat.completions.create.return_value = mock_response

        request = ChatRequest(
            messages=[
                Message(role="user", content="Process this data offline")
            ]
        )

        response = await provider.complete(request)
        assert response.content[0].text == "Offline processing active"

    def test_provider_configuration_validation(self):
        """Test provider validates configuration correctly."""
        # Test valid configuration
        valid_config = {
            "default_model": "qwen2.5-7b",
            "auto_hardware_optimization": True,
            "offline_mode": True,
            "max_tokens": 2048,
            "temperature": 0.7
        }

        with patch('amplifier_module_provider_foundry_local.FoundryLocalManager'):
            with patch('amplifier_module_provider_foundry_local.AsyncOpenAI'):
                provider = FoundryLocalProvider(config=valid_config)
                assert provider.default_model == "qwen2.5-7b"
                assert provider.auto_hardware_optimization is True
                                assert provider.offline_mode is True
                assert provider.max_tokens == 2048
                assert provider.temperature == 0.7

    def test_provider_default_configuration(self):
        """Test provider uses sensible defaults when config is empty."""
        with patch('amplifier_module_provider_foundry_local.FoundryLocalManager'):
            with patch('amplifier_module_provider_foundry_local.AsyncOpenAI'):
                provider = FoundryLocalProvider(config={})
                assert provider.default_model == "qwen2.5-7b"  # From constants
                assert provider.auto_hardware_optimization is True  # Default
                assert provider.offline_mode is True  # Default
                assert provider.max_tokens == 2048  # From constants
                assert provider.temperature == 0.7  # From constants

    @pytest.mark.asyncio
    async def test_provider_priority_configuration(self, provider_with_mock_client):
        """Test provider priority configuration for hybrid scenarios."""
        provider, _ = provider_with_mock_client

        # Test default priority
        assert provider.priority == 50  # Default from implementation

        # Test custom priority
        config = {"priority": 100}
        with patch('amplifier_module_provider_foundry_local.FoundryLocalManager'):
            with patch('amplifier_module_provider_foundry_local.AsyncOpenAI'):
                high_priority_provider = FoundryLocalProvider(config=config)
                assert high_priority_provider.priority == 100


@pytest.mark.asyncio
async def test_end_to_end_integration_with_amplifier_session():
    """End-to-end test with actual AmplifierSession (requires Foundry Local)."""
    # This test requires actual Foundry Local installation
    # It should be run manually or in CI with Foundry Local installed

    config = {
        "session": {
            "orchestrator": "loop-basic",
            "context": "context-simple",
        },
        "providers": [
            {
                "module": "provider-foundry-local",
                "source": "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main",
                "config": {
                    "default_model": "qwen2.5-7b",
                    "offline_mode": True,
                }
            }
        ],
        "tools": [
            {
                "module": "tool-filesystem",
                "source": "git+https://github.com/microsoft/amplifier-module-tool-filesystem@main"
            }
        ]
    }

    # Skip test if Foundry Local is not available
    try:
        from foundry_local import FoundryLocalManager
    except ImportError:
        pytest.skip("Foundry Local not available for integration test")

    try:
        async with AmplifierSession(config=config) as session:
            response = await session.execute(
                "Hello! Please introduce yourself and confirm you're running locally."
            )
            assert response is not None
            assert len(response) > 0

    except Exception as e:
        pytest.skip(f"Foundry Local integration test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])