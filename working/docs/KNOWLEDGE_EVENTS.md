Knowledge Pipeline Events
=========================

Overview
- Append-only newline-delimited JSON events at `.data/knowledge/events.jsonl`.
- Provides visibility into sync/extraction progress, skips, failures, and summaries.
- Minimal, durable, tail-friendly. No services required.

Event Types
- `sync_started`: Beginning of a sync run. Data: `total`, `max`.
- `article_skipped`: Pre-check/IO skip. Data: `title`, `reason`.
- `extraction_started`: Extraction begins for a source. Data: `title`.
- `extraction_succeeded`: Completed extraction. Data: counts for `concepts`, `relationships`, `insights`.
- `extraction_failed`: Extraction error. Data: `error`.
- `sync_finished`: Summary. Data: `processed`, `skipped`, `total`.

CLI Usage
- Last 50 events: `make knowledge-events N=50`
- Follow live (Ctrl+C to stop): `make knowledge-events-tail N=20`
- Summary:
  - Last run: `make knowledge-events-summary`
  - All events: `make knowledge-events-summary SCOPE=all`

Implementation Notes
- Emitted by `amplifier/knowledge_synthesis/cli.py` using `EventEmitter`.
- Stable filename enables easy tailing, scripts, or UI streaming later.
