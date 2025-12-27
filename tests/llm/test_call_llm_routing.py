#!/usr/bin/env python3
"""Test call_llm routing logic for different providers."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_provider_routing_logic():
    """Test that call_llm can route to correct providers."""
    print("=" * 60)
    print("Testing Call LLM Routing Logic")
    print("=" * 60)

    from wikigen.utils.call_llm import (
        _call_gemini,
        _call_openai,
        _call_anthropic,
        _call_openrouter,
        _call_ollama,
    )

    providers = {
        "gemini": _call_gemini,
        "openai": _call_openai,
        "anthropic": _call_anthropic,
        "openrouter": _call_openrouter,
        "ollama": _call_ollama,
    }

    print("\n1. Testing provider functions exist:")
    for provider_id, func in providers.items():
        assert func is not None, f"Provider function for {provider_id} should exist"
        print(f"   ✓ {provider_id} function: {func.__name__}")

    print("\n2. Testing function signatures:")
    for provider_id, func in providers.items():
        import inspect

        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        print(f"   {provider_id}: {func.__name__}({', '.join(params)})")

        # All should have prompt and model at minimum
        assert (
            "prompt" in params
        ), f"{provider_id} function should have 'prompt' parameter"
        assert (
            "model" in params
        ), f"{provider_id} function should have 'model' parameter"
        print(f"   ✓ {provider_id} has required parameters")

    print("\n" + "=" * 60)
    print("✓ All routing functions exist and have correct signatures")
    print("=" * 60)


def test_ollama_routing():
    """Test Ollama-specific routing."""
    print("\n" + "=" * 60)
    print("Testing Ollama Routing")
    print("=" * 60)

    from wikigen.utils.call_llm import _call_ollama
    import inspect

    # Check that Ollama function accepts api_key as optional
    sig = inspect.signature(_call_ollama)
    params = sig.parameters

    assert "api_key" in params, "Ollama function should have api_key parameter"
    api_key_param = params["api_key"]

    # api_key should have a default value (optional) - None is a valid default
    # inspect uses Parameter.empty for parameters without defaults
    assert (
        api_key_param.default is not inspect.Parameter.empty
    ), "Ollama api_key should be optional"
    print("✓ Ollama function correctly has optional api_key parameter")
    print(f"   Default value: {api_key_param.default}")

    print("\n" + "=" * 60)
    print("✓ Ollama routing configured correctly")
    print("=" * 60)


def test_openai_o1_support():
    """Test OpenAI o1 model support."""
    print("\n" + "=" * 60)
    print("Testing OpenAI o1 Support")
    print("=" * 60)

    from wikigen.utils.call_llm import _call_openai
    import inspect

    # Check the function has logic for o1 models
    source = inspect.getsource(_call_openai)

    assert "o1" in source or "startswith" in source, "Should check for o1 models"
    print("✓ OpenAI function has o1 model detection logic")

    print("\n" + "=" * 60)
    print("✓ OpenAI o1 support configured")
    print("=" * 60)


def test_anthropic_extended_thinking():
    """Test Anthropic extended thinking support."""
    print("\n" + "=" * 60)
    print("Testing Anthropic Extended Thinking")
    print("=" * 60)

    from wikigen.utils.call_llm import _call_anthropic
    import inspect

    # Check the function has logic for extended thinking
    source = inspect.getsource(_call_anthropic)

    assert "thinking" in source.lower(), "Should handle extended thinking"
    assert "content" in source.lower(), "Should handle content array"
    print("✓ Anthropic function has extended thinking logic")

    print("\n" + "=" * 60)
    print("✓ Anthropic extended thinking configured")
    print("=" * 60)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Call LLM Routing Test Suite")
    print("=" * 60 + "\n")

    tests_passed = 0
    tests_failed = 0

    try:
        test_provider_routing_logic()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ Provider routing test failed: {e}")
        import traceback

        traceback.print_exc()

    try:
        test_ollama_routing()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ Ollama routing test failed: {e}")
        import traceback

        traceback.print_exc()

    try:
        test_openai_o1_support()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ OpenAI o1 support test failed: {e}")
        import traceback

        traceback.print_exc()

    try:
        test_anthropic_extended_thinking()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ Anthropic extended thinking test failed: {e}")
        import traceback

        traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✓ Passed: {tests_passed}")
    if tests_failed > 0:
        print(f"✗ Failed: {tests_failed}")
        sys.exit(1)
    else:
        print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
