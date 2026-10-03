"""Lightweight Claude LLM provider interface using official anthropic SDK."""

import os
import json
from typing import Dict, Any, Optional
from src.utils.logger import logger


class ModelNotFoundError(Exception):
    """Raised when Anthropic returns 404 / NotFoundError for a model ID (config error)."""
    pass


class LLMExecutionError(Exception):
    """Raised when an LLM call fails due to API error, validation error, or unexpected response."""
    pass


class AnthropicClient:
    """Wrapper around the official anthropic Python client for structured tool calls."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None
        if self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
                self._client = None

    def is_available(self) -> bool:
        """Returns True if the Anthropic client is initialized with an API key."""
        return self._client is not None

    def call_structured(
        self,
        model: str,
        system: str,
        user_prompt: str,
        tool_name: str,
        tool_schema: Dict[str, Any],
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Makes a forced structured tool call to Claude.

        Raises:
            ModelNotFoundError: if model ID returns 404 / NotFoundError (config error).
            LLMExecutionError: on any other API error, timeout, or schema failure.
        """
        if not self.is_available():
            raise LLMExecutionError("Anthropic client is not available (missing ANTHROPIC_API_KEY).")

        import anthropic

        try:
            # Force tool choice to guarantee JSON payload adhering to tool_schema
            response = self._client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[
                    {
                        "name": tool_name,
                        "description": f"Output schema for {tool_name}",
                        "input_schema": tool_schema,
                    }
                ],
                tool_choice={"type": "tool", "name": tool_name},
            )

            # Extract tool use content block
            for block in response.content:
                if block.type == "tool_use" and block.name == tool_name:
                    if isinstance(block.input, dict):
                        return block.input
                    elif isinstance(block.input, str):
                        return json.loads(block.input)

            raise LLMExecutionError(f"No tool_use block named '{tool_name}' returned by model.")

        except anthropic.NotFoundError as e:
            # 404 is a configuration error: raise immediately, do not fall back
            logger.error(f"Anthropic model '{model}' not found (404): {e}. This is a config error.")
            raise ModelNotFoundError(f"Model ID '{model}' not found (404). Check config/research_gaps.yaml.") from e

        except Exception as e:
            # Check if exception represents 404
            status_code = getattr(e, "status_code", None)
            if status_code == 404:
                raise ModelNotFoundError(f"Model ID '{model}' not found (404). Check config/research_gaps.yaml.") from e
            logger.warning(f"Anthropic structured call failed for model '{model}': {e}")
            raise LLMExecutionError(f"Anthropic call failed: {e}") from e
