"""Replay a real root-session transcript through TODAY'S context-simple (origin/main)
and show what the model actually receives after compaction.
Usage: python probe_replay_compaction.py <sid-prefix> [context_window]"""
import asyncio, glob, json, os, sys, re
from amplifier_module_context_simple import SimpleContextManager

sid = sys.argv[1]; window = int(sys.argv[2]) if len(sys.argv) > 2 else 200_000
strip = len(sys.argv) > 3 and sys.argv[3] == "strip"
p = glob.glob(os.path.expanduser(f"~/.amplifier/projects/*/sessions/{sid}*/transcript.jsonl"))[0]
msgs = []
with open(p) as f:
    for line in f:
        try: m = json.loads(line)
        except Exception: continue
        if isinstance(m, dict) and "role" in m: msgs.append(m)

def is_reminder(m):
    md = m.get("metadata") or {}; c = m.get("content")
    return m.get("role") == "user" and (md.get("persisted") or (isinstance(c, str) and c.startswith("<system-reminder")))

class Prov: context_window = window

async def main():
    ctx = SimpleContextManager(max_tokens=window)
    async def factory(): return "SYSTEM PROMPT " + "x" * 40_000   # ~10K tokens, typical bundle
    await ctx.set_system_prompt_factory(factory)
    # replay up to N messages so we can look at a mid-session state too
    cut = int(len(msgs) * 0.6)
    for m in msgs[:cut]:
        if strip and is_reminder(m): continue
        await ctx.add_message(dict(m))
    view = await ctx.get_messages_for_request(provider=Prov())
    stats = ctx._last_compaction_stats or {}
    print(f"[{'STRIP reminders (pre-08-31 tail mode)' if strip else 'AS-IS (persist mode, today)'}] session {sid}: replayed {cut}/{len(msgs)} canonical msgs; budget window {window:,}")
    print(f"compaction stats: level={stats.get('strategy_level')} before={stats.get('before_tokens')} after={stats.get('after_tokens')} removed={stats.get('messages_removed')} stubbed={stats.get('user_messages_stubbed')}")
    roles = {}
    rem_full = rem_stub = real_full = real_stub = 0; rem_chars = 0
    for m in view:
        roles[m["role"]] = roles.get(m["role"], 0) + 1
        if m["role"] == "user":
            stub = m.get("_stubbed") or str(m.get("content","")).startswith("[User message compacted")
            if is_reminder(m) or "<system-reminder" in str(m.get("content","")) :
                if stub: rem_stub += 1
                else: rem_full += 1; rem_chars += len(str(m.get("content")))
            else:
                if stub: real_stub += 1
                else: real_full += 1
    print("roles in request view:", roles)
    print(f"reminder user msgs: {rem_full} intact ({rem_chars:,} chars) + {rem_stub} stubbed")
    print(f"real user msgs    : {real_full} intact + {real_stub} stubbed")
    # last real human message: intact?
    last_real = None
    for m in reversed(view):
        if m["role"] == "user" and not is_reminder(m) and "<system-reminder" not in str(m.get("content","")):
            last_real = m; break
    if last_real: print("last REAL human message in view:", repr(str(last_real.get('content'))[:120]))
asyncio.run(main())
