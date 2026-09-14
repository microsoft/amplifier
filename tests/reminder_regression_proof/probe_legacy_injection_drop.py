"""Probe: under v1, does an unmigrated hook's ephemeral injection (persisted by
loop-streaming's _drain_legacy_injections_into_v1_context) reach the model when a
system prompt factory is set (the app-cli / foundation default)?"""
import asyncio
from typing import Any
from amplifier_module_context_simple import mount

class R: action = "continue"
class Coord:
    def __init__(self): self._c = {}
    def register_capability(self, n, v): self._c[n] = v
    def get_capability(self, n): return self._c.get(n)
    async def mount(self, n, o): setattr(self, n, o)
    def get(self, n): return getattr(self, n, None)
    async def process_hook_result(self, *a, **k): return R()

async def main():
    coord = Coord()
    await mount(coord, {"compaction_notice_enabled": False})
    ctx, asm = coord.context, coord.get_capability("context.instructions.v1")
    async def factory(): return "BASE SYSTEM PROMPT"
    await ctx.set_system_prompt_factory(factory)
    class P: instruction_layout_version = 1; context_window = 200_000
    anchor = {"input_id": "in-1", "message_id": "in-1", "origin": "human"}
    with asm.input_scope("human", "in-1"):
        await ctx.add_message({"role": "user", "content": "hi"})
    # exactly what loop-streaming writes for an unmigrated hook under v1:
    await ctx.add_message({"role": "system", "content": "<system-reminders>\nWAYFINDER LEGACY REMINDER\n</system-reminders>",
                           "metadata": {"ephemeral": True, "legacy_injection": True}})
    async with asm.turn("t", anchor):
        async with asm.request({"turn_id": "t", "request_id": "r1", "input_anchor": anchor, "tail_anchor": None, "completed_batches": []}, P()):
            view = await ctx.get_messages_for_request(provider=P())
    blob = " ".join(str(m.get("content")) for m in view)
    print("messages in canonical history:", len(await ctx.get_messages()))
    print("messages in request view      :", len(view))
    print("legacy reminder reached model :", "WAYFINDER LEGACY REMINDER" in blob)
asyncio.run(main())
