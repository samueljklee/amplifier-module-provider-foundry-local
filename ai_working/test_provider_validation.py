#!/usr/bin/env python3
"""Test Foundry Local provider to capture RuntimeWarnings."""

import asyncio
import sys
import warnings
import logging

logging.basicConfig(level=logging.INFO)

# Enable RuntimeWarnings as errors to catch them
warnings.simplefilter('error', category=RuntimeWarning)

async def test_provider():
    """Test provider initialization and basic operations."""
    print("=" * 70)
    print("🧪 Foundry Local Provider Validation Test")
    print("=" * 70)
    
    try:
        print("\n1️⃣  Importing provider...")
        from amplifier_module_provider_foundry_local import FoundryLocalProvider
        print("   ✓ Import successful")
        
        print("\n2️⃣  Initializing provider...")
        config = {"default_model": "qwen2.5-7b", "debug": True}
        provider = FoundryLocalProvider(config=config)
        print(f"   ✓ Provider: {provider.name}")
        print(f"   ✓ Manager: {provider.manager}")
        
        print("\n3️⃣  Testing get_info()...")
        info = provider.get_info()
        print(f"   ✓ ID: {info.id}")
        
        print("\n4️⃣  Testing list_models()...")
        models = await provider.list_models()
        print(f"   ✓ Found {len(models)} models")
        
        print("\n✅ ALL TESTS PASSED!")
        return True
        
    except RuntimeWarning as e:
        print(f"\n⚠️  RuntimeWarning caught: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_provider())
    sys.exit(0 if success else 1)
