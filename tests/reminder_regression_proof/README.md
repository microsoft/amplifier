# Reminder-regression proof (2026-09-14)

Evidence and reproduction for the long-session context regression, and for the
proposed fix: `amplifier-module-loop-streaming` branch
`fix/ephemeral-injection-default-tail` (default `ephemeral_injection_mode`
back to `"tail"`).

## Root cause

1. 2026-08-29 provider-openai #76: stateless-only (no `previous_response_id`);
   the full transcript is sent every call.
2. 2026-08-30/31 loop-streaming #44/#45/#46: `ephemeral_injection_mode` default
   flipped to `"persist"`. Every CHANGED merged hook injection is written to
   canonical history as a `role: user` message (`metadata.ephemeral=true,
   persisted=true`).
3. `hooks-mode` re-injects the full mode body (16-52K chars) on every
   `provider:request`; `hooks-todo-reminder` changes text every <=3 tool calls;
   the kernel merges all hooks into one blob, so the change-gate fires on
   nearly every LLM call and re-persists the whole blob.
4. context-simple's compactor treats every `role: user` message as a human
   turn: never removed, last one protected as the current intent, stubbed only
   after all removable assistant/tool history is gone. Persisted reminders are
   an irreducible, growing floor; real work is compacted away first.
5. Symptom patches landed elsewhere (foundation `is_real_user_message`
   2026-08-31, app-cli "hide persisted reminders" 2026-09-08); the compactor
   was never changed.

## Field measurements (read-only, this host)

- 1,399 root sessions >=40 messages since 08-25: 21,816 persisted reminder
  user-messages (149M chars) vs 6,710 real user messages (32M chars).
- Session `3d90a954` (09-14): 619 reminders, 27.7M chars, avg 44.7K; 604
  mid-turn; `mode-converge-manager` 443 blocks avg 52K chars.
- Replay through today's compactor, 200K window (`results/replay_results.txt`):
  as-is level 8, after=175K (target 100K, never converges), 333K chars of
  reminder text in the view; with reminders stripped level 7, after=99K.
- Same session through `fix/request-retention`'s compactor
  (`results/replay_retention.txt`): level 8, after=145K, 166K chars of
  reminders. The floor and the storm remain.

## DTU proof (dtu/, results/)

One DTU (`dtu/reminder-regression.yaml`), two `AMPLIFIER_HOME`s, same build
(2026.09.12), same foundation@main, same claude-sonnet-5, same 3-turn
tool-heavy task with `--resume`:

| | P: today (persist) | T: fix (tail) |
|---|---|---|
| real user messages | 3 (426 chars) | 3 (426 chars) |
| persisted reminder user-messages | 14 (16.7K chars), 11 mid-turn | 0 |
| task, resume, recall | OK | OK |
| replay @12K budget | level 3, 5 tool results, 1/3 human prompts stubbed | no compaction, all intact |
| replay @8K budget | level 5, 1 tool result, 2/3 human prompts stubbed | level 3, 6 tool results, 0 stubbed |
| Anthropic cached-input share | 92% | 89% |

A persist-mode (polluted) session resumed under the fixed binary works,
recalls the first request, and adds 0 new reminders (`dtu/resume_check.sh`).

## Reproduce

```bash
# census of persisted reminders in local root sessions
python3 probe_transcript_floor.py

# replay a real transcript through the context-simple checkout you run this in
cd <amplifier-module-context-simple checkout> && uv run python <this dir>/probe_replay_compaction.py <sid-prefix> 200000 [strip]

# DTU arms (needs ANTHROPIC_API_KEY, incus)
amplifier-digital-twin launch dtu/reminder-regression.yaml
amplifier-digital-twin file-push -r <id> <loop-streaming checkout on fix/ephemeral-injection-default-tail> /root/   # as /root/loop-streaming-tail
amplifier-digital-twin file-push <id> dtu/run_arm.sh /root/run_arm.sh
amplifier-digital-twin exec <id> -- bash /root/run_arm.sh P
amplifier-digital-twin exec <id> -- bash /root/run_arm.sh T
amplifier-digital-twin file-push <id> dtu/resume_check.sh /root/resume_check.sh
amplifier-digital-twin exec <id> -- bash /root/resume_check.sh
amplifier-digital-twin destroy <id>

# replay the two DTU transcripts through a context-simple checkout
cd <amplifier-module-context-simple checkout> && uv run python <this dir>/probe_replay_dtu.py
```

`probe_cache_prefix.py` and `probe_legacy_injection_drop.py` belong to the
review of the `feat/instruction-assembly-review-20260914` branches (live
`before_human` records bust the prompt-cache prefix mid-turn; unmigrated hook
injections are silently dropped under v1).
