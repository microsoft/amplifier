#!/usr/bin/env bash
# Resume arm P's (polluted, persist-mode) session under the FIXED binary (arm T env).
set -euo pipefail
export AMPLIFIER_HOME=/root/home_T UV_TOOL_DIR=/root/uvtools_T UV_TOOL_BIN_DIR=/root/bin_T PATH="/root/bin_T:$PATH"
PSID=$(basename "$(ls -td /root/home_P/projects/*/sessions/*/ | head -1)")
PSLUG=$(basename "$(dirname "$(dirname "$(ls -td /root/home_P/projects/*/sessions/*/ | head -1)")")")
mkdir -p "/root/home_T/projects/$PSLUG/sessions"
cp -r "/root/home_P/projects/$PSLUG/sessions/$PSID" "/root/home_T/projects/$PSLUG/sessions/"
cd /root/proj_P
BEFORE=$(wc -l < "/root/home_T/projects/$PSLUG/sessions/$PSID/transcript.jsonl")
amplifier run --mode single --output-format json --resume "$PSID" "Add one line to SUMMARY.md saying how many files you summarized in total, then tell me in one sentence what the FIRST thing I asked in this session was." > /root/resume.json 2>/root/resume.err || { echo "resume FAILED"; tail -c 1500 /root/resume.err; exit 1; }
TR="/root/home_T/projects/$PSLUG/sessions/$PSID/transcript.jsonl"
python3 - "$TR" "$BEFORE" <<'PY'
import json,sys
p,before=sys.argv[1],int(sys.argv[2]); lines=open(p).read().splitlines()
new=[json.loads(l) for l in lines[before:]]
rem=[m for m in new if m.get("role")=="user" and ((m.get("metadata") or {}).get("persisted") or str(m.get("content","")).startswith("<system-reminder"))]
print(json.dumps({"resumed_session_msgs_before":before,"new_msgs":len(new),"new_persisted_reminders":len(rem),"new_roles":[m.get("role") for m in new]}))
PY
python3 -c "import json; print('answer:', str(json.load(open('/root/resume.json')).get('response'))[:300])"
tail -3 SUMMARY.md
