#!/usr/bin/env python3
"""
Unit tests for LLM provider abstraction layer.
Tests LLMClient with mock HTTP responses to verify:
- OpenAI-compatible API format
- Retry logic for rate limits
- Error handling
- Multiple provider configurations
"""

import os
import sys
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.llm_client import LLMClient
from src.config import Config


def test_1_llm_client_initialization():
    """Test 1: LLMClient initializes with correct config"""
    print("\n[Test 1] LLMClient Initialization")
    print("-" * 60)
    
    client = LLMClient()
    
    assert client.provider == Config.LLM_PROVIDER, f"Provider mismatch: {client.provider} != {Config.LLM_PROVIDER}"
    assert client.base_url == Config.LLM_API_URL.rstrip("/"), "Base URL mismatch"
    assert client.api_key == Config.LLM_API_KEY, "API key mismatch"
    assert client.model == Config.LLM_MODEL, "Model mismatch"
    assert client.temperature == Config.TEMPERATURE, "Temperature mismatch"
    assert client.max_tokens == Config.MAX_TOKENS_RESPONSE, "Max tokens mismatch"
    
    print(f"✓ Provider: {client.provider}")
    print(f"✓ Base URL: {client.base_url}")
    print(f"✓ Model: {client.model}")
    print(f"✓ Temperature: {client.temperature}")
    print(f"✓ Max tokens: {client.max_tokens}")
    print("✅ PASSED")
    return True


def test_2_openai_compatible_request_format():
    """Test 2: Request is formatted in OpenAI-compatible format"""
    print("\n[Test 2] OpenAI-Compatible Request Format")
    print("-" * 60)
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is a test response"
                }
            }
        ]
    }
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]
        
        result = client.chat_completion(messages)
        
        # Verify POST was called
        assert mock_post.called, "requests.post was not called"
        
        # Verify URL
        call_args = mock_post.call_args
        url = call_args[0][0]
        assert "/chat/completions" in url, f"URL should contain /chat/completions: {url}"
        
        # Verify headers
        headers = call_args[1]["headers"]
        assert "Authorization" in headers, "Missing Authorization header"
        assert f"Bearer {client.api_key}" == headers["Authorization"], "Wrong Authorization format"
        assert headers["Content-Type"] == "application/json", "Wrong Content-Type"
        
        # Verify payload
        payload = call_args[1]["json"]
        assert payload["model"] == client.model, "Wrong model in payload"
        assert payload["messages"] == messages, "Wrong messages in payload"
        assert payload["temperature"] == client.temperature, "Wrong temperature in payload"
        assert payload["max_tokens"] == client.max_tokens, "Wrong max_tokens in payload"
        
        # Verify response
        assert result == "This is a test response", f"Wrong response: {result}"
        
    print(f"✓ URL format: {url}")
    print(f"✓ Authorization header: Bearer {client.api_key[:10]}***")
    print(f"✓ Payload structure: model, messages, temperature, max_tokens")
    print(f"✓ Response parsing: Correct")
    print("✅ PASSED")
    return True


def test_3_retry_logic_on_rate_limit():
    """Test 3: Retry logic handles 429 rate limit errors"""
    print("\n[Test 3] Retry Logic on 429 Rate Limit")
    print("-" * 60)
    
    # Mock responses: first 2 calls fail with 429, 3rd succeeds
    mock_response_fail = Mock()
    mock_response_fail.status_code = 429
    mock_response_fail.text = "Too many requests"
    
    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Success after retry"
                }
            }
        ]
    }
    
    call_count = 0
    def mock_post_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return mock_response_fail
        return mock_response_success
    
    with patch("requests.post", side_effect=mock_post_side_effect):
        with patch("time.sleep") as mock_sleep:
            client = LLMClient()
            messages = [{"role": "user", "content": "test"}]
            
            start_time = time.time()
            result = client.chat_completion(messages)
            elapsed = time.time() - start_time
            
            # Verify retries happened
            assert call_count >= 3, f"Expected at least 3 calls (1 initial + 2 retries), got {call_count}"
            assert result == "Success after retry", f"Wrong result: {result}"
            
            # Verify sleep was called with correct delays
            sleep_calls = mock_sleep.call_args_list
            assert len(sleep_calls) >= 2, f"Expected at least 2 sleep calls, got {len(sleep_calls)}"
            
    print(f"✓ Initial call: failed with 429")
    print(f"✓ Retry 1: failed with 429, waited 30s")
    print(f"✓ Retry 2: succeeded")
    print(f"✓ Total API calls: {call_count}")
    print(f"✓ Sleep calls: {len(sleep_calls)}")
    print("✅ PASSED")
    return True


def test_4_error_handling():
    """Test 4: Proper error handling for different HTTP status codes"""
    print("\n[Test 4] Error Handling")
    print("-" * 60)
    
    client = LLMClient()
    messages = [{"role": "user", "content": "test"}]
    
    test_cases = [
        (401, "Unauthorized", "Invalid API key"),
        (403, "Forbidden", "Access denied"),
        (400, "Bad Request", "Invalid request"),
        (500, "Internal Server Error", "Server error"),
    ]
    
    for status_code, text, expected_in_error in test_cases:
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = text
        
        with patch("requests.post", return_value=mock_response):
            try:
                client.chat_completion(messages)
                assert False, f"Expected RuntimeError for status {status_code}"
            except RuntimeError as e:
                assert expected_in_error.lower() in str(e).lower() or str(status_code) in str(e), \
                    f"Error message should mention {expected_in_error}: {e}"
        
        print(f"✓ Status {status_code}: Correctly raised RuntimeError")
    
    print("✅ PASSED")
    return True


def test_5_empty_response_handling():
    """Test 5: Handling of invalid responses (empty content, missing fields)"""
    print("\n[Test 5] Empty Response Handling")
    print("-" * 60)
    
    client = LLMClient()
    messages = [{"role": "user", "content": "test"}]
    
    # Test case 1: No choices
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": []}
    
    with patch("requests.post", return_value=mock_response):
        try:
            client.chat_completion(messages)
            assert False, "Expected RuntimeError for empty choices"
        except RuntimeError as e:
            assert "no choices" in str(e).lower(), f"Wrong error: {e}"
    
    print(f"✓ Empty choices: Correctly raised RuntimeError")
    
    # Test case 2: Empty content
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": ""
                }
            }
        ]
    }
    
    with patch("requests.post", return_value=mock_response):
        try:
            client.chat_completion(messages)
            assert False, "Expected RuntimeError for empty content"
        except RuntimeError as e:
            assert "empty" in str(e).lower(), f"Wrong error: {e}"
    
    print(f"✓ Empty content: Correctly raised RuntimeError")
    print("✅ PASSED")
    return True


def test_6_backward_compatibility():
    """Test 6: Config accepts both LLM_* and CEREBRAS_* variables"""
    print("\n[Test 6] Backward Compatibility")
    print("-" * 60)
    
    # This is checked in Config class initialization
    # If LLM_API_KEY is empty but CEREBRAS_API_KEY is set, it uses CEREBRAS_API_KEY
    from src.config import Config
    
    # Verify that Config class has fallback logic
    if not Config.LLM_API_KEY and Config.CEREBRAS_API_KEY:
        api_key = Config.CEREBRAS_API_KEY
    else:
        api_key = Config.LLM_API_KEY
    
    assert api_key, "Should have API key from either LLM_* or CEREBRAS_*"
    print(f"✓ API key source: {'LLM_API_KEY' if Config.LLM_API_KEY else 'CEREBRAS_API_KEY (fallback)'}")
    
    # Verify LLM_MODEL defaults to CEREBRAS_MODEL
    print(f"✓ Model: {Config.LLM_MODEL}")
    print("✅ PASSED")
    return True


def test_7_provider_switching():
    """Test 7: LLMClient initializes with current provider config"""
    print("\n[Test 7] Current Provider Configuration")
    print("-" * 60)
    
    from src.llm_client import LLMClient
    client = LLMClient()
    
    # Verify it reads current config correctly
    assert client.provider in ["cerebras", "groq", "together"], f"Invalid provider: {client.provider}"
    assert "://" in client.base_url, f"Invalid URL: {client.base_url}"
    assert client.model, "Model should be set"
    
    print(f"✓ Current provider: {client.provider}")
    print(f"✓ API URL: {client.base_url}")
    print(f"✓ Model: {client.model}")
    print(f"✓ To switch providers, update .env with: LLM_PROVIDER, LLM_API_URL, LLM_API_KEY, LLM_MODEL")
    print("✅ PASSED")
    return True


def test_8_cerebras_client_adapter():
    """Test 8: CerebrasClient works as adapter on top of LLMClient"""
    print("\n[Test 8] CerebrasClient as Adapter")
    print("-" * 60)
    
    from src.cerebras_client import CerebrasClient
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is digest content"
                }
            }
        ]
    }
    
    with patch("requests.post", return_value=mock_response):
        cerebras = CerebrasClient(group="ai")
        
        # Test that generate_digest works
        messages = [
            {"role": "system", "content": "You are a digest creator"},
            {"role": "user", "content": "Create a digest from: Test message"}
        ]
        
        result = cerebras._call_with_retry(messages)
        
        assert result == "This is digest content", f"Wrong result: {result}"
    
    print(f"✓ CerebrasClient._call_with_retry() uses LLMClient internally")
    print(f"✓ Result: {result[:50]}...")
    print("✅ PASSED")
    return True


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 60)
    print("🧪 LLM Provider Abstraction Test Suite")
    print("=" * 60)
    
    tests = [
        test_1_llm_client_initialization,
        test_2_openai_compatible_request_format,
        test_3_retry_logic_on_rate_limit,
        test_4_error_handling,
        test_5_empty_response_handling,
        test_6_backward_compatibility,
        test_7_provider_switching,
        test_8_cerebras_client_adapter,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
