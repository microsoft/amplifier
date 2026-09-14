"""Verify exported CLI captures, producing a public summary without raw data.

Usage: python check.py RUN_DIR... --output summary.json
The run directories must contain CI JSONL, fixture events, and runner summaries.
"""
import argparse
import hashlib
import json
from pathlib import Path

FACT = 'cobalt-5731'
ORIGINAL = 'amber-6428'
CORRECTION = 'violet-8392'


def without_cache(value):
    if isinstance(value, dict):
        return {k: without_cache(v) for k, v in value.items() if k != 'cache_control'}
    if isinstance(value, list):
        return [without_cache(v) for v in value]
    return value


def inspect_run(root):
    summary = json.loads((root / 'summary.json').read_text())
    files = list((root / 'captures').rglob('events.jsonl'))
    assert len(files) == 1, 'Expected exactly one resumed session capture'
    events = [json.loads(line) for line in files[0].read_text().splitlines()]
    fixture = [json.loads(line) for line in (root / 'fixture' / 'fixture-events.jsonl').read_text().splitlines()]
    sources = [e['data'] for e in fixture if e['event'] == 'sources']
    assert len(sources) == 2, 'Expected initial and resumed source identities'
    assert sources[0] == sources[1], 'Sources changed during resume'
    assert sources[0].get('fixture_sha256'), 'Stale fixture or missing fixture provenance'
    expected = json.loads(Path(__file__).with_name('source-identities.json').read_text())
    arm = summary['arm']
    for mounted, key in [('context', 'context_' + ('new' if arm in ('candidate', 'new-context') else 'old')),
                         ('orchestrator', 'loop_' + ('new' if arm in ('candidate', 'new-loop') else 'old'))]:
        assert sources[0][mounted]['sha256'] == expected[key]['sha256'], f'Wrong imported {mounted} source'
    assert sources[0]['fixture_sha256'] == expected['fixture']['sha256'], 'Wrong fixture source'
    assert sources[0]['core_version'] == '1.6.1', 'Core version drift'

    requests = [e['data']['raw'] for e in events if e['event'] == 'llm:request' and e['data'].get('raw')]
    assert requests, 'No durable raw provider requests'
    rows = []
    previous = None
    for index, request in enumerate(requests):
        messages = request.get('input', request.get('messages'))
        assert isinstance(messages, list), 'Unexpected provider wire format'
        user_text = json.dumps([m for m in messages if m.get('role') == 'user'])
        instructions = request.get('instructions', request.get('system'))
        rows.append({
            'request': index + 1,
            'policy_in_user_messages': FACT in user_text,
            'original_in_user_messages': ORIGINAL in user_text,
            'correction_in_user_messages': CORRECTION in user_text,
            'message_count': len(messages),
            'raw_request_sha256': hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
            'exact_previous_message_prefix': previous is not None and messages[:len(previous[0])] == previous[0],
            'previous_prefix_ignoring_cache_markers': previous is not None and without_cache(messages[:len(previous[0])]) == without_cache(previous[0]),
            'system_unchanged': previous is not None and instructions == previous[1],
        })
        previous = (messages, instructions)
    canonical = json.loads((root / 'fixture' / 'canonical.json').read_text())
    compactions = [e['data'] for e in fixture if e['event'] == 'compaction']
    tool_steps = sum(e['event'] == 'tool:post' and e['data'].get('tool_name') == 'retention_step' for e in events)
    complete = [e['data'].get('status') for e in events if e['event'] == 'orchestrator:complete']
    row = {k: v for k, v in summary.items() if k != 'pins'}
    usages = [e['data']['raw'].get('usage', {}) for e in events if e['event'] == 'llm:response' and e['data'].get('raw')]
    cache_reads = [u.get('cache_read_input_tokens', u.get('input_tokens_details', {}).get('cached_tokens', 0)) for u in usages]
    row.update(sources=sources[0], raw_requests=rows, tool_steps=tool_steps, completion_statuses=complete,
               provider_reported_cache_read_tokens=cache_reads,
               compactions=len(compactions), max_compaction_level=max((c.get('strategy_level', 0) for c in compactions), default=0),
               canonical_contains_policy=FACT in json.dumps(canonical),
               canonical_contains_original=ORIGINAL in json.dumps(canonical),
               canonical_contains_correction=CORRECTION in json.dumps(canonical),
               capture_sha256=hashlib.sha256(files[0].read_bytes()).hexdigest())
    assert summary['exit'] == 0 and summary.get('resume_exit') == 0, 'CLI execution failed'
    if summary['arm'] == 'candidate':
        assert all(r['policy_in_user_messages'] for r in rows), 'Active policy omitted from a candidate request'
        assert all(r['original_in_user_messages'] for r in rows), 'Original human fact omitted'
        assert json.loads(summary['response']) == {'policy_code': FACT, 'original_code': ORIGINAL}, 'Candidate initial recall failed'
        assert json.loads(summary['resume_response']) == {'policy_code': FACT, 'original_code': CORRECTION}, 'Candidate resumed recall failed'
        resume_positions = [i for i, e in enumerate(events) if e['event'] == 'session:resume']
        assert len(resume_positions) == 1, 'Expected exactly one CLI resume'
        split = resume_positions[0]
        initial_events, resumed_events = events[:split], events[split:]
        steps = [e['data']['result'] for e in initial_events if e['event'] == 'tool:post' and e['data'].get('tool_name') == 'retention_step']
        assert [s.get('output', {}).get('step') for s in steps] == list(range(1, 7)), 'Work steps must be sequential and complete'
        assert all(s.get('success') is True for s in steps), 'A work step failed'
        assert [s['output'].get('done') for s in steps] == [False] * 5 + [True], 'Incorrect work completion signal'
        assert not any(e['event'] == 'tool:post' for e in resumed_events), 'Resume must not continue old work'
        assert complete == ['success', 'success'], 'Candidate turn did not complete'
        assert row['canonical_contains_policy'] and row['canonical_contains_original'] and row['canonical_contains_correction'], 'Canonical evidence missing facts'
        for phase_events, expected_facts in [(initial_events, {'policy_code': FACT, 'original_code': ORIGINAL}),
                                              (resumed_events, {'policy_code': FACT, 'original_code': CORRECTION})]:
            responses = [e['data']['raw'] for e in phase_events if e['event'] == 'llm:response']
            assert responses, 'No raw response in turn'
            final = responses[-1]
            blocks = final.get('content', [])
            if 'output' in final:
                blocks = [b for item in final['output'] if item.get('type') == 'message' for b in item.get('content', [])]
            final_text = ''.join(b.get('text', '') for b in blocks)
            assert json.loads(final_text) == expected_facts, 'Raw final response contradicts reported recall'

        initial_requests = sum(e['event'] == 'llm:request' for e in initial_events)
        assert initial_requests == 7 and len(requests) == 8, 'Unexpected request sequence'
        assert all(r['correction_in_user_messages'] for r in rows[initial_requests:]), 'Current human correction missing on resume'
        phase = 0
        pressure, resumed_pressure, compact_counts = [], [], [0, 0]
        for e in fixture:
            if e['event'] == 'sources':
                phase += 1
            elif e['event'] == 'pressure':
                (pressure if phase == 1 else resumed_pressure).append(e['data']['request'])
            elif e['event'] == 'compaction':
                compact_counts[phase - 1] += 1
        assert pressure == [2, 4, 6] and not resumed_pressure, 'Wrong forced pressure sequence'
        assert compact_counts[0] >= 3 and compact_counts[1] >= 1, 'Missing initial or resumed compaction'
        row['verification'] = {'initial_successful_steps': list(range(1, 7)), 'resumed_tool_calls': 0,
                               'forced_pressure_requests': pressure, 'compactions_by_turn': compact_counts,
                               'final_responses_match_raw': True}

    return row


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = [inspect_run(p) for p in args.runs]
    args.output.write_text(json.dumps(rows, indent=2) + '\n')
    print('Verified', len(rows), 'runs and', sum(len(r['raw_requests']) for r in rows), 'raw requests')
