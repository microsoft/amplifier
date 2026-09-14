"""Probe: does a volatile `before_human` live instruction bust the prompt-cache prefix mid-turn?

Uses the REAL context-simple InstructionAssembly + SimpleContextManager and the REAL
Anthropic provider lowering (captured client, no network). One turn, two LLM
iterations with a tool batch in between. The producer's before_human content
changes between iteration 1 and 2 (the way hooks-todo-reminder and
hooks-status-context's per-request `git status` block do under v1).

Run from the workspace root:
  cd amplifier-module-provider-anthropic && uv run --with ../amplifier-module-context-simple python ../probe_cache_prefix.py
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from amplifier_core.message_models import ChatRequest, Message
from amplifier_module_context_simple import mount
from amplifier_module_provider_anthropic import AnthropicProvider


class FakeHookResponse:
    action = "continue"


class FakeCoordinator:
    def __init__(self) -> None:
        self._caps: dict[str, Any] = {}
        self.hooks = None

    def register_capability(self, name: str, value: Any) -> None:
        self._caps[name] = value

    def get_capability(self, name: str) -> Any:
        return self._caps.get(name)

    async def mount(self, name: str, obj: Any) -> None:
        setattr(self, name, obj)

    def get(self, name: str) -> Any:
        return getattr(self, name, None)

    async def process_hook_result(self, result: Any, event: str, hook_name: str) -> Any:
        return FakeHookResponse()


class DummyResp:
    """Minimal Anthropic response shape for provider.complete()."""

    def __init__(self) -> None:
        self.content = []
        self.stop_reason = "end_turn"
        self.usage = MagicMock(input_tokens=0, output_tokens=0, cache_read_input_tokens=0, cache_creation_input_tokens=0)
        self.model = "claude-opus-4-8"
        self.id = "msg"


def capture(provider: AnthropicProvider, messages: list[dict[str, Any]]) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    async def create(**params: Any) -> MagicMock:
        captured.update(params)
        response = MagicMock()
        response.parse = AsyncMock(return_value=DummyResp())
        response.headers = {}
        return response

    provider.client.messages.with_raw_response.create = AsyncMock(side_effect=create)
    req = ChatRequest(messages=[Message(**m) for m in messages])
    asyncio.run(provider.complete(req))
    return captured


async def build_views() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    coord = FakeCoordinator()
    await mount(coord, {"compaction_notice_enabled": False})
    context = coord.context
    assembly = coord.get_capability("context.instructions.v1")

    state = {"iteration": 1}

    def snapshot(scope: dict[str, Any]) -> list[dict[str, str]]:
        # Same shape as hooks-todo-reminder / status-context git block: content
        # depends on state that changes between LLM calls within one turn.
        return [
            {
                "key": "reminder",
                "content": f"<system-reminder>reminder rendered for iteration {state['iteration']}</system-reminder>",
                "placement": "before_human",
            }
        ]

    assembly.register("volatile-producer", snapshot)

    class Provider:
        instruction_layout_version = 1
        context_window = 200_000

    provider = Provider()
    with assembly.input_scope("human", "input-1"):
        await context.add_message({"role": "user", "content": "please fix the bug"})
    anchor = {"input_id": "input-1", "message_id": "input-1", "origin": "human"}

    async with assembly.turn("turn-1", anchor):
        # --- iteration 1 ---
        scope1 = {"turn_id": "turn-1", "request_id": "req-1", "input_anchor": anchor, "tail_anchor": None, "completed_batches": []}
        async with assembly.request(scope1, provider):
            view1 = await context.get_messages_for_request(provider=provider)
            assistant = {"role": "assistant", "content": "", "tool_calls": [{"id": "call-1", "name": "edit_file", "arguments": {}}], "metadata": {"message_id": "asst-1"}}
            await assembly.accept_response("req-1", assistant)
        await context.add_message({"role": "tool", "name": "edit_file", "tool_call_id": "call-1", "content": "ok", "metadata": {"message_id": "tool-1"}})

        # --- iteration 2: producer state changed (todo used / git status changed) ---
        state["iteration"] = 2
        scope2 = {"turn_id": "turn-1", "request_id": "req-2", "input_anchor": anchor, "tail_anchor": {"after_message_id": "tool-1"}, "completed_batches": []}
        async with assembly.request(scope2, provider):
            view2 = await context.get_messages_for_request(provider=provider)
    return view1, view2


def main() -> None:
    view1, view2 = asyncio.run(build_views())
    provider = AnthropicProvider(api_key="x", config={"default_model": "claude-opus-4-8", "enable_prompt_caching": True, "max_retries": 0, "use_streaming": False})
    wire1 = capture(provider, view1)["messages"]
    wire2 = capture(provider, view2)["messages"]

    print("=== iteration 1 wire messages ===")
    for i, m in enumerate(wire1):
        print(i, m["role"], json.dumps(m["content"])[:160])
    print("=== iteration 2 wire messages ===")
    for i, m in enumerate(wire2):
        print(i, m["role"], json.dumps(m["content"])[:160])

    # Longest common wire prefix (what a prefix cache could reuse)
    def strip_cc(m: dict[str, Any]) -> str:
        c = m["content"]
        if isinstance(c, list):
            c = [{k: v for k, v in b.items() if k != "cache_control"} for b in c]
        return json.dumps({"role": m["role"], "content": c}, sort_keys=True)

    common = 0
    for a, b in zip(wire1, wire2):
        if strip_cc(a) != strip_cc(b):
            break
        common += 1
    print(f"\ncommon cacheable prefix: {common} of {len(wire2)} messages in iteration 2 "
          f"(divergence at index {common}: the merged human message)")


if __name__ == "__main__":
    main()
