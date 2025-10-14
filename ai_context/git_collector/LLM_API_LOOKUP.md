# strangeloopcanon/llm-api-hub/blob/main

[git-collector-data]

**URL:** https://github.com/strangeloopcanon/llm-api-hub/blob/main/  
**Date:** 10/9/2025, 3:58:05 AM  
**Files:** 1  

=== File: README.md ===
# LLM API Lookup

One table. Links land on canonical, always-current docs for each provider.

Last verified: 2025-10-08 (HTTP checked from this environment; some providers block CLI requests behind Cloudflare, but the links below are the canonical doc URLs.)

| Provider | How to call (Text/Chat) | Models catalog | API reference (root) | Base URL |
|---|---|---|---|---|
| Google Gemini | https://ai.google.dev/api/generate-content | https://ai.google.dev/gemini-api/docs/models | https://ai.google.dev/api | https://generativelanguage.googleapis.com |
| OpenAI | https://platform.openai.com/docs/api-reference/responses/create | https://platform.openai.com/docs/models | https://platform.openai.com/docs/api-reference | https://api.openai.com |
| Anthropic (Claude) | https://docs.claude.com/en/api/messages | https://docs.claude.com/en/api/models | https://docs.claude.com/en/api | https://api.anthropic.com/v1 |
| xAI (Grok) | https://docs.x.ai/docs/api-reference | https://docs.x.ai/docs/models | https://docs.x.ai/docs/api-reference | https://api.x.ai/v1 |
| DeepSeek | https://api-docs.deepseek.com/api/create-chat-completion | https://api-docs.deepseek.com/api/list-models | https://api-docs.deepseek.com/ | https://api.deepseek.com |
| OpenRouter (Aggregator) | https://openrouter.ai/docs/quickstart | https://openrouter.ai/docs/api-reference/list-available-models | https://openrouter.ai/docs/api-reference/overview | https://openrouter.ai/api/v1 |

## How to use
- Pick your provider row and click “How to call” for the current request schema, parameters, and examples.
- Use “Models catalog” to confirm the latest model IDs and availability.
- For multi‑provider access or OpenAI‑compatible SDKs, consider OpenRouter; verify provider‑specific quirks via their API reference.

---

## Which API shape to use?

Minimal guidance to choose the right request shape by provider and task. Links go straight to the canonical pages.

| Task | OpenAI | Anthropic (Claude) | xAI (Grok) | DeepSeek | OpenRouter |
|---|---|---|---|---|---|
| Basic text/chat | Prefer Responses: https://platform.openai.com/docs/api-reference/responses/create • If a model doesn’t support Responses, use Chat Completions: https://platform.openai.com/docs/api-reference/chat/create (check model page: https://platform.openai.com/docs/models) | Messages: https://docs.claude.com/en/api/messages | OpenAI‑compatible Chat/Responses and Anthropic‑compatible Messages (see API Ref): https://docs.x.ai/docs/api-reference | Chat Completions: https://api-docs.deepseek.com/api/create-chat-completion | OpenAI‑like schema; see Quickstart: https://openrouter.ai/docs/quickstart |
| Structured JSON output | Structured outputs guide: https://platform.openai.com/docs/guides/structured-outputs (Responses API) | JSON output with Claude: https://docs.claude.com/en/docs/build-with-claude/json-output | Use xAI API reference for `response_format`/schema details: https://docs.x.ai/docs/api-reference | JSON mode: https://api-docs.deepseek.com/guides/json_mode | Use provider‑specific JSON/Tools via backend; see API overview: https://openrouter.ai/docs/api-reference/overview |
| Tool / function calling | Tools (function calling) overview: https://platform.openai.com/docs/guides/tools | Tool use with Claude: https://docs.claude.com/en/docs/build-with-claude/tool-use | See API reference (OpenAI/Anthropic compatible): https://docs.x.ai/docs/api-reference | Function calling guide: https://api-docs.deepseek.com/guides/function_calling | OpenAI‑style `tools` supported; see API overview: https://openrouter.ai/docs/api-reference/overview |

Addendum for Gemini:
- Basic text/chat: https://ai.google.dev/api/generate-content
- Structured JSON output: https://ai.google.dev/gemini-api/docs/structured-output
- Function calling: https://ai.google.dev/gemini-api/docs/function-calling

### Provider notes (brief)
- OpenAI: For new apps, use the unified Responses API. Some older models only document Chat Completions—if the model page lacks Responses examples, use Chat Completions. Always confirm on the model page: https://platform.openai.com/docs/models
- Anthropic: Use native tool calling (Messages `tools` param) rather than prompting for JSON when you need tools. Docs: tool use https://docs.claude.com/en/docs/build-with-claude/tool-use and API reference https://docs.claude.com/en/api/messages. Always send the `anthropic-version` header, and include `max_tokens` (required). Leave sampling params (e.g., temperature/top‑p) unset unless you need style variance; for tool loops, keep temperature low or 0.
- xAI: Offers OpenAI‑compatible Chat/Responses and Anthropic‑compatible Messages; pick the shape your client expects: https://docs.x.ai/docs/api-reference
- DeepSeek: Primary is OpenAI‑compatible Chat Completions. JSON mode and function calling are documented under Guides.
- OpenRouter: Aggregates many providers behind an OpenAI‑like schema; behavior follows the underlying model/provider.

