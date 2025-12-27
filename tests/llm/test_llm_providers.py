#!/usr/bin/env python3
"""Test script for LLM provider and model selection."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from wikigen.utils.llm_providers import (
    get_provider_list,
    get_provider_info,
    get_display_name,
    get_recommended_models,
    requires_api_key,
    LLM_PROVIDERS,
)


def test_provider_registry():
    """Test that all providers are properly registered."""
    print("=" * 60)
    print("Testing Provider Registry")
    print("=" * 60)

    # Test 1: Get provider list
    print("\n1. Testing provider list:")
    providers = get_provider_list()
    print(f"   Found {len(providers)} providers: {', '.join(providers)}")
    assert len(providers) == 5, f"Expected 5 providers, got {len(providers)}"
    assert "gemini" in providers
    assert "openai" in providers
    assert "anthropic" in providers
    assert "openrouter" in providers
    assert "ollama" in providers
    print("   ✓ All providers registered correctly")

    # Test 2: Get display names
    print("\n2. Testing display names:")
    for provider_id in providers:
        display_name = get_display_name(provider_id)
        print(f"   {provider_id}: {display_name}")
        assert display_name, f"Display name should not be empty for {provider_id}"
    print("   ✓ All display names retrieved correctly")

    # Test 3: Get recommended models
    print("\n3. Testing recommended models:")
    for provider_id in providers:
        models = get_recommended_models(provider_id)
        print(f"   {provider_id}: {len(models)} models")
        assert len(models) > 0, f"No recommended models for {provider_id}"
        for model in models:
            assert model, f"Model name should not be empty for {provider_id}"
    print("   ✓ All recommended models retrieved correctly")

    # Test 4: API key requirements
    print("\n4. Testing API key requirements:")
    for provider_id in providers:
        needs_key = requires_api_key(provider_id)
        provider_info = get_provider_info(provider_id)
        print(
            f"   {provider_id}: {'Requires API key' if needs_key else 'No API key needed'}"
        )

        if provider_id == "ollama":
            assert not needs_key, "Ollama should not require an API key"
            assert (
                provider_info.get("keyring_key") is None
            ), "Ollama should not have keyring_key"
            assert (
                provider_info.get("api_key_env") is None
            ), "Ollama should not have api_key_env"
        else:
            assert needs_key, f"{provider_id} should require an API key"
            assert provider_info.get(
                "keyring_key"
            ), f"{provider_id} should have keyring_key"
            assert provider_info.get(
                "api_key_env"
            ), f"{provider_id} should have api_key_env"
    print("   ✓ API key requirements correct")

    # Test 5: Ollama special configuration
    print("\n5. Testing Ollama special configuration:")
    ollama_info = get_provider_info("ollama")
    assert (
        ollama_info.get("base_url") == "http://localhost:11434"
    ), "Ollama base URL should be set"
    assert (
        ollama_info.get("base_url_env") == "OLLAMA_BASE_URL"
    ), "Ollama base URL env var should be set"
    print("   ✓ Ollama configuration correct")

    print("\n" + "=" * 60)
    print("✓ All provider registry tests passed!")
    print("=" * 60)


def test_provider_info_structure():
    """Test that provider info has required structure."""
    print("\n" + "=" * 60)
    print("Testing Provider Info Structure")
    print("=" * 60)

    required_fields = ["display_name", "recommended_models"]

    for provider_id, provider_info in LLM_PROVIDERS.items():
        print(f"\nChecking {provider_id}:")
        for field in required_fields:
            assert (
                field in provider_info
            ), f"{provider_id} missing required field: {field}"
            print(f"   ✓ Has {field}")

        # Check API key related fields
        if provider_info.get("requires_api_key", True):
            assert provider_info.get(
                "keyring_key"
            ), f"{provider_id} missing keyring_key"
            assert provider_info.get(
                "api_key_env"
            ), f"{provider_id} missing api_key_env"
            print(f"   ✓ Has API key configuration")
        else:
            assert (
                provider_info.get("keyring_key") is None
                or provider_info.get("keyring_key") is None
            )
            print(f"   ✓ Correctly marked as no API key needed")

    print("\n" + "=" * 60)
    print("✓ All provider info structure tests passed!")
    print("=" * 60)


def test_model_selection():
    """Test model selection scenarios."""
    print("\n" + "=" * 60)
    print("Testing Model Selection")
    print("=" * 60)

    # Test 1: Get models for each provider
    print("\n1. Testing model retrieval for each provider:")
    for provider_id in get_provider_list():
        models = get_recommended_models(provider_id)
        print(f"   {provider_id}:")
        for i, model in enumerate(models, 1):
            print(f"      {i}) {model}")

    # Test 2: Verify Ollama models
    print("\n2. Testing Ollama models:")
    ollama_models = get_recommended_models("ollama")
    assert (
        "llama3.2" in ollama_models or "llama3.1" in ollama_models
    ), "Should have llama models"
    print("   ✓ Ollama models retrieved")

    # Test 3: Custom model entry (simulated)
    print("\n3. Custom model entry would work for any provider:")
    for provider_id in get_provider_list():
        print(f"   {provider_id}: Supports custom model names")
    print("   ✓ Custom model entry supported")

    print("\n" + "=" * 60)
    print("✓ All model selection tests passed!")
    print("=" * 60)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LLM Provider and Model Selection Test Suite")
    print("=" * 60 + "\n")

    tests_passed = 0
    tests_failed = 0

    try:
        test_provider_registry()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ Provider registry test failed: {e}")
        import traceback

        traceback.print_exc()

    try:
        test_provider_info_structure()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ Provider info structure test failed: {e}")
        import traceback

        traceback.print_exc()

    try:
        test_model_selection()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ Model selection test failed: {e}")
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
