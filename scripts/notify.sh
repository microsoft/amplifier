#!/usr/bin/env bash
# notify.sh — Send push notifications via ntfy.sh when long-running tasks complete
# Usage: notify.sh "Title" "Message body" [priority]
# Priority: 1=min, 2=low, 3=default, 4=high, 5=urgent
#
# Configuration:
#   NTFY_TOPIC  — required, your ntfy.sh topic (e.g., "amplifier-alerts")
#   NTFY_SERVER — optional, defaults to https://ntfy.sh
#
# Setup:
#   1. Install ntfy app on your phone (iOS/Android)
#   2. Subscribe to your topic in the app
#   3. export NTFY_TOPIC="your-topic-name" in your shell profile
#
# Integration with Amplifier:
#   Called by hooks when agents complete long-running tasks.
#   Can also be called directly: ./scripts/notify.sh "Build done" "All tests pass"

set -euo pipefail

TITLE="${1:-Amplifier}"
MESSAGE="${2:-Task completed}"
PRIORITY="${3:-3}"
NTFY_SERVER="${NTFY_SERVER:-https://ntfy.sh}"

if [[ -z "${NTFY_TOPIC:-}" ]]; then
    exit 0
fi

curl -sf \
    -H "Title: ${TITLE}" \
    -H "Priority: ${PRIORITY}" \
    -H "Tags: robot" \
    -d "${MESSAGE}" \
    "${NTFY_SERVER}/${NTFY_TOPIC}" > /dev/null 2>&1 || true
