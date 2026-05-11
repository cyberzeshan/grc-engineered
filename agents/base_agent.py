from __future__ import annotations

from core.providers import LLMProvider, create_provider

DEFAULT_MODEL = "claude-sonnet-4-6"


class BaseAgent:
    """Base class for all GRC agents.

    Delegates all LLM calls to the configured provider (Anthropic or Ollama).
    Select the provider via the LLM_PROVIDER environment variable.
    """

    def __init__(
        self,
        system_prompt: str,
        tools: list[dict] | None = None,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self._system_prompt = system_prompt
        self.tools = tools or []
        self._provider: LLMProvider = create_provider()

    def run(self, user_message: str, context: dict | None = None) -> str:
        content = user_message
        if context:
            content = f"Context:\n{_format_context(context)}\n\n{user_message}"
        return self._provider.complete(
            system=self._system_prompt,
            messages=[{"role": "user", "content": content}],
            max_tokens=4096,
            tools=self.tools,
        )

    def run_streaming(self, user_message: str, context: dict | None = None) -> str:
        """Stream a long response and return the full text when done."""
        content = user_message
        if context:
            content = f"Context:\n{_format_context(context)}\n\n{user_message}"
        return self._provider.stream(
            system=self._system_prompt,
            messages=[{"role": "user", "content": content}],
            max_tokens=8192,
        )

    def run_with_tools(
        self, user_message: str, context: dict | None = None, max_iterations: int = 10
    ) -> str:
        """Agentic loop: calls tools until the model signals end_turn."""
        content = user_message
        if context:
            content = f"Context:\n{_format_context(context)}\n\n{user_message}"
        return self._provider.complete_with_tools(
            system=self._system_prompt,
            user_message=content,
            tools=self.tools,
            max_tokens=4096,
            handle_tool_call=self._handle_tool_call,
            max_iterations=max_iterations,
        )

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Override in subclasses to implement tool execution."""
        return f"Tool '{tool_name}' not implemented."


def _format_context(context: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in context.items())
