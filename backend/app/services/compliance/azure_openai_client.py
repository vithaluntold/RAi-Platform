"""
Azure OpenAI Client — multi-endpoint round-robin with retry and fallback.

Features:
  - Round-robin across primary endpoints (distributes rate limits)
  - Automatic fallback to secondary pool on 429 / 5xx
  - Configurable temperature, max_tokens, response parsing
  - Works with both env-var config AND agent backend_config JSON
"""
import logging
import time
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

import openai

logger = logging.getLogger(__name__)


@dataclass
class EndpointConfig:
    """Single Azure OpenAI endpoint"""
    endpoint_url: str
    api_key: str
    deployment_name: str
    api_version: str = "2024-10-21"


@dataclass
class AzureOpenAIClientConfig:
    """Full client config with primary + fallback pools"""
    primary_endpoints: List[EndpointConfig] = field(default_factory=list)
    fallback_endpoints: List[EndpointConfig] = field(default_factory=list)
    temperature: float = 0.0
    max_tokens: int = 16384
    max_retries: int = 3
    retry_delay: float = 2.0


class AzureOpenAIClient:
    """
    Multi-endpoint Azure OpenAI client with round-robin and fallback.

    Usage:
        client = AzureOpenAIClient.from_settings(settings)
        # or
        client = AzureOpenAIClient.from_agent_config(backend_config)

        result = await client.chat_completion(
            system_prompt="You are a compliance analyst.",
            user_prompt="Analyze this...",
        )
    """

    def __init__(self, config: AzureOpenAIClientConfig):
        self._config = config
        self._primary_index = 0
        self._fallback_index = 0
        self._primary_clients: List[openai.AzureOpenAI] = []
        self._fallback_clients: List[openai.AzureOpenAI] = []

        for ep in config.primary_endpoints:
            self._primary_clients.append(
                openai.AzureOpenAI(
                    azure_endpoint=ep.endpoint_url,
                    api_key=ep.api_key,
                    api_version=ep.api_version,
                )
            )

        for ep in config.fallback_endpoints:
            self._fallback_clients.append(
                openai.AzureOpenAI(
                    azure_endpoint=ep.endpoint_url,
                    api_key=ep.api_key,
                    api_version=ep.api_version,
                )
            )

    @classmethod
    def from_settings(cls, settings) -> "AzureOpenAIClient":
        """Build client from app Settings (env vars)"""
        config = AzureOpenAIClientConfig()

        # Parse comma-separated primary endpoints
        endpoints = [e.strip() for e in settings.AZURE_OPENAI_ENDPOINTS.split(",") if e.strip()]
        api_keys = [k.strip() for k in settings.AZURE_OPENAI_API_KEYS.split(",") if k.strip()]

        for i, ep in enumerate(endpoints):
            key = api_keys[i] if i < len(api_keys) else api_keys[0] if api_keys else ""
            config.primary_endpoints.append(
                EndpointConfig(
                    endpoint_url=ep,
                    api_key=key,
                    deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                )
            )

        # Parse fallback endpoints
        fallback_endpoints = [e.strip() for e in settings.AZURE_OPENAI_FALLBACK_ENDPOINTS.split(",") if e.strip()]
        fallback_keys = [k.strip() for k in settings.AZURE_OPENAI_FALLBACK_API_KEYS.split(",") if k.strip()]

        for i, ep in enumerate(fallback_endpoints):
            key = fallback_keys[i] if i < len(fallback_keys) else fallback_keys[0] if fallback_keys else ""
            config.fallback_endpoints.append(
                EndpointConfig(
                    endpoint_url=ep,
                    api_key=key,
                    deployment_name=settings.AZURE_OPENAI_FALLBACK_DEPLOYMENT,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                )
            )

        return cls(config)

    @classmethod
    def from_agent_config(cls, backend_config: dict) -> "AzureOpenAIClient":
        """Build client from Agent.backend_config JSON (ProviderConfigAzure shape)"""
        config = AzureOpenAIClientConfig(
            temperature=backend_config.get("temperature", 0.0),
            max_tokens=backend_config.get("max_tokens", 16384),
        )

        for ep in backend_config.get("llm_endpoints", []):
            config.primary_endpoints.append(
                EndpointConfig(
                    endpoint_url=ep["endpoint_url"],
                    api_key=ep["api_key"],
                    deployment_name=ep["deployment_name"],
                    api_version=ep.get("api_version", "2024-10-21"),
                )
            )

        for ep in backend_config.get("fallback_endpoints", []):
            config.fallback_endpoints.append(
                EndpointConfig(
                    endpoint_url=ep["endpoint_url"],
                    api_key=ep["api_key"],
                    deployment_name=ep["deployment_name"],
                    api_version=ep.get("api_version", "2024-10-21"),
                )
            )

        return cls(config)

    def _next_primary(self) -> tuple:
        """Get next primary client + deployment (round-robin)"""
        if not self._primary_clients:
            return None, None
        idx = self._primary_index % len(self._primary_clients)
        self._primary_index += 1
        return self._primary_clients[idx], self._config.primary_endpoints[idx].deployment_name

    def _next_fallback(self) -> tuple:
        """Get next fallback client + deployment (round-robin)"""
        if not self._fallback_clients:
            return None, None
        idx = self._fallback_index % len(self._fallback_clients)
        self._fallback_index += 1
        return self._fallback_clients[idx], self._config.fallback_endpoints[idx].deployment_name

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request with automatic retry + fallback.

        Returns dict with:
          - content: str (the response text)
          - model: str
          - usage: dict (prompt_tokens, completion_tokens, total_tokens)
          - provider: str ("primary" or "fallback")
        """
        temp = temperature if temperature is not None else self._config.temperature
        max_tok = max_tokens if max_tokens is not None else self._config.max_tokens

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Guard: no endpoints configured
        if not self._primary_clients and not self._fallback_clients:
            raise RuntimeError(
                "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINTS and "
                "AZURE_OPENAI_API_KEYS environment variables, or configure "
                "llm_endpoints in the agent's backend_config."
            )

        # Try primary endpoints
        last_error = None
        for attempt in range(self._config.max_retries):
            client, deployment = self._next_primary()
            if not client:
                break
            try:
                kwargs = {
                    "model": deployment,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": max_tok,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = client.chat.completions.create(**kwargs)
                return {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    "provider": "primary",
                }
            except openai.RateLimitError as e:
                last_error = e
                logger.warning("Primary endpoint rate-limited (attempt %d/%d), trying next",
                               attempt + 1, self._config.max_retries)
                time.sleep(self._config.retry_delay * (attempt + 1))
            except openai.APIError as e:
                last_error = e
                logger.warning("Primary endpoint API error (attempt %d/%d): %s",
                               attempt + 1, self._config.max_retries, str(e))
                time.sleep(self._config.retry_delay)

        # Try fallback endpoints
        for attempt in range(self._config.max_retries):
            client, deployment = self._next_fallback()
            if not client:
                break
            try:
                kwargs = {
                    "model": deployment,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": max_tok,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = client.chat.completions.create(**kwargs)
                logger.info("Fallback endpoint succeeded on attempt %d", attempt + 1)
                return {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    "provider": "fallback",
                }
            except openai.RateLimitError as e:
                last_error = e
                logger.warning("Fallback endpoint rate-limited (attempt %d/%d)",
                               attempt + 1, self._config.max_retries)
                time.sleep(self._config.retry_delay * (attempt + 1))
            except openai.APIError as e:
                last_error = e
                logger.warning("Fallback endpoint API error: %s", str(e))
                time.sleep(self._config.retry_delay)

        raise RuntimeError(
            f"All Azure OpenAI endpoints exhausted after retries. Last error: {last_error}"
        )

    def chat_completion_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Chat completion expecting JSON output — auto-parses response"""
        result = self.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            result["parsed"] = json.loads(result["content"])
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, returning raw content")
            result["parsed"] = None
        return result
