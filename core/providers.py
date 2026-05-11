from __future__ import annotations

import os
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Common interface for all LLM backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int,
        tools: list[dict],
    ) -> str: ...

    @abstractmethod
    def stream(self, system: str, messages: list[dict], max_tokens: int) -> str: ...

    @abstractmethod
    def complete_with_tools(
        self,
        system: str,
        user_message: str,
        tools: list[dict],
        max_tokens: int,
        handle_tool_call,
        max_iterations: int,
    ) -> str: ...


class AnthropicProvider(LLMProvider):
    """Anthropic Claude backend with prompt caching."""

    def __init__(self, api_key: str, model: str) -> None:
        import anthropic as _anthropic
        self._anthropic = _anthropic
        self.client = _anthropic.Anthropic(api_key=api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    def _sys(self, text: str) -> list[dict]:
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    def complete(self, system: str, messages: list[dict], max_tokens: int, tools: list[dict]) -> str:
        try:
            kwargs: dict = dict(
                model=self._model,
                max_tokens=max_tokens,
                system=self._sys(system),
                messages=messages,
            )
            if tools:
                kwargs["tools"] = tools
            resp = self.client.messages.create(**kwargs)
            return "".join(b.text for b in resp.content if b.type == "text")
        except self._anthropic.BadRequestError as exc:
            return f"[Agent Error - BadRequest] {exc.message}"
        except self._anthropic.RateLimitError:
            return "[Agent Error] Rate limited — please retry in a moment."
        except self._anthropic.APIError as exc:
            return f"[Agent Error] {exc}"

    def stream(self, system: str, messages: list[dict], max_tokens: int) -> str:
        try:
            with self.client.messages.stream(
                model=self._model,
                max_tokens=max_tokens,
                system=self._sys(system),
                messages=messages,
            ) as s:
                return "".join(b.text for b in s.get_final_message().content if b.type == "text")
        except self._anthropic.BadRequestError as exc:
            return f"[Agent Error - BadRequest] {exc.message}"
        except self._anthropic.RateLimitError:
            return "[Agent Error] Rate limited — please retry in a moment."
        except self._anthropic.APIError as exc:
            return f"[Agent Error] {exc}"

    def complete_with_tools(
        self, system, user_message, tools, max_tokens, handle_tool_call, max_iterations
    ) -> str:
        messages = [{"role": "user", "content": user_message}]
        try:
            for _ in range(max_iterations):
                resp = self.client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    system=self._sys(system),
                    tools=tools,
                    messages=messages,
                )
                if resp.stop_reason == "end_turn":
                    return "".join(b.text for b in resp.content if b.type == "text")
                if resp.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": resp.content})
                    results = []
                    for block in resp.content:
                        if block.type == "tool_use":
                            results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": handle_tool_call(block.name, block.input),
                            })
                    if results:
                        messages.append({"role": "user", "content": results})
                elif resp.stop_reason == "max_tokens":
                    partial = "".join(b.text for b in resp.content if b.type == "text")
                    return f"[Agent Warning] Output truncated at max_tokens limit.\n{partial}"
                else:
                    return "".join(b.text for b in resp.content if b.type == "text")
            return "[Agent Error] Maximum tool iterations reached without end_turn."
        except self._anthropic.BadRequestError as exc:
            return f"[Agent Error - BadRequest] {exc.message}"
        except self._anthropic.RateLimitError:
            return "[Agent Error] Rate limited — please retry in a moment."
        except self._anthropic.APIError as exc:
            return f"[Agent Error] {exc}"


class OllamaProvider(LLMProvider):
    """Ollama backend via the OpenAI-compatible local API (http://localhost:11434/v1).

    Recommended models with tool support: llama3.2, llama3.1, qwen2.5, mistral-nemo.
    Install a model with: ollama pull llama3.2
    """

    def __init__(self, base_url: str, model: str) -> None:
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError(
                "The openai package is required for Ollama support.\n"
                "Run: pip install openai   or   uv pip install openai"
            )
        # Ollama exposes an OpenAI-compatible endpoint — api_key is unused but required by the client
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
        self._model = model

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @staticmethod
    def _to_openai_tools(tools: list[dict]) -> list[dict]:
        """Convert Anthropic tool schema format to OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
            for t in tools
        ]

    def complete(self, system: str, messages: list[dict], max_tokens: int, tools: list[dict]) -> str:
        try:
            all_msgs = [{"role": "system", "content": system}] + messages
            kwargs: dict = dict(model=self._model, messages=all_msgs, max_tokens=max_tokens)
            if tools:
                kwargs["tools"] = self._to_openai_tools(tools)
            resp = self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as exc:
            return f"[Agent Error] Ollama ({self._model}): {exc}"

    def stream(self, system: str, messages: list[dict], max_tokens: int) -> str:
        try:
            all_msgs = [{"role": "system", "content": system}] + messages
            chunks = self.client.chat.completions.create(
                model=self._model,
                messages=all_msgs,
                max_tokens=max_tokens,
                stream=True,
            )
            return "".join(
                chunk.choices[0].delta.content or ""
                for chunk in chunks
                if chunk.choices
            )
        except Exception as exc:
            return f"[Agent Error] Ollama ({self._model}): {exc}"

    def complete_with_tools(
        self, system, user_message, tools, max_tokens, handle_tool_call, max_iterations
    ) -> str:
        import json

        messages: list[dict] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]
        openai_tools = self._to_openai_tools(tools) if tools else []

        try:
            for _ in range(max_iterations):
                kwargs: dict = dict(model=self._model, messages=messages, max_tokens=max_tokens)
                if openai_tools:
                    kwargs["tools"] = openai_tools
                resp = self.client.chat.completions.create(**kwargs)
                choice = resp.choices[0]
                msg = choice.message

                if not msg.tool_calls or choice.finish_reason == "stop":
                    return msg.content or ""

                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in msg.tool_calls
                    ],
                })
                for tc in msg.tool_calls:
                    try:
                        tool_input = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_input = {}
                    result = handle_tool_call(tc.function.name, tool_input)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

            return "[Agent Error] Maximum tool iterations reached."
        except Exception as exc:
            return f"[Agent Error] Ollama ({self._model}): {exc}"


def create_provider() -> LLMProvider:
    """Instantiate the LLM provider selected by the LLM_PROVIDER environment variable.

    LLM_PROVIDER=anthropic (default)
        Requires: ANTHROPIC_API_KEY
        Optional: ANTHROPIC_MODEL (default: claude-sonnet-4-6)

    LLM_PROVIDER=ollama
        Optional: OLLAMA_BASE_URL (default: http://localhost:11434)
        Optional: OLLAMA_MODEL    (default: llama3.2)
        Requires: ollama running locally + `pip install openai`
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

    if provider == "ollama":
        return OllamaProvider(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        )

    # Default: Anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set.\n"
            "Add it to your .env file, or set LLM_PROVIDER=ollama to use a local model instead."
        )
    return AnthropicProvider(
        api_key=api_key,
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
    )
