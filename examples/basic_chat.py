"""
Basic Foundry Local chat example.

This example demonstrates using Foundry Local for privacy-first AI chat
with tool calling support.
"""

import asyncio
from amplifier_core import AmplifierSession, ChatRequest, Message

# Example configuration for Foundry Local provider
CONFIG = {
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
                "auto_hardware_optimization": True,
                "offline_mode": True,
                "max_tokens": 2048,
                "temperature": 0.7,
                "debug": True,
            }
        }
    ],
    "tools": [
        {"module": "tool-filesystem"},
        {"module": "tool-bash"},
    ]
}


async def basic_chat_example():
    """Example: Basic chat conversation."""
    print("🤖 Foundry Local Basic Chat Example")
    print("=" * 50)

    async with AmplifierSession(config=CONFIG) as session:
        # Simple greeting
        response = await session.execute(
            "Hello! Please introduce yourself and explain what makes you different from cloud AI models."
        )

        print(f"AI: {response}")
        print()


async def tool_calling_example():
    """Example: Using tools with Foundry Local."""
    print("🔧 Foundry Local Tool Calling Example")
    print("=" * 50)

    async with AmplifierSession(config=CONFIG) as session:
        # File system operation
        response = await session.execute(
            "List the files in the current directory and tell me what kind of project this is."
        )

        print(f"AI: {response}")
        print()


async def privacy_sensitive_example():
    """Example: Processing sensitive data locally."""
    print("🔒 Foundry Local Privacy-Sensitive Example")
    print("=" * 50)

    async with AmplifierSession(config=CONFIG) as session:
        # Simulate processing sensitive information
        response = await session.execute(
            "I need to process some sensitive financial data locally. "
            "Can you explain how you ensure privacy when processing this type of data?"
        )

        print(f"AI: {response}")
        print()


async def hardware_optimization_example():
    """Example: Hardware optimization demonstration."""
    print("⚡ Foundry Local Hardware Optimization Example")
    print("=" * 50)

    async with AmplifierSession(config=CONFIG) as session:
        # Ask about hardware capabilities
        response = await session.execute(
            "What hardware optimizations are available for AI inference, "
            "and how do they improve performance?"
        )

        print(f"AI: {response}")
        print()


async def main():
    """Run all examples."""
    print("🚀 Foundry Local Provider Examples")
    print("📋 This requires Foundry Local to be installed and running")
    print("🔧 Install with: winget install Microsoft.FoundryLocal (Windows)")
    print("          or: brew install foundrylocal (macOS)")
    print()

    try:
        await basic_chat_example()
        await tool_calling_example()
        await privacy_sensitive_example()
        await hardware_optimization_example()

        print("✅ All examples completed successfully!")

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print()
        print("🔍 Troubleshooting:")
        print("1. Make sure Foundry Local is installed: foundry --version")
        print("2. Make sure a model is downloaded: foundry model list")
        print("3. Download a model if needed: foundry model run qwen2.5-7b")
        print("4. Check Foundry Local service: foundry service status")


if __name__ == "__main__":
    asyncio.run(main())