"""OpenAI-compatible LLM client for any provider."""

import time
import requests
import json
from typing import List, Dict, Any, Optional

from .config import Config

_RETRY_DELAYS = [30, 60, 120]  # seconds to wait between retries on 429


class LLMClient:
    """Client for OpenAI-compatible LLM APIs (Cerebras, Groq, Together, etc.)."""

    def __init__(self):
        """Initialize LLM client with provider-agnostic settings."""
        self.provider = Config.LLM_PROVIDER
        self.base_url = Config.LLM_API_URL.rstrip("/")  # Remove trailing slash
        self.api_key = Config.LLM_API_KEY
        self.model = Config.LLM_MODEL
        self.temperature = Config.TEMPERATURE
        self.max_tokens = Config.MAX_TOKENS_RESPONSE
        
        print(f"🤖 LLMClient initialized: provider={self.provider}, model={self.model}, url={self.base_url}")

    def chat_completion(
        self, messages: List[Dict[str, str]]
    ) -> str:
        """
        Call OpenAI-compatible chat completion API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            Generated response text
        """
        return self._call_with_retry(messages)

    def _call_with_retry(self, messages: List[Dict[str, str]]) -> str:
        """
        Call LLM API with retry logic for rate limits (429).

        Args:
            messages: List of message dicts

        Returns:
            Response text

        Raises:
            RuntimeError: If all retries exhausted or non-recoverable error
        """
        for attempt, delay in enumerate(_RETRY_DELAYS, 1):
            try:
                response = self._make_request(messages)
                return response

            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "429" in error_str or "rate" in error_str.lower() or "too many" in error_str.lower():
                    print(f"⚠️  Rate limit hit (attempt {attempt}/{len(_RETRY_DELAYS)}). Waiting {delay}s...")
                    time.sleep(delay)
                else:
                    # Non-rate-limit error: fail immediately
                    raise RuntimeError(f"LLM API error ({self.provider}): {e}")

        # Final attempt after all retries
        try:
            response = self._make_request(messages)
            return response
        except Exception as e:
            raise RuntimeError(
                f"LLM API error ({self.provider}) after {len(_RETRY_DELAYS)} retries: {e}"
            )

    def _make_request(self, messages: List[Dict[str, str]]) -> str:
        """
        Make HTTP request to OpenAI-compatible API endpoint.

        Args:
            messages: List of message dicts

        Returns:
            Response text

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            # Check HTTP status
            if response.status_code == 429:
                raise Exception(f"Rate limit (429): {response.text}")
            elif response.status_code == 401:
                raise Exception(f"Unauthorized (401): Invalid API key or credentials")
            elif response.status_code == 403:
                raise Exception(f"Forbidden (403): Access denied")
            elif response.status_code >= 500:
                raise Exception(f"Server error ({response.status_code}): {response.text}")
            elif response.status_code >= 400:
                raise Exception(f"Client error ({response.status_code}): {response.text}")

            # Parse response
            result = response.json()

            # Check for API-level errors
            if not result.get("choices") or len(result["choices"]) == 0:
                raise Exception(f"Invalid response: no choices returned. Response: {result}")

            content = result["choices"][0].get("message", {}).get("content", "").strip()
            if not content:
                raise Exception(f"Empty response content. Full response: {result}")

            return content

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
