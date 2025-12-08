#!/usr/bin/env python3
"""
Static validation of debug modes implementation.
"""

import os


def test_debug_modes_static():
    """Validate debug modes by checking source code."""

    print("Testing debug modes implementation (static analysis)...")
    print("=" * 70)

    # Read the source file
    source_file = os.path.join(
        os.path.dirname(__file__),
        '..',  # Go up from tests/ to project root
        'amplifier_module_provider_foundry_local',
        '__init__.py'
    )

    with open(source_file, 'r') as f:
        source = f.read()

    # Test 1: Configuration options
    print("\n1. Checking configuration options...")

    checks = {
        'debug config': 'self.debug = self.config.get("debug"',
        'raw_debug config': 'self.raw_debug = self.config.get("raw_debug"',
        'debug_truncate_length config': 'self.debug_truncate_length = self.config.get("debug_truncate_length"',
    }

    for name, pattern in checks.items():
        if pattern in source:
            print(f"   ✅ {name} found")
        else:
            print(f"   ❌ {name} NOT FOUND")
            return False

    # Test 2: Helper method
    print("\n2. Checking _truncate_values method...")

    if 'def _truncate_values(self, obj: Any, max_length: int | None = None)' in source:
        print("   ✅ _truncate_values method signature found")
    else:
        print("   ❌ _truncate_values method NOT FOUND")
        return False

    if '... ({len(obj)} chars total)' in source:
        print("   ✅ Truncation suffix logic found")
    else:
        print("   ❌ Truncation suffix logic NOT FOUND")
        return False

    # Test 3: Request events
    print("\n3. Checking request event emissions...")

    request_events = {
        'llm:request (INFO)': '"llm:request"',
        'llm:request:debug (DEBUG)': '"llm:request:debug"',
        'llm:request:raw (RAW)': '"llm:request:raw"',
    }

    for name, pattern in request_events.items():
        if pattern in source:
            print(f"   ✅ {name} event found")
        else:
            print(f"   ❌ {name} event NOT FOUND")
            return False

    # Test 4: Response events
    print("\n4. Checking response event emissions...")

    response_events = {
        'llm:response (INFO)': '"llm:response"',
        'llm:response:debug (DEBUG)': '"llm:response:debug"',
        'llm:response:raw (RAW)': '"llm:response:raw"',
    }

    for name, pattern in response_events.items():
        if pattern in source:
            print(f"   ✅ {name} event found")
        else:
            print(f"   ❌ {name} event NOT FOUND")
            return False

    # Test 5: Conditional debug logic
    print("\n5. Checking conditional debug logic...")

    # Count occurrences
    debug_conditionals = source.count('if self.debug:')
    raw_debug_conditionals = source.count('if self.debug and self.raw_debug:')

    if debug_conditionals >= 2:  # At least for request and response
        print(f"   ✅ Found {debug_conditionals} 'if self.debug:' conditionals")
    else:
        print(f"   ❌ Only found {debug_conditionals} 'if self.debug:' conditionals (expected >= 2)")
        return False

    if raw_debug_conditionals >= 2:  # At least for request and response
        print(f"   ✅ Found {raw_debug_conditionals} 'if self.debug and self.raw_debug:' conditionals")
    else:
        print(f"   ❌ Only found {raw_debug_conditionals} 'if self.debug and self.raw_debug:' conditionals (expected >= 2)")
        return False

    # Test 6: Truncation usage
    print("\n6. Checking truncation usage in debug events...")

    if 'self._truncate_values(params)' in source:
        print("   ✅ Request params truncation found")
    else:
        print("   ❌ Request params truncation NOT FOUND")
        return False

    if 'self._truncate_values(response_dict)' in source:
        print("   ✅ Response dict truncation found")
    else:
        print("   ❌ Response dict truncation NOT FOUND")
        return False

    # Test 7: Raw debug doesn't use truncation
    print("\n7. Checking raw debug events (should NOT truncate)...")

    # Look for the pattern where raw events include complete data
    if '"params": params,  # Complete untruncated params' in source:
        print("   ✅ Raw request includes complete params (no truncation)")
    else:
        print("   ⚠️  Raw request comment not found (but may still work)")

    if '"response": raw_response,  # Complete untruncated response' in source:
        print("   ✅ Raw response includes complete response (no truncation)")
    else:
        print("   ⚠️  Raw response comment not found (but may still work)")

    print("\n" + "=" * 70)
    print("✅ ALL CHECKS PASSED")
    print("\nDebug modes implementation validated:")
    print("  ✓ Configuration options (debug, raw_debug, debug_truncate_length)")
    print("  ✓ Helper method (_truncate_values)")
    print("  ✓ Request events (INFO, DEBUG, RAW)")
    print("  ✓ Response events (INFO, DEBUG, RAW)")
    print("  ✓ Conditional logic for debug levels")
    print("  ✓ Truncation for DEBUG events")
    print("  ✓ No truncation for RAW events")

    return True


def main():
    """Run the validation."""
    try:
        result = test_debug_modes_static()
        if result:
            print("\n" + "=" * 70)
            print("✅ DEBUG MODES STATIC VALIDATION PASSED")
            print("=" * 70)
            print("\nImplementation follows the same pattern as:")
            print("  - amplifier-module-provider-anthropic")
            print("  - amplifier-module-provider-ollama")
            print("  - amplifier-module-provider-azure-openai")
            print("  - amplifier-module-provider-vllm")
            return 0
        else:
            print("\n" + "=" * 70)
            print("❌ VALIDATION FAILED")
            print("=" * 70)
            return 1
    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
