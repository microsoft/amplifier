"""Measure, per ROOT session transcript (no '_' agent suffix), how much of the
canonical history is persisted reminder blobs (role=user + metadata.persisted)
vs real user turns, and how many messages the compactor can never remove.
Reads transcript.jsonl line by line with json; prints only aggregates."""
import json, sys, glob, os, datetime
rows = []
for p in glob.glob(os.path.expanduser("~/.amplifier/projects/*/sessions/*/transcript.jsonl")):
    sid = os.path.basename(os.path.dirname(p))
    if "_" in sid:  # sub-agent sessions
        continue
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(p))
    if mtime < datetime.datetime(2026, 8, 25):
        continue
    n = real_user = persisted = persisted_chars = real_chars = tool = asst = 0
    last_user_is_reminder = None
    try:
        with open(p) as f:
            for line in f:
                try:
                    m = json.loads(line)
                except Exception:
                    continue
                if not isinstance(m, dict) or "role" not in m:
                    continue
                n += 1
                role = m.get("role"); md = m.get("metadata") or {}
                c = m.get("content"); clen = len(c) if isinstance(c, str) else len(json.dumps(c))
                if role == "user":
                    if md.get("persisted") or (isinstance(c, str) and c.startswith("<system-reminder")):
                        persisted += 1; persisted_chars += clen; last_user_is_reminder = True
                    else:
                        real_user += 1; real_chars += clen; last_user_is_reminder = False
                elif role == "tool": tool += 1
                elif role == "assistant": asst += 1
    except Exception:
        continue
    if n >= 40:
        rows.append((n, real_user, persisted, persisted_chars, real_chars, tool, asst, last_user_is_reminder, mtime.date(), sid[:8]))
rows.sort(key=lambda r: -r[0])
print(f"{'msgs':>5} {'realU':>5} {'remU':>5} {'remKchars':>9} {'realKchars':>10} {'tool':>5} {'asst':>5} lastU=rem date       sid")
for r in rows[:25]:
    print(f"{r[0]:>5} {r[1]:>5} {r[2]:>5} {r[3]/1000:>9.0f} {r[4]/1000:>10.0f} {r[5]:>5} {r[6]:>5} {str(r[7]):>9} {r[8]} {r[9]}")
tot = [sum(r[i] for r in rows) for i in range(7)]
print(f"\n{len(rows)} root sessions >=40 msgs since 08-25: real user {tot[1]}, reminder-user {tot[2]} ({tot[3]/1000:.0f}K chars vs real {tot[4]/1000:.0f}K chars)")
