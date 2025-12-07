"""
Comprehensive integration examples for Foundry Local provider with other Amplifier modules.

This file demonstrates real-world usage patterns including:
- Tool integration (filesystem, bash, web, search)
- Orchestrator compatibility (loop-basic, loop-streaming)
- Hooks integration (logging, approval, streaming-ui)
- Hybrid cloud-local scenarios
- Privacy-first workflows
"""

import asyncio
import json
import tempfile
from pathlib import Path

# Example 1: Basic Foundry Local with Tools
FOUNDARY_LOCAL_WITH_TOOLS_CONFIG = {
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
                "audio_enabled": True,
                "offline_mode": True,
                "max_tokens": 2048,
                "temperature": 0.7,
                "debug": True,
            }
        }
    ],
    "tools": [
        {
            "module": "tool-filesystem",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-filesystem@main"
        },
        {
            "module": "tool-bash",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-bash@main"
        },
        {
            "module": "tool-web",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-web@main"
        },
        {
            "module": "tool-search",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-search@main"
        }
    ],
    "hooks": [
        {
            "module": "hooks-logging",
            "source": "git+https://github.com/microsoft/amplifier-module-hooks-logging@main",
            "config": {
                "auto_discover": True,
                "debug": True
            }
        }
    ]
}

# Example 2: Streaming with Foundry Local
FOUNDARY_LOCAL_STREAMING_CONFIG = {
    "session": {
        "orchestrator": "loop-streaming",
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
                "temperature": 0.8,
            }
        }
    ],
    "tools": [
        {
            "module": "tool-filesystem",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-filesystem@main"
        }
    ],
    "hooks": [
        {
            "module": "hooks-logging",
            "source": "git+https://github.com/microsoft/amplifier-module-hooks-logging@main",
            "config": {
                "auto_discover": True
            }
        },
        {
            "module": "hooks-streaming-ui",
            "source": "git+https://github.com/microsoft/amplifier-module-hooks-streaming-ui@main"
        }
    ]
}

# Example 3: Hybrid Cloud-Local Configuration
HYBRID_CLOUD_LOCAL_CONFIG = {
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
                "priority": 100,  # Higher priority for privacy
                "offline_mode": True,
                "auto_hardware_optimization": True,
            }
        },
        {
            "module": "provider-anthropic",
            "source": "git+https://github.com/microsoft/amplifier-module-provider-anthropic@main",
            "config": {
                "default_model": "claude-sonnet-4-5",
                "priority": 50,  # Lower priority, fallback option
                "api_key": "${ANTHROPIC_API_KEY}"
            }
        }
    ],
    "tools": [
        {
            "module": "tool-filesystem",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-filesystem@main"
        },
        {
            "module": "tool-bash",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-bash@main"
        }
    ],
    "hooks": [
        {
            "module": "hooks-logging",
            "source": "git+https://github.com/microsoft/amplifier-module-hooks-logging@main",
            "config": {
                "auto_discover": True,
                "debug": True
            }
        }
    ]
}

# Example 4: Privacy-Sensitive Configuration with Approval
PRIVACY_FOCUSED_CONFIG = {
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
                "offline_mode": True,  # Force offline mode
                "auto_hardware_optimization": True,
                "debug": True,
            }
        }
    ],
    "tools": [
        {
            "module": "tool-filesystem",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-filesystem@main",
            "config": {
                "allowed_paths": ["/tmp", "./workspace"],  # Restrict file access
                "require_approval": True  # Require approval for sensitive operations
            }
        },
        {
            "module": "tool-bash",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-bash@main",
            "config": {
                "allowed_commands": ["ls", "cat", "grep", "find"],  # Restricted command set
                "require_approval": True
            }
        }
    ],
    "hooks": [
        {
            "module": "hooks-logging",
            "source": "git+https://github.com/microsoft/amplifier-module-hooks-logging@main",
            "config": {
                "auto_discover": True,
                "debug": True,
                "log_all_content": True  # Log all content for audit trail
            }
        },
        {
            "module": "hooks-approval",
            "source": "git+https://github.com/microsoft/amplifier-module-hooks-approval@main",
            "config": {
                "require_approval_for": [
                    "tool:filesystem:write",
                    "tool:bash:execute",
                    "provider:request"
                ],
                "timeout_seconds": 300,
                "default_action": "deny"
            }
        }
    ]
}


async def example_1_basic_tool_integration():
    """Example 1: Foundry Local with comprehensive tool integration."""
    print("🔧 Example 1: Foundry Local + Tools Integration")
    print("=" * 60)

    try:
        from amplifier_core import AmplifierSession

        async with AmplifierSession(config=FOUNDARY_LOCAL_WITH_TOOLS_CONFIG) as session:
            # File system operations
            print("\n📁 File System Operations:")
            response = await session.execute(
                "Create a temporary file called 'test.txt' with some content, then read it back."
            )
            print(f"AI: {response[:200]}..." if len(response) > 200 else f"AI: {response}")

            # Bash operations
            print("\n💻 Bash Operations:")
            response = await session.execute(
                "List the files in the current directory and show the git status if this is a git repository."
            )
            print(f"AI: {response[:200]}..." if len(response) > 200 else f"AI: {response}")

            # Web operations (if available)
            print("\n🌐 Web Operations:")
            response = await session.execute(
                "Can you check if https://github.com/microsoft/amplifier is accessible and what it contains?"
            )
            print(f"AI: {response[:200]}..." if len(response) > 200 else f"AI: {response}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure Foundry Local is installed and running")


async def example_2_streaming_integration():
    """Example 2: Foundry Local with streaming orchestrator and UI."""
    print("\n⚡ Example 2: Foundry Local + Streaming Integration")
    print("=" * 60)

    try:
        from amplifier_core import AmplifierSession

        async with AmplifierSession(config=FOUNDARY_LOCAL_STREAMING_CONFIG) as session:
            print("\n🔄 Streaming Response Example:")
            response = await session.execute(
                "Write a detailed explanation of how local AI models work, including their advantages "
                "for privacy and offline operation. Make this comprehensive."
            )
            print(f"AI: {response[:300]}..." if len(response) > 300 else f"AI: {response}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure Foundry Local and required modules are installed")


async def example_3_hybrid_cloud_local():
    """Example 3: Hybrid cloud-local scenario with automatic failover."""
    print("\n🌐 Example 3: Hybrid Cloud-Local Scenario")
    print("=" * 60)

    try:
        from amplifier_core import AmplifierSession

        async with AmplifierSession(config=HYBRID_CLOUD_LOCAL_CONFIG) as session:
            print("\n🔄 Testing Provider Priority:")
            response = await session.execute(
                "Which provider are you using and why? Explain the benefits of local processing."
            )
            print(f"AI: {response}")

            # Test with a task that might benefit from cloud model
            print("\n🧠 Testing Complex Reasoning:")
            response = await session.execute(
                "Explain quantum computing in simple terms suitable for a 10-year old."
            )
            print(f"AI: {response[:300]}..." if len(response) > 300 else f"AI: {response}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 This requires both Foundry Local and Anthropic API key")


async def example_4_privacy_sensitive_workflow():
    """Example 4: Privacy-sensitive workflow with approval hooks."""
    print("\n🔒 Example 4: Privacy-Sensitive Workflow")
    print("=" * 60)

    try:
        from amplifier_core import AmplifierSession

        async with AmplifierSession(config=PRIVACY_FOCUSED_CONFIG) as session:
            print("\n🔐 Processing Sensitive Data:")
            response = await session.execute(
                "I need to process some sensitive financial data locally. "
                "Explain how you ensure privacy and security when processing this information."
            )
            print(f"AI: {response}")

            # Create a temporary workspace for sensitive operations
            print("\n📁 Secure File Operations:")
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                response = await session.execute(
                    f"Create a secure analysis report in the directory {temp_path}. "
                    f"Only use the provided directory and do not access any other files."
                )
                print(f"AI: {response[:300]}..." if len(response) > 300 else f"AI: {response}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 This example requires Foundry Local and approval hooks")


async def example_5_hardware_optimization_demo():
    """Example 5: Hardware optimization capabilities."""
    print("\n⚡ Example 5: Hardware Optimization Demo")
    print("=" * 60)

    try:
        from amplifier_core import AmplifierSession

        hardware_config = {
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
                        "debug": True,
                    }
                }
            ],
            "tools": [
                {
                    "module": "tool-bash",
                    "source": "git+https://github.com/microsoft/amplifier-module-tool-bash@main"
                }
            ],
            "hooks": [
                {
                    "module": "hooks-logging",
                    "source": "git+https://github.com/microsoft/amplifier-module-hooks-logging@main",
                    "config": {"debug": True}
                }
            ]
        }

        async with AmplifierSession(config=hardware_config) as session:
            print("\n🖥️ Hardware Capabilities:")
            response = await session.execute(
                "Check the system hardware capabilities and explain what optimizations are available "
                "for AI inference on this machine."
            )
            print(f"AI: {response}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Foundry Local provides hardware optimization information")


async def example_6_audio_transcription_demo():
    """Example 6: Audio transcription capabilities."""
    print("\n🎵 Example 6: Audio Transcription Demo")
    print("=" * 60)

    try:
        from amplifier_core import AmplifierSession

        audio_config = {
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
                        "audio": {
                            "enabled": True,
                            "transcription_model": "whisper"
                        },
                        "auto_hardware_optimization": True,
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

        async with AmplifierSession(config=audio_config) as session:
            print("\n🎙️ Audio Processing Capabilities:")
            response = await session.execute(
                "Explain how audio transcription works with local models and what formats are supported. "
                "Also describe the privacy benefits of local audio processing."
            )
            print(f"AI: {response}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Audio transcription requires Foundry Local with Whisper support")


def create_configuration_guide():
    """Create a configuration guide for different use cases."""

    guide = {
        "foundry_local_integration_guide": {
            "overview": "Foundry Local provider integration patterns for Amplifier",

            "configurations": {
                "privacy_first": PRIVACY_FOCUSED_CONFIG,
                "hybrid_cloud_local": HYBRID_CLOUD_LOCAL_CONFIG,
                "basic_integration": FOUNDARY_LOCAL_WITH_TOOLS_CONFIG,
                "streaming": FOUNDARY_LOCAL_STREAMING_CONFIG
            },

            "use_cases": {
                "development": {
                    "description": "Local development with offline AI",
                    "config": "basic_integration",
                    "benefits": ["No API costs", "Privacy", "Offline operation", "Fast response"]
                },
                "enterprise": {
                    "description": "Enterprise with sensitive data",
                    "config": "privacy_first",
                    "benefits": ["Data privacy", "Audit trail", "Approval workflows", "Local processing"]
                },
                "research": {
                    "description": "Research with hybrid capabilities",
                    "config": "hybrid_cloud_local",
                    "benefits": ["Local privacy", "Cloud capability", "Automatic failover", "Cost optimization"]
                },
                "real_time": {
                    "description": "Real-time applications",
                    "config": "streaming",
                    "benefits": ["Streaming responses", "Hardware optimization", "Low latency", "Interactive UI"]
                }
            },

            "compatibility": {
                "orchestrators": ["loop-basic", "loop-streaming", "loop-events"],
                "context_managers": ["context-simple", "context-persistent"],
                "tools": [
                    "tool-filesystem", "tool-bash", "tool-web", "tool-search",
                    "tool-task", "tool-todo"
                ],
                "hooks": [
                    "hooks-logging", "hooks-approval", "hooks-streaming-ui",
                    "hooks-backup", "hooks-redaction"
                ],
                "providers": [
                    "provider-anthropic", "provider-openai", "provider-azure-openai",
                    "provider-ollama", "provider-mock"
                ]
            }
        }
    }

    return guide


async def main():
    """Run all integration examples."""
    print("🚀 Foundry Local Provider Integration Examples")
    print("=" * 60)
    print("📋 This demonstrates Foundry Local integration with Amplifier modules")
    print("🔧 Install Foundry Local: winget install Microsoft.FoundryLocal (Windows)")
    print("                        brew install foundrylocal (macOS)")
    print()

    examples = [
        example_1_basic_tool_integration,
        example_2_streaming_integration,
        example_3_hybrid_cloud_local,
        example_4_privacy_sensitive_workflow,
        example_5_hardware_optimization_demo,
        example_6_audio_transcription_demo
    ]

    for example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"❌ Example {example_func.__name__} failed: {e}")
        print("\n" + "=" * 60)

    # Save configuration guide
    guide = create_configuration_guide()
    guide_path = Path("foundry_local_integration_guide.json")
    guide_path.write_text(json.dumps(guide, indent=2))
    print(f"📚 Configuration guide saved to: {guide_path}")

    print("\n✅ Integration examples completed!")
    print("\n🔍 Troubleshooting:")
    print("1. Ensure Foundry Local is installed and running")
    print("2. Check model availability: foundry model list")
    print("3. Install required Amplifier modules")
    print("4. Verify configuration file syntax")


if __name__ == "__main__":
    asyncio.run(main())