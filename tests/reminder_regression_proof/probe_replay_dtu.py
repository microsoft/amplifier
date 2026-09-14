"""Replay the two DTU transcripts through today's context-simple with a small explicit
budget so compaction fires, and report what the model would receive."""
import asyncio, json, sys
from amplifier_module_context_simple import SimpleContextManager

def load(p):
    out=[]
    for line in open(p):
        try: m=json.loads(line)
        except Exception: continue
        if isinstance(m,dict) and "role" in m: out.append(m)
    return out
def is_rem(m):
    md=m.get("metadata") or {}; c=m.get("content")
    return m["role"]=="user" and (md.get("persisted") or (isinstance(c,str) and c.startswith("<system-reminder")))

async def run(label, path, budget):
    ctx = SimpleContextManager(max_tokens=budget)
    async def factory(): return "SYSTEM " + "x"*4000
    await ctx.set_system_prompt_factory(factory)
    for m in load(path): await ctx.add_message(dict(m))
    view = await ctx.get_messages_for_request(token_budget=budget)
    st = ctx._last_compaction_stats or {}
    rem=[m for m in view if m["role"]=="user" and is_rem(m)]
    real=[m for m in view if m["role"]=="user" and not is_rem(m)]
    stub=lambda m: bool(m.get("_stubbed"))
    last_user=[m for m in view if m["role"]=="user"][-1]
    print(f"[{label}] budget={budget:,} level={st.get('strategy_level')} before={st.get('before_tokens')} after={st.get('after_tokens')} removed={st.get('messages_removed')}")
    print(f"   view: {len(view)} msgs = {sum(m['role']=='tool' for m in view)} tool, {sum(m['role']=='assistant' for m in view)} assistant, "
          f"{len(real)} real user ({sum(map(stub,real))} stubbed), {len(rem)} reminders ({sum(map(stub,rem))} stubbed, {sum(len(str(m['content'])) for m in rem if not stub(m)):,} chars intact)")
    print(f"   last user-role msg the compactor protects as 'current intent': {'REMINDER' if is_rem(last_user) else 'real human'}: {str(last_user['content'])[:70]!r}")

async def main():
    for b in (12_000, 8_000):
        await run("P persist(today)", "results/transcript_P.jsonl", b)
        await run("T tail(fix)      ", "results/transcript_T.jsonl", b)
        print()
asyncio.run(main())
