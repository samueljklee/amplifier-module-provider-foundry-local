#!/usr/bin/env python3
"""
Amplifier-style interface using Foundry Local directly
This bypasses the provider validation issues in amplifier@next
"""

import asyncio
import sys
from openai import AsyncOpenAI

class AmplifierFoundryInterface:
    """Amplifier-style interface for Foundry Local"""

    def __init__(self, endpoint="http://127.0.0.1:65320/v1", model="qwen2.5-7b-instruct-generic-gpu:4"):
        self.client = AsyncOpenAI(
            base_url=endpoint,
            api_key="dummy-key"  # Foundry Local doesn't need real API key
        )
        self.model = model
        self.messages = []

    async def chat(self, user_message, system_message=None):
        """Send a chat message and get response"""

        # Build message history
        messages = []

        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add conversation history
        messages.extend(self.messages)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        try:
            # Get completion from Foundry Local
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7,
                stream=False
            )

            assistant_message = response.choices[0].message.content

            # Add to conversation history
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            return f"Error: {e}"

    async def close(self):
        """Close the client"""
        await self.client.close()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python amplifier_foundry_workaround.py \"your message\"")
        print("Example: python amplifier_foundry_workaround.py \"what model are you using?\"")
        sys.exit(1)

    user_message = " ".join(sys.argv[1:])

    interface = AmplifierFoundryInterface()

    try:
        system_message = """You are an AI assistant powered by Amplifier using Microsoft Foundry Local for privacy-first AI inference.

Be helpful, accurate, and efficient in your responses. Your responses are processed locally using Foundry Local, ensuring data privacy and security."""

        response = await interface.chat(user_message, system_message)
        print(response)

    finally:
        await interface.close()

if __name__ == "__main__":
    asyncio.run(main())