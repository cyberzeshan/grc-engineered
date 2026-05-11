from __future__ import annotations

import os
from typing import Any

import anthropic

# Use claude-sonnet-4-6 (current Sonnet; design spec called for the Sonnet tier)
DEFAULT_MODEL = "claude-sonnet-4-6"


class BaseAgent:
    """Base class for all GRC agents.

    Wraps the Anthropic client with:
    - Prompt caching on the system prompt (5-min TTL)
    - Streaming support for long outputs
    - Typed exception handling
    - Tool use support
    """

    def __init__(
        self,
        system_prompt: str,
        tools: list[dict] | None = None,
        model: str = DEFAULT_MODEL,
    ) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.tools = tools or []
        # Cache the system prompt — stable across all runs of this agent type
        self._system = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def run(self, user_message: str, context: dict | None = None) -> str:
        content = user_message
        if context:
            content = f"Context:\n{_format_context(context)}\n\n{user_message}"

        messages = [{"role": "user", "content": content}]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "system": self._system,
            "messages": messages,
        }
        if self.tools:
            kwargs["tools"] = self.tools

        try:
            response = self.client.messages.create(**kwargs)
            return self._extract_text(response)
        except anthropic.BadRequestError as exc:
            return f"[Agent Error - BadRequest] {exc.message}"
        except anthropic.RateLimitError:
            return "[Agent Error] Rate limited — please retry in a moment."
        except anthropic.APIError as exc:
            return f"[Agent Error] {exc}"

    def run_streaming(self, user_message: str, context: dict | None = None) -> str:
        """Run with streaming; returns full text after stream completes."""
        content = user_message
        if context:
            content = f"Context:\n{_format_context(context)}\n\n{user_message}"

        messages = [{"role": "user", "content": content}]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 8192,
            "system": self._system,
            "messages": messages,
        }
        if self.tools:
            kwargs["tools"] = self.tools

        try:
            with self.client.messages.stream(**kwargs) as stream:
                return self._extract_text(stream.get_final_message())
        except anthropic.BadRequestError as exc:
            return f"[Agent Error - BadRequest] {exc.message}"
        except anthropic.RateLimitError:
            return "[Agent Error] Rate limited — please retry in a moment."
        except anthropic.APIError as exc:
            return f"[Agent Error] {exc}"

    def run_with_tools(self, user_message: str, context: dict | None = None, max_iterations: int = 10) -> str:
        """Agentic loop: runs until stop_reason == end_turn."""
        content = user_message
        if context:
            content = f"Context:\n{_format_context(context)}\n\n{user_message}"

        messages = [{"role": "user", "content": content}]

        try:
            for _ in range(max_iterations):
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self._system,
                    tools=self.tools,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    return self._extract_text(response)

                if response.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": response.content})
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._handle_tool_call(block.name, block.input)
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result,
                                }
                            )
                    messages.append({"role": "user", "content": tool_results})
                else:
                    return self._extract_text(response)

            return "[Agent Error] Maximum tool iterations reached without end_turn."
        except anthropic.BadRequestError as exc:
            return f"[Agent Error - BadRequest] {exc.message}"
        except anthropic.RateLimitError:
            return "[Agent Error] Rate limited — please retry in a moment."
        except anthropic.APIError as exc:
            return f"[Agent Error] {exc}"

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Override in subclasses to implement tool execution."""
        return f"Tool '{tool_name}' not implemented."

    def _extract_text(self, response) -> str:
        return "".join(
            block.text for block in response.content if block.type == "text"
        )


def _format_context(context: dict) -> str:
    lines = []
    for k, v in context.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)
