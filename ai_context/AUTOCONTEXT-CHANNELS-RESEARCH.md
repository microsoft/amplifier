# AutoContext MCP Channels Research

**Date:** 2026-03-20
**CC Version:** 2.1.80
**AutoContext Version:** 0.1.0
**Status:** NOT YET AVAILABLE

## Findings

### --channels flag (Claude Code)
- `claude --help` does not list `--channels` in v2.1.80
- Changelog mentions it as "research preview" but it's not exposed in the CLI yet
- Likely gated behind a feature flag or future release

### AutoContext push support
- `autocontext_capabilities` returns 7 operations: evaluate_strategy, validate_strategy, publish_artifact, fetch_artifact, list_artifacts, distill_status, trigger_distillation
- **No push/channel/notification support** in the current API surface
- AutoContext is request-response only — no outbound event subscription

### Integration path (when available)
Expected flow:
1. `.mcp.json` adds `--channels` to autocontext server args
2. AutoContext MCP server declares supported channels in its manifest
3. Claude Code routes channel messages to a registered hook
4. Hook writes to `${CLAUDE_PLUGIN_DATA}/` for persistence

## Blockers
- Claude Code CLI does not expose `--channels` flag yet (research preview)
- AutoContext MCP server has no push/channel capability
- Both sides need updates before channels work

## Infrastructure Ready
Handler script (`hooks/mcp-channel-handler.sh`) and hooks.json registration are prepared.
When channels become available:
1. Add `--channels` to `.mcp.json` autocontext args
2. AutoContext needs to implement channel support on its side
3. Register MCPChannel event in hooks.json

## Next Steps
- Monitor Claude Code changelog for `--channels` graduation from research preview
- Monitor AutoContext releases for push/channel capability
- When both available: enable via `.mcp.json` flag + hooks.json entry
