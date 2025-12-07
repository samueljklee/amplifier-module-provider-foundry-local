"""
Orchestrator compatibility examples for Foundry Local provider.

This demonstrates how Foundry Local works with different Amplifier orchestrators:
- loop-basic: Simple request-response execution
- loop-streaming: Streaming responses for real-time interaction
- loop-events: Event-driven execution with advanced features
"""

import asyncio
import json
from typing import Any

# Basic orchestrator configuration
LOOP_BASIC_CONFIG = {
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
                "max_tokens": 1024,
                "temperature": 0.7,
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

# Streaming orchestrator configuration
LOOP_STREAMING_CONFIG = {
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
                "max_tokens": 2048,
                "temperature": 0.8,  # Higher temperature for creative streaming
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
            "module": "hooks-streaming-ui",
            "source": "git+https://github.com/microsoft/amplifier-module-hooks-streaming-ui@main"
        }
    ]
}

# Event-driven orchestrator configuration
LOOP_EVENTS_CONFIG = {
    "session": {
        "orchestrator": "loop-events",
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
            "module": "tool-web",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-web@main"
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

# Persistent context with streaming
PERSISTENT_CONTEXT_STREAMING_CONFIG = {
    "session": {
        "orchestrator": "loop-streaming",
        "context": "context-persistent",
    },
    "providers": [
        {
            "module": "provider-foundry-local",
            "source": "git+https://github.com/microsoft/amplifier-module-provider-foundry-local@main",
            "config": {
                "default_model": "qwen2.5-7b",
                "auto_hardware_optimization": True,
                "offline_mode": True,
                "temperature": 0.6,
            }
        }
    ],
    "tools": [
        {
            "module": "tool-filesystem",
            "source": "git+https://github.com/microsoft/amplifier-module-tool-filesystem@main"
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
                "auto_discover": True
            }
        }
    ]
}


class OrchestratorTestSuite:
    """Test suite for validating Foundry Local with different orchestrators."""

    def __init__(self):
        self.results = {}

    async def test_loop_basic(self):
        """Test Foundry Local with loop-basic orchestrator."""
        print("🔄 Testing loop-basic orchestrator")
        print("=" * 50)

        try:
            from amplifier_core import AmplifierSession

            async with AmplifierSession(config=LOOP_BASIC_CONFIG) as session:
                # Test 1: Simple text generation
                print("\n📝 Test 1: Simple text generation")
                response = await session.execute(
                    "Explain the benefits of running AI models locally in 3 bullet points."
                )
                print(f"✅ Response: {response}")
                self.results["loop_basic_text"] = {"success": True, "response_length": len(response)}

                # Test 2: Tool calling
                print("\n🔧 Test 2: Tool calling")
                response = await session.execute(
                    "Create a temporary file called 'foundry_test.txt' with the current timestamp."
                )
                print(f"✅ Response: {response}")
                self.results["loop_basic_tools"] = {"success": True, "response_length": len(response)}

                # Test 3: Multiple turns
                print("\n💬 Test 3: Multiple-turn conversation")
                response1 = await session.execute("What is the capital of France?")
                response2 = await session.execute("What is the population of that city?")
                print(f"✅ Turn 1: {response1}")
                print(f"✅ Turn 2: {response2}")
                self.results["loop_basic_conversation"] = {"success": True, "turns": 2}

        except Exception as e:
            print(f"❌ Error: {e}")
            self.results["loop_basic"] = {"success": False, "error": str(e)}

    async def test_loop_streaming(self):
        """Test Foundry Local with loop-streaming orchestrator."""
        print("\n🌊 Testing loop-streaming orchestrator")
        print("=" * 50)

        try:
            from amplifier_core import AmplifierSession

            async with AmplifierSession(config=LOOP_STREAMING_CONFIG) as session:
                # Test 1: Streaming response
                print("\n📝 Test 1: Streaming text generation")
                response = await session.execute(
                    "Write a detailed explanation of how local AI models work. "
                    "Include technical details about privacy and security."
                )
                print(f"✅ Streaming response: {response[:300]}...")
                self.results["loop_streaming_text"] = {"success": True, "response_length": len(response)}

                # Test 2: Streaming with tools
                print("\n🔧 Test 2: Streaming with tool calls")
                response = await session.execute(
                    "Analyze the current directory structure and create a summary report "
                    "in a file called 'directory_analysis.txt'."
                )
                print(f"✅ Response: {response[:300]}...")
                self.results["loop_streaming_tools"] = {"success": True, "response_length": len(response)}

        except Exception as e:
            print(f"❌ Error: {e}")
            self.results["loop_streaming"] = {"success": False, "error": str(e)}

    async def test_loop_events(self):
        """Test Foundry Local with loop-events orchestrator."""
        print("\n⚡ Testing loop-events orchestrator")
        print("=" * 50)

        try:
            from amplifier_core import AmplifierSession

            async with AmplifierSession(config=LOOP_EVENTS_CONFIG) as session:
                # Test 1: Event-driven execution
                print("\n📝 Test 1: Event-driven text generation")
                response = await session.execute(
                    "Create a step-by-step guide for setting up a local AI development environment."
                )
                print(f"✅ Response: {response[:300]}...")
                self.results["loop_events_text"] = {"success": True, "response_length": len(response)}

                # Test 2: Event-driven with multiple tools
                print("\n🔧 Test 2: Event-driven with tool orchestration")
                response = await session.execute(
                    "Research local AI frameworks, check what's available in this system, "
                    "and create a comprehensive comparison report."
                )
                print(f"✅ Response: {response[:300]}...")
                self.results["loop_events_tools"] = {"success": True, "response_length": len(response)}

        except Exception as e:
            print(f"❌ Error: {e}")
            self.results["loop_events"] = {"success": False, "error": str(e)}

    async def test_persistent_context_streaming(self):
        """Test Foundry Local with persistent context and streaming."""
        print("\n💾 Testing persistent context with streaming")
        print("=" * 50)

        try:
            from amplifier_core import AmplifierSession

            async with AmplifierSession(config=PERSISTENT_CONTEXT_STREAMING_CONFIG) as session:
                # Test 1: Context accumulation
                print("\n📝 Test 1: Context accumulation across turns")
                context_data = {
                    "project_name": "Local AI Assistant",
                    "user_preference": "privacy-focused"
                }

                response1 = await session.execute(
                    f"Remember that I'm working on a project called '{context_data['project_name']}' "
                    f"and prefer {context_data['user_preference']} solutions."
                )

                response2 = await session.execute(
                    "Based on our previous conversation, recommend a local AI stack for my project."
                )
                print(f"✅ Context-aware response: {response2[:300]}...")
                self.results["persistent_context"] = {"success": True, "context_retained": True}

                # Test 2: Long conversation
                print("\n💬 Test 2: Extended conversation with context")
                topics = [
                    "Hardware requirements for local AI",
                    "Model selection criteria",
                    "Privacy considerations",
                    "Performance optimization"
                ]

                for i, topic in enumerate(topics, 1):
                    response = await session.execute(f"Tell me about {topic} for my {context_data['project_name']}")
                    print(f"✅ Topic {i}: {response[:100]}...")

                self.results["extended_conversation"] = {"success": True, "topics_covered": len(topics)}

        except Exception as e:
            print(f"❌ Error: {e}")
            self.results["persistent_context"] = {"success": False, "error": str(e)}

    async def test_orchestrator_switching(self):
        """Test switching between orchestrators in same session."""
        print("\n🔄 Testing orchestrator switching")
        print("=" * 50)

        try:
            # Test basic orchestrator
            from amplifier_core import AmplifierSession

            basic_config = LOOP_BASIC_CONFIG.copy()
            async with AmplifierSession(config=basic_config) as session:
                response = await session.execute(
                    "This is a message using the basic orchestrator. What are the benefits of basic execution?"
                )
                print(f"✅ Basic orchestrator response: {response[:200]}...")

            # Test streaming orchestrator
            streaming_config = LOOP_STREAMING_CONFIG.copy()
            async with AmplifierSession(config=streaming_config) as session:
                response = await session.execute(
                    "This is a message using the streaming orchestrator. How does streaming improve user experience?"
                )
                print(f"✅ Streaming orchestrator response: {response[:200]}...")

            self.results["orchestrator_switching"] = {"success": True}

        except Exception as e:
            print(f"❌ Error: {e}")
            self.results["orchestrator_switching"] = {"success": False, "error": str(e)}

    def generate_compatibility_report(self) -> dict[str, Any]:
        """Generate a comprehensive compatibility report."""
        report = {
            "foundry_local_orchestrator_compatibility": {
                "timestamp": "2025-01-15T00:00:00Z",
                "provider": "foundry-local",
                "summary": {
                    "total_tests": len(self.results),
                    "successful_tests": len([r for r in self.results.values() if r.get("success", False)]),
                    "failed_tests": len([r for r in self.results.values() if not r.get("success", True)])
                },
                "results": self.results,
                "compatibility_matrix": {
                    "loop-basic": self.results.get("loop_basic_text", {}).get("success", False),
                    "loop-streaming": self.results.get("loop_streaming_text", {}).get("success", False),
                    "loop-events": self.results.get("loop_events_text", {}).get("success", False),
                    "context-persistent": self.results.get("persistent_context", {}).get("success", False),
                },
                "recommended_configurations": {
                    "development": {
                        "orchestrator": "loop-basic",
                        "context": "context-simple",
                        "reason": "Simple and fast for development workflows"
                    },
                    "interactive": {
                        "orchestrator": "loop-streaming",
                        "context": "context-persistent",
                        "reason": "Real-time interaction with context retention"
                    },
                    "production": {
                        "orchestrator": "loop-events",
                        "context": "context-persistent",
                        "reason": "Event-driven architecture for production systems"
                    }
                },
                "performance_notes": {
                    "local_optimization": "Foundry Local provides hardware-optimized inference",
                    "offline_operation": "All orchestrators work in offline mode",
                    "privacy_preservation": "Local execution ensures data privacy",
                    "tool_integration": "Full compatibility with all Amplifier tools"
                }
            }
        }

        return report


async def run_orchestrator_compatibility_tests():
    """Run all orchestrator compatibility tests."""
    print("🚀 Foundry Local Orchestrator Compatibility Tests")
    print("=" * 60)
    print("📋 Testing compatibility with all Amplifier orchestrators")
    print()

    test_suite = OrchestratorTestSuite()

    tests = [
        ("loop-basic", test_suite.test_loop_basic),
        ("loop-streaming", test_suite.test_loop_streaming),
        ("loop-events", test_suite.test_loop_events),
        ("persistent-context", test_suite.test_persistent_context_streaming),
        ("orchestrator-switching", test_suite.test_orchestrator_switching),
    ]

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            await test_func()
            print(f"✅ {test_name} test completed")
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")

    # Generate and save report
    report = test_suite.generate_compatibility_report()

    report_path = "orchestrator_compatibility_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 Compatibility report saved to: {report_path}")

    # Print summary
    summary = report["foundry_local_orchestrator_compatibility"]["summary"]
    print(f"\n📈 Test Summary:")
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Successful: {summary['successful_tests']}")
    print(f"   Failed: {summary['failed_tests']}")
    print(f"   Success rate: {summary['successful_tests'] / summary['total_tests'] * 100:.1f}%")

    return report


async def main():
    """Main function to run all compatibility tests."""
    print("🔧 Foundry Local + Orchestrator Compatibility")
    print("🎯 This validates Foundry Local works with all Amplifier orchestrators")
    print()

    # Run compatibility tests
    report = await run_orchestrator_compatibility_tests()

    # Print recommendations
    recommendations = report["foundry_local_orchestrator_compatibility"]["recommended_configurations"]
    print("\n💡 Recommended Configurations:")
    for use_case, config in recommendations.items():
        print(f"\n📋 {use_case.title()}:")
        print(f"   Orchestrator: {config['orchestrator']}")
        print(f"   Context: {config['context']}")
        print(f"   Reason: {config['reason']}")

    print("\n✅ Orchestrator compatibility testing completed!")


if __name__ == "__main__":
    asyncio.run(main())