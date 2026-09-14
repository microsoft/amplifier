#!/usr/bin/env bash
# Usage: run_arm.sh <P|T>  -- runs inside the DTU. Three resumed turns of tool-heavy work.
set -euo pipefail
ARM="$1"
export AMPLIFIER_HOME=/root/home_$ARM
mkdir -p "$AMPLIFIER_HOME"
# Each arm gets its OWN uv tool environment: the CLI refuses to share one
# Python env across AMPLIFIER_HOMEs (editable installs are per-home).
export UV_TOOL_DIR=/root/uvtools_$ARM UV_TOOL_BIN_DIR=/root/bin_$ARM
if [ ! -x "$UV_TOOL_BIN_DIR/amplifier" ]; then uv tool install -q git+https://github.com/microsoft/amplifier >/dev/null 2>&1; fi
export PATH="$UV_TOOL_BIN_DIR:$PATH"
echo "amplifier=$(command -v amplifier)"
cat > "$AMPLIFIER_HOME/settings.yaml" <<YAML
config:
  providers:
    - module: provider-anthropic
      source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main
      config:
        api_key: \${ANTHROPIC_API_KEY}
        default_model: claude-sonnet-5
YAML
if [ "$ARM" = "T" ]; then
cat >> "$AMPLIFIER_HOME/settings.yaml" <<'YAML'
sources:
  modules:
    loop-streaming: file:///root/loop-streaming-tail
YAML
fi
amplifier bundle add git+https://github.com/microsoft/amplifier-foundation@main --app >/dev/null 2>&1 || true
PROJ=/root/proj_$ARM; rm -rf "$PROJ"; mkdir -p "$PROJ/sample"; cd "$PROJ"
for i in 1 2 3 4 5; do printf 'module %d\n' $i > sample/mod$i.py; for j in $(seq 1 $((i*7))); do echo "def f${i}_$j(x): return x + $j" >> sample/mod$i.py; done; done
git init -q . && git -c user.email=dtu@example.com -c user.name=dtu add -A && git -c user.email=dtu@example.com -c user.name=dtu commit -qm init

run() { amplifier run --mode single --output-format json "$@" 2>>"$PROJ/stderr.log"; }
echo "== turn 1"; run "Use the todo tool to plan, then read EVERY file under ./sample one at a time with the read tool and write SUMMARY.md listing each file with its function count. Keep the todo list updated as you go." > t1.json
SID=$(ls -t "$AMPLIFIER_HOME"/projects/*/sessions/ | head -1); SID=$(basename "$(ls -td "$AMPLIFIER_HOME"/projects/*/sessions/*/ | head -1)")
echo "session=$SID"
echo "== turn 2"; run --resume "$SID" "Now append a 'Line counts' section to SUMMARY.md with the exact line count of each sample file (use the bash tool with wc -l). Update the todo list." > t2.json
echo "== turn 3"; run --resume "$SID" "In ONE sentence: what was the very first thing I asked you to do in this session?" > t3.json
TR=$(ls "$AMPLIFIER_HOME"/projects/*/sessions/$SID/transcript.jsonl)
python3 - "$TR" "$ARM" <<'PY'
import json, sys
p, arm = sys.argv[1], sys.argv[2]
n=ru=rem=remc=ruc=asst=tool=0
for line in open(p):
    try: m=json.loads(line)
    except Exception: continue
    if not isinstance(m,dict) or "role" not in m: continue
    n+=1; r=m["role"]; md=m.get("metadata") or {}; c=m.get("content"); cl=len(c) if isinstance(c,str) else len(json.dumps(c))
    if r=="user":
        if md.get("persisted") or (isinstance(c,str) and c.startswith("<system-reminder")): rem+=1; remc+=cl
        else: ru+=1; ruc+=cl
    elif r=="assistant": asst+=1
    elif r=="tool": tool+=1
print(json.dumps({"arm":arm,"messages":n,"real_user":ru,"real_user_chars":ruc,"persisted_reminders":rem,"persisted_reminder_chars":remc,"assistant":asst,"tool":tool}))
PY
echo "== turn3 answer:"; python3 -c "import json,sys; d=json.load(open('t3.json')); print(str(d.get('response', d))[:300])" || cat t3.json | head -c 300
echo "== SUMMARY.md head:"; head -5 SUMMARY.md 2>/dev/null || echo "(missing)"
cp "$TR" /root/transcript_$ARM.jsonl
