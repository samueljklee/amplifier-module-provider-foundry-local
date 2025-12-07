#!/usr/bin/env python3
"""Direct test of Foundry Local provider to capture RuntimeWarnings."""

import asyncio
import sys
import warnings

# Enable all warnings including RuntimeWarnings
warnings.simplefilter('always', RuntimeWarning)

# Add to path
sys.path.insert(0, '/Users/samule/code/amplifier-dev/amplifier-module-provider-foundry-local')

async def test_provider():
    """Test the provider directly."""
    print("🧪 Testing Foundry Local Provider for RuntimeWarnings")
    print("=" * 60)
    
    try:
        # Import the provider
        from amplifier_module_provider_foundry_local import FoundryLocalProvider
        print("✓ Provider imported successfully")
        
        # Test initialization (this is where the RuntimeWarning likely occurs)
        print("\n📦 Initializing provider...")
        config = {
            "default_model": "qwen2.5-7b",
            "debug": True,
            "base_url": "http://127.0.0.1:65320/v1"
        }
        
        provider = FoundryLocalProvider(config=config)
        print(f"✓ Provider initialized")
        print(f"  - Name: {provider.name}")
        print(f"  - Default model: {provider.default_model}")
        print(f"  - Manager: {provider.manager}")
        
        # Test get_info
        print("\n📋 Testing get_info()...")
        info = provider.get_info()
        print(f"✓ Provider info retrieved: {info.id}")
        
        # Test list_models
        print("\n📝 Testing list_models()...")
        models = await provider.list_models()
        print(f"✓ Found {len(models)} models")
        
        print("\n✅ All tests passed - no RuntimeWarnings detected!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Watching for RuntimeWarnings about unawaited coroutines...\n")
    success = asyncio.run(test_provider())
    sys.exit(0 if success else 1)
