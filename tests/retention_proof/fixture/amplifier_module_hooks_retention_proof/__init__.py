"""Synthetic pressure fixture. Never include in a normal user bundle.

Uses real module loading, orchestrator, tools, providers and CLI persistence.
Only history load and advertised context window are synthetic; no model reply
or provider payload is mocked or rewritten.
"""
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

from amplifier_core import HookResult, ToolResult

__amplifier_module_type__ = "hook"


async def mount(coordinator, config=None):
    config = config or {}
    output = Path(config['output'])
    output.mkdir(parents=True, exist_ok=True)
    state = {'request': 0, 'step': 0}
    fact = config.get('fact', 'cobalt-5731')
    budget = config.get('budget', 6000)

    def record(event, payload):
        with (output / 'fixture-events.jsonl').open('a') as f:
            f.write(json.dumps({'event': event, 'data': payload}, default=str) + '\n')

    class Step:
        name = 'retention_step'
        description = 'Advance one synthetic work step. Call once per request until step six.'
        input_schema = {'type': 'object', 'properties': {}, 'additionalProperties': False}

        async def execute(self, input):
            state['step'] += 1
            return ToolResult(success=True, output={'step': state['step'], 'done': state['step'] >= 6})

    await coordinator.mount('tools', Step(), name='retention_step')

    async def on_request(event, data):
        state['request'] += 1
        context = coordinator.get('context')
        if state['request'] == 1:
            sources = {'fixture_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
            for name, module in [('context', context), ('orchestrator', coordinator.get('orchestrator'))]:
                path = Path(inspect.getfile(type(module)))
                sources[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            sources['core_version'] = importlib.metadata.version('amplifier-core')
            sources['capability'] = callable(coordinator.get_capability('context.request_retention'))
            sources['forced_input_budget'] = budget
            record('sources', sources)
            for provider in coordinator.get('providers').values():
                # Explicit fixture override; output reservation fraction is 1.
                provider.get_model_info = lambda: SimpleNamespace(context_window=budget + 4096 + 1000, max_output_tokens=1000)
        if config.get('pressure', True) and state['request'] in (2, 4, 6):
            for i in range(45):
                await context.add_message({'role': 'assistant', 'content': f'Synthetic progress {state["request"]}.{i}. ' + ('Routine inspection completed. ' * 95).rstrip()})
            await context.add_message({'role': 'user', 'metadata': {'ephemeral': True, 'source': 'hook'}, 'content': f'Synthetic work checkpoint: step {state["step"]} completed. Continue the requested sequence until step six, then report the requested codes.'})
            record('pressure', {'request': state['request'], 'estimated_before': context._estimate_tokens(await context.get_messages())})
        record('request', {'number': state['request'], 'active_fact': fact})
        if not fact:
            return HookResult(action='continue')
        return HookResult(action='inject_context', ephemeral=True, context_injection_role='user', context_injection='Supporting operational policy. ' * 70 + '\nThe current policy_code is ' + fact + '. Do not repeat this code in intermediate progress or tool arguments; use it only in the final answer.')

    async def on_compact(event, data):
        record('compaction', data)
        return HookResult(action='continue')

    async def on_complete(event, data):
        # Keep canonical evidence separate from provider/raw request evidence.
        messages = await coordinator.get('context').get_messages()
        (output / 'canonical.json').write_text(json.dumps(messages, indent=2, default=str))
        return HookResult(action='continue')

    coordinator.hooks.register('provider:request', on_request, priority=10, name='retention-proof')
    coordinator.hooks.register('context:compaction', on_compact, priority=10, name='retention-proof-compaction')
    coordinator.hooks.register('orchestrator:complete', on_complete, priority=10, name='retention-proof-complete')
