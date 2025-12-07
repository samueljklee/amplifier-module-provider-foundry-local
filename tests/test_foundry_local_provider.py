"""Tests for Foundry Local provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from amplifier_core.message_models import ChatRequest, Message, ToolSpec
from amplifier_module_provider_foundry_local import FoundryLocalProvider


class TestFoundryLocalProvider:
    """Test cases for FoundryLocalProvider."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "default_model": "qwen2.5-7b",
            "auto_hardware_optimization": True,
            "offline_mode": True,
            "max_tokens": 2048,
            "temperature": 0.7,
        }

    @pytest.fixture
    def mock_manager(self):
        """Mock Foundry Local manager."""
        manager = MagicMock()
        manager.endpoint = "http://127.0.0.1:5000"
        manager.api_key = "foundry-local-key"
        manager.get_model_info.return_value = MagicMock(id="qwen2.5-7b-cpu")
        return manager

    @pytest.fixture
    def provider(self, mock_config, mock_manager):
        """Create provider instance with mocked dependencies."""
        with patch('amplifier_module_provider_foundry_local.FoundryLocalManager') as mock_manager_class:
            mock_manager_class.return_value = mock_manager

            with patch('amplifier_module_provider_foundry_local.AsyncOpenAI') as mock_openai:
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client

                provider = FoundryLocalProvider(config=mock_config)
                provider.client = mock_client
                provider.manager = mock_manager

                return provider

    def test_provider_initialization(self, provider, mock_config):
        """Test provider initializes correctly."""
        assert provider.name == "foundry-local"
        assert provider.api_label == "Foundry Local"
        assert provider.default_model == mock_config["default_model"]
        assert provider.auto_hardware_optimization == mock_config["auto_hardware_optimization"]
        assert provider.offline_mode == mock_config["offline_mode"]

    def test_get_provider_info(self, provider):
        """Test provider metadata."""
        info = provider.get_info()

        assert info.id == "foundry-local"
        assert info.display_name == "Microsoft Foundry Local"
        assert info.credential_env_vars == []  # No credentials required
        assert "offline" in info.capabilities
        assert "tools" in info.capabilities
        assert "hardware_optimized" in info.capabilities

    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        """Test model listing."""
        models = await provider.list_models()

        assert len(models) > 0
        model_ids = [model.id for model in models]
        assert "qwen2.5-7b" in model_ids
        assert "qwen2.5-0.5b" in model_ids
        assert "phi-4-mini" in model_ids

    @pytest.mark.asyncio
    async def test_complete_basic_request(self, provider):
        """Test basic chat completion."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from Foundry Local!"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(
            input_tokens=10,
            output_tokens=15,
            total_tokens=25
        )

        provider.client.chat.completions.create.return_value = mock_response

        # Create test request
        request = ChatRequest(
            messages=[
                Message(role="user", content="Hello, Foundry Local!")
            ]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify response
        assert response.content is not None
        assert len(response.content) == 1
        assert response.content[0].text == "Hello from Foundry Local!"
        assert response.tool_calls is None
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 15

    @pytest.mark.asyncio
    async def test_complete_with_tools(self, provider):
        """Test chat completion with tools."""
        # Mock OpenAI response with tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_function"
        mock_tool_call.function.arguments = '{"arg1": "value1"}'

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

        provider.client.chat.completions.create.return_value = mock_response

        # Create test request with tools
        request = ChatRequest(
            messages=[
                Message(role="user", content="Call the test function")
            ],
            tools=[
                ToolSpec(
                    name="test_function",
                    description="A test function",
                    parameters={"type": "object", "properties": {"arg1": {"type": "string"}}}
                )
            ]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify response
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "test_function"
        assert response.tool_calls[0].arguments == {"arg1": "value1"}

    @pytest.mark.asyncio
    async def test_complete_with_system_message(self, provider):
        """Test chat completion with system message."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response with system instruction"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock(
            input_tokens=15,
            output_tokens=20,
            total_tokens=35
        )

        provider.client.chat.completions.create.return_value = mock_response

        # Create test request with system message
        request = ChatRequest(
            messages=[
                Message(role="system", content="You are a helpful assistant."),
                Message(role="user", content="Hello!")
            ]
        )

        # Execute completion
        response = await provider.complete(request)

        # Verify the API was called with system message
        provider.client.chat.completions.create.assert_called_once()
        call_args = provider.client.chat.completions.create.call_args[1]
        assert "system" in call_args
        assert call_args["system"] == "You are a helpful assistant."

    def test_convert_tools_to_openai_format(self, provider):
        """Test tool conversion to OpenAI format."""
        tools = [
            ToolSpec(
                name="get_weather",
                description="Get current weather",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["city"]
                }
            )
        ]

        openai_tools = provider._convert_tools_from_request(tools)

        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"
        assert openai_tools[0]["function"]["name"] == "get_weather"
        assert openai_tools[0]["function"]["description"] == "Get current weather"
        assert "city" in openai_tools[0]["function"]["parameters"]["properties"]

    def test_convert_messages_to_openai_format(self, provider):
        """Test message conversion to OpenAI format."""
        messages = [
            Message(role="system", content="System instruction"),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
            Message(role="tool", content="Tool result", tool_name="test_tool", tool_call_id="call_123"),
        ]

        openai_messages = provider._convert_messages_to_openai(messages)

        # System messages should be filtered out
        roles = [msg["role"] for msg in openai_messages]
        assert "system" not in roles

        # Check user message
        user_messages = [msg for msg in openai_messages if msg["role"] == "user"]
        assert len(user_messages) == 1
        assert user_messages[0]["content"] == "Hello"

        # Check assistant message
        assistant_messages = [msg for msg in openai_messages if msg["role"] == "assistant"]
        assert len(assistant_messages) == 1
        assert assistant_messages[0]["content"] == "Hi there!"

        # Check tool message
        tool_messages = [msg for msg in openai_messages if msg["role"] == "tool"]
        assert len(tool_messages) == 1
        assert "test_tool" in tool_messages[0]["content"]

    def test_parse_tool_calls(self, provider):
        """Test parsing tool calls from response."""
        from amplifier_core.message_models import ToolCall

        # Create mock response with tool calls
        response = MagicMock()
        response.tool_calls = [
            ToolCall(id="call_1", name="func1", arguments={"arg": "value1"}),
            ToolCall(id="call_2", name="func2", arguments={"arg": "value2"}),
        ]

        # Parse tool calls
        parsed_calls = provider.parse_tool_calls(response)

        assert len(parsed_calls) == 2
        assert parsed_calls[0].name == "func1"
        assert parsed_calls[1].name == "func2"

    @pytest.mark.asyncio
    async def test_complete_api_error_handling(self, provider):
        """Test error handling during API calls."""
        # Mock API error
        provider.client.chat.completions.create.side_effect = Exception("API Error")

        request = ChatRequest(
            messages=[Message(role="user", content="Test")]
        )

        # Should raise the exception
        with pytest.raises(Exception, match="API Error"):
            await provider.complete(request)

    def test_foundry_manager_initialization_failure(self, mock_config):
        """Test handling of Foundry Local manager initialization failure."""
        with patch('amplifier_module_provider_foundry_local.FoundryLocalManager') as mock_manager_class:
            mock_manager_class.side_effect = ImportError("foundry-local not found")

            with pytest.raises(ImportError, match="foundry-local package is required"):
                FoundryLocalProvider(config=mock_config)


@pytest.mark.asyncio
async def test_mount_function():
    """Test the mount function."""
    mock_coordinator = MagicMock()
    mock_config = {"default_model": "qwen2.5-7b"}

    with patch('amplifier_module_provider_foundry_local.FoundryLocalProvider') as mock_provider_class:
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        with patch('amplifier_module_provider_foundry_local.FoundryLocalManager'):
            from amplifier_module_provider_foundry_local import mount

            cleanup = await mount(mock_coordinator, mock_config)

            # Verify coordinator.mount was called
            mock_coordinator.mount.assert_called_once_with("providers", mock_provider, name="foundry-local")

            # Verify cleanup function is returned
            assert cleanup is not None
            assert callable(cleanup)