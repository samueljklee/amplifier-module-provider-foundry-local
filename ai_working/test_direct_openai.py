#!/usr/bin/env python3
"""
Direct test of Foundry Local using OpenAI client
"""

import asyncio
from openai import AsyncOpenAI

async def test_foundry_local_direct():
    """Test Foundry Local directly with OpenAI client"""

    # Initialize OpenAI client for Foundry Local
    client = AsyncOpenAI(
        base_url="http://127.0.0.1:65320/v1",
        api_key="dummy-key"  # Foundry Local doesn't need real API key
    )

    try:
        print("Testing Foundry Local connection...")

        # List available models
        models_response = await client.models.list()
        print("Available models:")
        for model in models_response.data:
            print(f"  - {model.id}")

        # Test a simple chat completion
        print("\nTesting chat completion...")
        chat_response = await client.chat.completions.create(
            model="qwen2.5-7b-instruct-generic-gpu:4",
            messages=[
                {"role": "user", "content": "What model are you using?"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        print("Response:", chat_response.choices[0].message.content)

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()

if __name__ == "__main__":
    result = asyncio.run(test_foundry_local_direct())
    if result:
        print("\n✅ Foundry Local is working!")
    else:
        print("\n❌ Foundry Local test failed")