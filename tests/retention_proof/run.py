"""Run inside a DTU with the pinned CLI installed; emits private raw evidence."""
import argparse
import json
from pathlib import Path
import subprocess

PINS = {
    'context_old': '2d1bdc4d9c1803491fe39820c8d503dd764d32de',
    'context_new': '95de3a4d1580f506fbf6669f24520837faa7a7f9',
    'loop_old': '2feefe4ba0c4cb50fc0c6b33648a8ef6a2908820',
    'loop_new': 'fca01bbe17510fcc496a4496bfdb04f3f3393740',
    'fixture': '8510f9a99465466800e986bf149c0be332f87a1a',
    'openai': 'c9b0e8e60702269c7a637875b89d011facfde020',
    'anthropic': '12fffb6ad2bafb1bb7999ab02245a35e42ca8672',
    'ci': '089b79c90b4c5b5fa89f7be0240f4bba307a8c66',
}


def run(args):
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    arm = args.arm
    model = 'gpt-5.6-terra' if args.provider == 'openai' else 'claude-sonnet-5'
    def source(repo, pin, local=False):
        return f'git+{args.gitea if local else "https://github.com/microsoft"}/{repo}@{pin}'
    ctx = source('amplifier-module-context-simple', PINS['context_' + ('new' if arm in ('candidate', 'new-context') else 'old')], True)
    loop = source('amplifier-module-loop-streaming', PINS['loop_' + ('new' if arm in ('candidate', 'new-loop') else 'old')], True)
    bundle = root / 'bundle.md'
    bundle.write_text(f'''---
bundle:
  name: retention-proof-{args.provider}-{arm}
  version: 0.1.0
session:
  raw: true
  orchestrator:
    module: loop-streaming
    source: {loop}
    config:
      max_iterations: 12
  context:
    module: context-simple
    source: {ctx}
    config:
      compaction_notice_enabled: false
      output_reserve_fraction: 1.0
providers:
  - module: provider-{args.provider}
    source: {source('amplifier-module-provider-' + args.provider, PINS[args.provider])}
    config:
      default_model: {model}
      raw: true
      {'max_output_tokens' if args.provider == 'openai' else 'max_tokens'}: 1200
      max_retries: 1
hooks:
  - module: hooks-retention-proof
    source: {source('amplifier', PINS['fixture'], True)}#subdirectory=tests/retention_proof/fixture
    config:
      output: {root / 'fixture'}
      budget: {args.budget}
      pressure: {str(not args.no_pressure).lower()}
  - module: hook-context-intelligence
    source: {source('amplifier-bundle-context-intelligence', PINS['ci'])}#subdirectory=modules/hook-context-intelligence
    config:
      base_path: {root / 'captures'}
---
You are running a synthetic conversation-retention test. Follow the user's tool
sequence exactly. Do not restate or quote secret codes until the final answer.
If a code is not present in the current conversation, answer UNKNOWN; do not guess.
''')
    prompt = ('Call retention_step six times sequentially during this single turn. After each tool result with done=false, immediately call retention_step again. When done=true, answer with the requested JSON. '
              'Do not answer until step six is complete. ' + 'Background: keep the report concise. ' * 20 +
              'The original_code is amber-6428. After step six return only JSON containing policy_code from the operational policy and original_code from this request. '
              'Brief progress is allowed, but no code restatements before the final JSON.')
    base = ['amplifier', 'run', '-B', 'file://' + str(bundle), '--output-format', 'json']
    result = subprocess.run(base + [prompt], cwd=root, capture_output=True, text=True, timeout=600)
    (root / 'first.stdout').write_text(result.stdout)
    (root / 'first.stderr').write_text(result.stderr)
    summary = {'arm': arm, 'provider': args.provider, 'model': model, 'exit': result.returncode, 'pins': PINS}
    assert (root / 'fixture' / 'fixture-events.jsonl').is_file(), 'Fixture did not mount/run; this is not valid proof'
    if result.returncode == 0:
        payload = json.loads(result.stdout)
        summary['response'] = payload.get('response')
        sid = payload['session_id']
        resumed = subprocess.run(base + ['--resume', sid, 'Cancel all previous work-step instructions; that task is closed. Latest correction: original_code is now violet-8392. Return only JSON with policy_code and this corrected original_code. Do not call tools.'], cwd=root, capture_output=True, text=True, timeout=300)
        (root / 'resume.stdout').write_text(resumed.stdout)
        (root / 'resume.stderr').write_text(resumed.stderr)
        summary['resume_exit'] = resumed.returncode
        if resumed.returncode == 0:
            summary['resume_response'] = json.loads(resumed.stdout).get('response')
    (root / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != 'pins'}), flush=True)
    if result.returncode:
        print(result.stderr[-4000:], flush=True)
    return result.returncode or summary.get("resume_exit", 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gitea', required=True, help='Gitea endpoint including owner, reachable inside the DTU')
    parser.add_argument('--provider', choices=['openai', 'anthropic'], required=True)
    parser.add_argument('--arm', choices=['baseline', 'candidate', 'new-context', 'new-loop'], required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--budget', type=int, default=12000)
    parser.add_argument('--no-pressure', action='store_true')
    raise SystemExit(run(parser.parse_args()))
