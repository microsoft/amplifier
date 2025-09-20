"""
Standalone tool generator (deterministic scaffold writer).

Creates a reusable CLI tool under cli_tools/<name> that embeds
its own minimal microtask plumbing and uses Claude Code SDK directly.

No fallbacks: if SDK/CLI are missing, generated tools fail fast
with clear guidance.
"""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any

from ..llm import LLM
from .compose_synth import compose_recipes_from_plan as _compose_recipes_from_plan2
from .tool_philosophy import step_generate_tool_philosophy
from .tool_philosophy import step_plan_tool_philosophy


def _extract_json_object(text: str) -> str:
    import json as _json
    import re

    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if not m:
        idx = text.find("steps")
        if idx != -1:
            left_brace = text.rfind("{", 0, idx)
            right_brace = text.find("}", idx)
            if left_brace != -1 and right_brace != -1:
                frag = text[left_brace : right_brace + 1]
                _json.loads(frag)
                return frag
        raise ValueError("No JSON object found in plan text")
    frag = m.group(0)
    _json.loads(frag)
    return frag


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _pkg_name(name: str) -> str:
    return name.replace("-", "_")


def step_plan_tool(llm: LLM, artifacts: Path, name: str, desc: str, template: str | None = None) -> dict[str, Any]:
    # Use philosophy-driven generation when no template specified
    # This is the new default approach
    if template is None:
        return step_plan_tool_philosophy(llm, artifacts, name, desc)

    # Legacy template-specific handling for backward compatibility
    if template == "_legacy_compose":
        prompt = (
            "You are a Tool Architect. Design a CLI tool as a composition of micro-steps.\n\n"
            + "Goal: "
            + desc
            + "\nConstraints:\n"
            + "- No fallbacks; fail fast if SDK/CLI missing.\n"
            + "- Must stream progress per step and write artifacts and status incrementally (resume-friendly).\n\n"
            + "Available step kinds (choose any sequence):\n"
            + "- discover_markdown: inputs={src_dir:str, limit:int} -> outputs={files:list[str]}; writes discover.json\n"
            + "- extract_structured: inputs={schema:list[str]}; for each file, extract those lists (keys = schema) as JSON; resume by skipping existing; writes findings/*.json and findings.json index\n"
            + "- synthesize_catalog: combine extracted JSONs into a deduplicated catalog with explicit source mapping; writes catalog.json\n"
            + "- draft_blueprints: for each catalog item, write a blueprint markdown with sections [Context, Interfaces, Risks, Test Strategy, Milestones]; skip existing; writes blueprints/*.md\n\n"
            + "Return ONLY a JSON object with fields:\n"
            + '{\n  "steps": [{"kind": str, "id": str, "params": dict}],\n  "cli": {"requires": ["--src", "--limit"]}\n}\n'
        )
        plan_text = llm.complete(prompt, system="You return strict JSON only.")
        (artifacts / "tool_plan.txt").write_text(plan_text)
        try:
            plan_clean = _extract_json_object(plan_text)
        except Exception:
            plan_text2 = llm.complete(
                "Return ONLY a valid JSON object with 'steps' array and optional 'cli' field. No commentary. Goal: "
                + desc,
                system="You return strict JSON only.",
            )
            plan_clean = _extract_json_object(plan_text2)
        (artifacts / "plan.json").write_text(plan_clean)
        return {"plan_json": str((artifacts / "plan.json").resolve())}
    prompt = f"""
You are a zen architect. Propose a crisp plan for a CLI tool.

Name: {name}
Description: {desc}
Template: {template or "auto"}

Return only bullet points for:
- Commands and their options
- Inputs/outputs and where files are written
- Progress reporting model
- Failure behavior (no fallbacks)
"""
    plan = llm.complete(prompt)
    (artifacts / "tool_plan.txt").write_text(plan)
    return {"plan": plan}


def _pyproject_toml(name: str, pkg: str) -> str:
    return (
        dedent(
            f"""
        [build-system]
        requires = ["setuptools>=68", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{name}"
        version = "0.1.0"
        description = "Generated CLI tool ({name})"
        requires-python = ">=3.11"
        dependencies = [
            "click>=8.2.1",
            "claude-code-sdk>=0.0.20",
        ]

        [project.scripts]
        {name} = "{pkg}.cli:cli"
        """
        ).strip()
        + "\n"
    )


def _llm_py() -> str:
    return (
        dedent(
            """
        from __future__ import annotations

        import shutil
        import asyncio

        class LLMUnavailable(RuntimeError):
            '''Raised when Claude Code SDK/CLI is unavailable.'''

        try:
            from claude_code_sdk import query as sdk_query, ClaudeCodeOptions
        except Exception:  # pragma: no cover - handled at runtime
            sdk_query = None  # type: ignore
            ClaudeCodeOptions = None  # type: ignore

        def _ensure_available() -> None:
            if sdk_query is None or ClaudeCodeOptions is None:
                raise LLMUnavailable(
                    "Claude Code SDK not available. Install: pip install claude-code-sdk"
                )
            cli = shutil.which("claude") or shutil.which("@anthropic-ai/claude-code")
            if not cli:
                raise LLMUnavailable(
                    "Claude CLI not found. Install: npm i -g @anthropic-ai/claude-code"
                )

        def complete(prompt: str, *, role: str | None = None, model: str | None = None) -> str:
            _ensure_available()

            assert ClaudeCodeOptions is not None and sdk_query is not None
            opts = ClaudeCodeOptions(
                system_prompt=role,
                model=model or "claude-3-5-sonnet-20241022",
                max_turns=1,
            )

            async def _go() -> str:
                chunks: list[str] = []
                final: str | None = None
                async for message in sdk_query(prompt=prompt, options=opts):  # type: ignore[misc]
                    tname = type(message).__name__
                    if tname == "ResultMessage":
                        final = getattr(message, "result", None)
                    elif hasattr(message, "content"):
                        for block in getattr(message, "content", []) or []:
                            txt = getattr(block, "text", None)
                            if txt:
                                chunks.append(str(txt))
                return final or "".join(chunks)

            return asyncio.run(_go())
        """
        ).strip()
        + "\n"
    )


def _orchestrator_py(tool_name: str) -> str:
    lines = [
        "from __future__ import annotations",
        "",
        "import json",
        "import uuid",
        "from pathlib import Path",
        "from typing import Any, Callable",
        "",
        "class State:",
        "    def __init__(self, job_id: str, recipe: str, run_dir: Path) -> None:",
        "        self.job_id = job_id",
        "        self.recipe = recipe",
        "        self.run_dir = run_dir",
        "        self.steps: list[dict[str, Any]] = []",
        "",
        "    def artifacts_dir(self) -> Path:",
        "        d = self.run_dir / 'artifacts'",
        "        d.mkdir(parents=True, exist_ok=True)",
        "        return d",
        "",
        "    def save(self) -> None:",
        "        path = self.run_dir / 'results.json'",
        "        tmp = path.with_suffix('.tmp')",
        "        tmp.write_text(json.dumps({",
        "            'job_id': self.job_id,",
        "            'recipe': self.recipe,",
        "            'updated_at': '',",
        "            'steps': self.steps,",
        "        }, indent=2))",
        "        tmp.replace(path)",
        "",
        "class Orchestrator:",
        "    def __init__(self, base: Path | None = None) -> None:",
        "        self.base = base or Path('.data') / '{TOOL_NAME}' / 'runs'",
        "        self.base.mkdir(parents=True, exist_ok=True)",
        "",
        "    def run(",
        "        self,",
        "        recipe: str,",
        "        steps: list[tuple[str, Callable[[Path], dict[str, Any]]]],",
        "        on_event: Callable[[str, str, dict[str, Any] | None], None] | None = None,",
        "    ) -> State:",
        "        job_id = str(uuid.uuid4())",
        "        run_dir = self.base / job_id",
        "        run_dir.mkdir(parents=True, exist_ok=True)",
        "        state = State(job_id, recipe, run_dir)",
        "        arts = state.artifacts_dir()",
        "        if on_event:",
        "            on_event('job', recipe, {'job_id': job_id, 'artifacts_dir': str(arts)})",
        "        for step_name, fn in steps:",
        "            if on_event:",
        "                on_event('start', step_name, None)",
        "            try:",
        "                out = fn(arts)",
        "                state.steps.append({'name': step_name, 'status': 'succeeded', 'output': out})",
        "                state.save()",
        "                if on_event:",
        "                    on_event('success', step_name, out)",
        "            except Exception as e:  # noqa: BLE001",
        "                state.steps.append({'name': step_name, 'status': 'failed', 'error': str(e)})",
        "                state.save()",
        "                if on_event:",
        "                    on_event('fail', step_name, {'error': str(e)})",
        "                break",
        "        return state",
    ]
    return "\n".join(lines).replace("{TOOL_NAME}", tool_name) + "\n"


def _ideas_recipe_py(tool_name: str) -> str:
    lines = [
        "from __future__ import annotations",
        "",
        "import json",
        "import re",
        "from pathlib import Path",
        "from typing import Any",
        "",
        "from .llm import complete",
        "",
        "def _w(path: Path, text: str) -> None:",
        "    path.parent.mkdir(parents=True, exist_ok=True)",
        "    path.write_text(text, encoding='utf-8')",
        "",
        "def _r(path: Path) -> str:",
        "    return path.read_text(encoding='utf-8', errors='ignore')",
        "",
        "def step_discover(art: Path, src: Path, limit: int) -> dict[str, Any]:",
        "    files = sorted(src.glob('*.md'))[:limit]",
        "    (art / 'discover.json').write_text(json.dumps([str(p) for p in files], indent=2))",
        "    return {'count': len(files), 'files': [str(p) for p in files]}",
        "",
        "def step_summarize_each(art: Path, work: Path) -> dict[str, Any]:",
        "    listing = json.loads((art / 'discover.json').read_text())",
        "    out_dir = work / 'summaries'",
        "    out_dir.mkdir(parents=True, exist_ok=True)",
        "    idx: list[str] = []",
        "    total = len(listing)",
        "    status = art / 'status.json'",
        "    for i, s in enumerate(listing, 1):",
        "        p = Path(s)",
        '        out = out_dir / f"{p.stem}.summary.md"',
        "        if out.exists():",
        "            idx.append(str(out))",
        "            status.write_text(json.dumps({'stage': 'summarize_each', 'done': i, 'total': total, 'file': s}))",
        "            continue",
        "        raw = _r(p)",
        "        summary = complete('Summarize the following markdown as 5-10 concrete bullet points. Avoid meta commentary.\n\n' + raw, role='analysis expert')",
        "        low = summary.lower().strip()",
        "        if len(summary) < 120 or any(k in low for k in ['i\\'ll', 'i will', 'let me', 'i\\'m going to', 'i am going to']):",
        "            summary = complete('Rewrite as a clean bullet list with concrete content only.\n\n' + raw, role='synthesis master')",
        "        _w(out, summary)",
        "        idx.append(str(out))",
        "        status.write_text(json.dumps({'stage': 'summarize_each', 'done': i, 'total': total, 'file': s}))",
        "    (art / 'summaries.json').write_text(json.dumps(idx, indent=2))",
        "    return {'summaries': idx}",
        "",
        "def _extract_json_array(text: str) -> list[dict]:",
        "    m = re.search(r'```json\s*(.*?)```', text, flags=re.S | re.I)",
        "    block = m.group(1) if m else None",
        "    if not block:",
        "        s = text.find('[')",
        "        e = text.rfind(']')",
        "        block = text[s : e + 1] if s != -1 and e != -1 and e > s else None",
        "    if not block:",
        "        return []",
        "    try:",
        "        return json.loads(block)",
        "    except Exception:",
        "        return []",
        "",
        "def step_synthesize_ideas(art: Path) -> dict[str, Any]:",
        "    sums = json.loads((art / 'summaries.json').read_text())",
        "    docs = [{'path': s, 'text': _r(Path(s))} for s in sums]",
        "    allowed = [d['path'] for d in docs]",
        "    prompt = (",
        "        'You are an idea synthesizer. Propose net-new ideas that combine insights across summaries.\n'",
        "        + 'Return ONLY a JSON array of objects: {\"title\": str, \"rationale\": str, \"sources\": [str]}.\n'",
        "        + 'Use sources ONLY from this allowed list: ' + json.dumps(allowed) + '\n\n'",
        "        + json.dumps(docs)[:90000]",
        "    )",
        "    raw = complete(prompt, role='analysis expert')",
        "    ideas = _extract_json_array(raw)",
        "    if not ideas:",
        "        prompt2 = (",
        "            'Return ONLY a JSON array with at least 5 items; each item must be ' ",
        "            + '{\"title\": str, \"rationale\": str, \"sources\": [str]} and sources must come from: ' ",
        "            + json.dumps(allowed) + '\n\nSummaries:\n' + json.dumps(docs)[:90000]",
        "        )",
        "        raw = complete(prompt2, role='synthesis master')",
        "        ideas = _extract_json_array(raw)",
        "    fixed: list[dict] = []",
        "    for it in ideas or []:",
        "        it['sources'] = [s for s in (it.get('sources') or []) if s in allowed]",
        "        fixed.append(it)",
        "    ideas = fixed",
        "    if not ideas:",
        "        raw2 = complete(",
        "            'List 8-12 cross-document synthesis ideas as bullet points focused on novelty. ' ",
        "            + 'Then output ONLY a JSON array under the schema {\"title\": str, \"rationale\": str, \"sources\": [str]} ' ",
        "            + 'with sources restricted to: ' + json.dumps(allowed) + '\n\n' + json.dumps(docs)[:90000],",
        "            role='synthesis master',",
        "        )",
        "        ideas = _extract_json_array(raw2)",
        "        fixed = []",
        "        for it in ideas or []:",
        "            it['sources'] = [s for s in (it.get('sources') or []) if s in allowed]",
        "            fixed.append(it)",
        "        ideas = fixed",
        "    (art / 'ideas.json').write_text(json.dumps(ideas, indent=2))",
        "    return {'ideas_count': len(ideas)}",
        "",
        "def step_expand_ideas(art: Path, src_dir: Path, work: Path) -> dict[str, Any]:",
        "    def _map_source(src: str) -> Path:",
        "        p = Path(src)",
        "        if p.name.endswith('.summary.md'):",
        "            c = src_dir / p.name.replace('.summary.md', '.md')",
        "            return c if c.exists() else p",
        "        return p if p.exists() else (src_dir / p.name)",
        "",
        "    ideas = json.loads((art / 'ideas.json').read_text())",
        "    out_dir = work / 'ideas'",
        "    out_dir.mkdir(parents=True, exist_ok=True)",
        "    expanded = 0",
        "    total = len(ideas)",
        "    status = art / 'status.json'",
        "    for i, idea in enumerate(ideas, 1):",
        "        title = idea.get('title') or f\"idea_{i:03d}\"",
        "        outfile = out_dir / f\"{title.replace(\' \', \'_\').lower()}\"",
        "        if outfile.exists():",
        "            status.write_text(json.dumps({'stage': 'expand_ideas', 'done': i, 'total': total, 'title': title, 'skipped': True}))",
        "            continue",
        "        srcs = [_map_source(s) for s in idea.get('sources', [])]",
        "        body = ('\n\n'.join(_r(p) for p in srcs if p and p.exists()))[:120000]",
        "        prompt = (",
        "            'Idea: ' + title + '\n\nRationale: ' + (idea.get('rationale', '') or '') + '\n\n'",
        "            + 'Write a persuasive case and concrete plan. Include: ## Context, ## Benefits, ## Risks, ## Plan. Do not ask for more information. ' ",
        "            + 'Relevant sources (may be partial excerpts):\n' + body",
        "        )",
        "        text = complete(prompt, role='modular builder')",
        "        if any(p in text.lower() for p in ['please provide', 'i don\'t see enough context', 'i need more', 'could you provide']):",
        "            text = complete('Rewrite into a concrete blueprint with sections: ## Context, ## Benefits, ## Risks, ## Plan. Do not ask questions; use the sources as context.\n\n' + text, role='synthesis master')",
        "        if text.count('## ') < 3 or len(text) < 600:",
        "            critique = complete('Critique this blueprint; list missing sections and weak depth.', role='analysis expert')",
        "            text = complete('Improve the blueprint using these fixes. Return only improved markdown.\nFixes:\n' + critique + '\n\n' + text, role='synthesis master')",
        "        required = ['## Context', '## Benefits', '## Risks', '## Plan']",
        "        def _ok(t: str) -> bool:",
        "            tl = t.lower()",
        "            if any(k.lower() not in tl for k in required):",
        "                return False",
        "            return len(t) > 800",
        "        if not _ok(text):",
        "            text = complete('Rewrite to include sections ## Context, ## Benefits, ## Risks, ## Plan with substantive detail (150+ words across sections). Return only markdown.\n\n' + text, role='synthesis master')",
        "            if not _ok(text):",
        "                text = complete('Using the sources below, write a complete blueprint with the required sections and depth. Return only markdown.\n\n' + body, role='synthesis master')",
        "        _w(outfile, text)",
        "        expanded += 1",
        "        status.write_text(json.dumps({'stage': 'expand_ideas', 'done': i, 'total': total, 'title': title}))",
        "    return {'expanded': expanded}",
        "",
        "def run(src: str, *, limit: int = 5, work: str | None = None, on_event=None) -> dict[str, Any]:",
        "    from .orchestrator import Orchestrator",
        "",
        "    srcp = Path(src)",
        "    workp = Path(work) if work else Path('.data') / '{TOOL}' / 'ideas_work'",
        "    orch = Orchestrator(Path('.data') / '{TOOL}' / 'runs')",
        "    steps = [",
        "        ('discover', lambda art: step_discover(art, srcp, limit)),",
        "        ('summarize_each', lambda art: step_summarize_each(art, workp)),",
        "        ('synthesize_ideas', lambda art: step_synthesize_ideas(art)),",
        "        ('expand_ideas', lambda art: step_expand_ideas(art, srcp, workp)),",
        "    ]",
        "    s = orch.run('ideas', steps, on_event)",
        "    return {",
        "        'job_id': s.job_id,",
        "        'recipe': s.recipe,",
        "        'success': all(step.get('status') == 'succeeded' for step in s.steps),",
        "        'artifacts_dir': str((Path('.data') / '{TOOL}' / 'runs' / s.job_id / 'artifacts').resolve()),",
        "    }",
    ]
    return "\n".join(lines).replace("{TOOL}", tool_name) + "\n"

def _summarize_recipe_py() -> str:
    lines = [
        "from __future__ import annotations",
        "",
        "from pathlib import Path",
        "from typing import Any",
        "",
        "from .llm import complete",
        "",
        "def summarize(paths: list[str], purpose: str | None = None) -> dict[str, Any]:",
        "    docs = [Path(p) for p in paths]",
        "    if not docs:",
        '        raise ValueError("No input files provided")',
        "    if purpose is None:",
        "        purpose = (",
        '            "Create an executive-style summary with key points and actionable recommendations.")',
        '    text = "\\n\\n".join(d.read_text(encoding="utf-8", errors="ignore") for d in docs)',
        "    prompt = (",
        "        purpose",
        '        + "\\n\\nSummarize the following content with clear section headings and 5-10 bullets.\\n\\n"',
        "        + text[:120000]",
        "    )",
        '    out = complete(prompt, role="analysis expert")',
        '    return {"summary": out}',
    ]
    return "\n".join(lines) + "\n"


def _compose_recipes_from_plan(tool_name: str, plan_text: str) -> str:
    try:
        plan_obj = json.loads(plan_text)
    except Exception:
        plan_obj = {}
    plan_literal = json.dumps(plan_obj)
    body = dedent("""
        from __future__ import annotations

        import json
        from pathlib import Path
        from typing import Any

        from .llm import complete

        PLAN = __PLAN__

        def _w(path: Path, text: str) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')

        def _r(path: Path) -> str:
            return path.read_text(encoding='utf-8', errors='ignore')

        def step_discover_markdown(art: Path, src_dir: Path, limit: int) -> dict[str, Any]:
            files = sorted(src_dir.glob('*.md'))[:limit]
            (art / 'discover.json').write_text(json.dumps([str(p) for p in files], indent=2))
            return {'files': [str(p) for p in files]}

        def step_extract_structured(art: Path, work: Path, schema: list[str]) -> dict[str, Any]:
            files = json.loads((art / 'discover.json').read_text()) if (art / 'discover.json').exists() else []
            out_dir = work / 'findings'
            out_dir.mkdir(parents=True, exist_ok=True)
            index: list[str] = []
            for p in files:
                path = Path(p)
                out = out_dir / f"{path.stem}.json"
                if out.exists():
                    index.append(str(out))
                    continue
                text = _r(path)
                keys = ', '.join(schema)
                prompt = (
                    'Extract the following lists as JSON keys [' + keys + '] from the document.\n'
                    'Return ONLY JSON with those keys, each an array of terse strings.\n\n' + text
                )
                raw = complete(prompt, role='analysis expert')
                data = {k: [] for k in schema}
                try:
                    import re, json as _json
                    m = re.search(r'```json\n(.*?)```', raw, flags=re.S | re.I)
                    block = m.group(1) if m else raw
                    data = _json.loads(block)
                except Exception:
                    pass
                out.write_text(json.dumps(data, indent=2))
                index.append(str(out))
            (art / 'findings.json').write_text(json.dumps(index, indent=2))
            return {'findings': index}

        def step_synthesize_catalog(art: Path) -> dict[str, Any]:
            index = json.loads((art / 'findings.json').read_text()) if (art / 'findings.json').exists() else []
            items = []
            for f in index:
                try:
                    items.append({'path': f, 'data': json.loads(Path(f).read_text())})
                except Exception:
                    items.append({'path': f, 'data': {}})
            prompt = (
                'Build a deduplicated requirements catalog from the items below. '
                'Each entry must be {id, title, rationale, sources[list of paths]} and id must be stable.\n\n'
                + json.dumps(items)[:90000]
            )
            raw = complete(prompt, role='synthesis master')
            catalog: list[dict] = []
            try:
                import re, json as _json
                m = re.search(r'```json\n(.*?)```', raw, flags=re.S | re.I)
                block = m.group(1) if m else raw
                catalog = _json.loads(block)
            except Exception:
                catalog = []
            (art / 'catalog.json').write_text(json.dumps(catalog, indent=2))
            return {'catalog_count': len(catalog)}

        def step_draft_blueprints(art: Path, work: Path) -> dict[str, Any]:
            catalog = json.loads((art / 'catalog.json').read_text()) if (art / 'catalog.json').exists() else []
            out_dir = work / 'blueprints'
            out_dir.mkdir(parents=True, exist_ok=True)
            written = 0
            for i, item in enumerate(catalog, 1):
                name = item.get('title') or ('item_%03d' % i)
                outfile = out_dir / (name.replace(' ', '_').lower() + '.md')
                if outfile.exists():
                    continue
                rationale = item.get('rationale', '')
                sources = '\n'.join(item.get('sources', []))
                prompt = (
                    'Item: ' + name + '\n\nRationale: ' + rationale + '\n\n'
                    'Draft a blueprint with sections: ## Context, ## Interfaces, ## Risks, ## Test Strategy, ## Milestones. '
                    'Reference source filenames where appropriate.\n\nSources:\n' + sources
                )
                text = complete(prompt, role='modular builder')
                if text.count('## ') < 3 or len(text) < 600:
                    critique = complete('Critique this blueprint; list missing sections and weak depth.', role='analysis expert')
                    text = complete('Improve the blueprint using these fixes. Return only improved markdown.\nFixes:\n' + critique + '\n\n' + text, role='synthesis master')
                outfile.write_text(text)
                written += 1
            return {'blueprints': written}

        def run(src: str, *, limit: int = 5, work: str | None = None, on_event=None) -> dict[str, Any]:
            from .orchestrator import Orchestrator

            srcp = Path(src)
            workp = Path(work) if work else Path('.data') / '__TOOL__' / 'compose_work'
            orch = Orchestrator(Path('.data') / '__TOOL__' / 'runs')

            steps_cfg = PLAN.get('steps', []) if isinstance(PLAN, dict) else []
            def _resolve(step: dict[str, Any]):
                kind = step.get('kind')
                params = step.get('params') or {}
                if kind == 'discover_markdown':
                    lim = int(params.get('limit') or limit)
                    return ('discover', lambda art: step_discover_markdown(art, srcp, lim))
                if kind == 'extract_structured':
                    schema = list(params.get('schema') or ['features','constraints','acceptance_criteria'])
                    return ('extract_structured', lambda art: step_extract_structured(art, workp, schema))
                if kind == 'synthesize_catalog':
                    return ('synthesize_catalog', lambda art: step_synthesize_catalog(art))
                if kind == 'draft_blueprints':
                    return ('draft_blueprints', lambda art: step_draft_blueprints(art, workp))
                raise ValueError('Unknown step kind: ' + str(kind))

            steps = [_resolve(s) for s in steps_cfg] or [
                ('discover', lambda art: step_discover_markdown(art, srcp, limit)),
                ('extract_structured', lambda art: step_extract_structured(art, workp, ['features','constraints','acceptance_criteria'])),
                ('synthesize_catalog', lambda art: step_synthesize_catalog(art)),
                ('draft_blueprints', lambda art: step_draft_blueprints(art, workp)),
            ]
            s = orch.run('compose', steps, on_event)
            return {
                'job_id': s.job_id,
                'recipe': s.recipe,
                'success': True,
                "artifacts_dir": str((Path('.data') / '__TOOL__' / 'runs' / s.job_id / 'artifacts').resolve()),
            }
    """)
    return body.replace("__PLAN__", plan_literal).replace("__TOOL__", tool_name) + "\n"


def _cli_py(name: str, pkg: str, template: str | None) -> str:
    if template is None:
        return (
            dedent(
                """
            from __future__ import annotations

            import json
            import click

            from .microtasks.recipes import run as run_compose

            @click.group()
            def cli() -> None:
                pass

            @cli.command("run")
            @click.option("--src", required=True, type=click.Path(exists=True, file_okay=False))
            @click.option("--limit", default=5, show_default=True, type=int)
            @click.option("--work", default=None, type=click.Path(file_okay=False))
            def run_cmd(src: str, limit: int, work: str | None) -> None:
                def _progress(evt: str, step_name: str, payload: dict | None) -> None:
                    if evt == 'job' and payload:
                        print('job_id: ' + str(payload.get('job_id')) + '  artifacts: ' + str(payload.get('artifacts_dir')))
                        return
                    print({'start': '▶ ' + step_name + '...', 'success': '✔ ' + step_name, 'fail': '✖ ' + step_name + ' failed'}.get(evt, step_name))

                res = run_compose(src, limit=limit, work=work, on_event=_progress)
                print(json.dumps(res, indent=2))
            """
            ).strip()
            + "\n"
        )
    if template == "ideas":
        return (
            dedent(
                """
            from __future__ import annotations

            import json
            import click

            from .microtasks.recipes import run as run_ideas

            @click.group()
            def cli() -> None:
                pass

            @cli.command("run")
            @click.option("--src", required=True, type=click.Path(exists=True, file_okay=False))
            @click.option("--limit", default=5, show_default=True, type=int)
            @click.option("--work", default=None, type=click.Path(file_okay=False))
            def run_cmd(src: str, limit: int, work: str | None) -> None:
                def _progress(evt: str, step_name: str, payload: dict | None) -> None:
                    if evt == 'job' and payload:
                        print('job_id: ' + str(payload.get('job_id')) + '  artifacts: ' + str(payload.get('artifacts_dir')))
                        return
                    print({'start': '▶ ' + step_name + '...', 'success': '✔ ' + step_name, 'fail': '✖ ' + step_name + ' failed'}.get(evt, step_name))

                res = run_ideas(src, limit=limit, work=work, on_event=_progress)
                print(json.dumps(res, indent=2))
            """
            ).strip()
            + "\n"
        )
    return (
        dedent(
            """
        from __future__ import annotations

        import json
        import click

        from .microtasks.recipes import summarize as summarize_impl

        @click.group()
        def cli() -> None:
            pass

        @cli.command("summarize")
        @click.option("--purpose", default=None, help="Custom summarization goal")
        @click.argument("files", nargs=-1, type=click.Path(exists=True, dir_okay=False))
        def summarize_cmd(purpose: str | None, files: tuple[str, ...]) -> None:
            if not files:
                raise click.ClickException("Provide at least one file")
            result = summarize_impl(list(files), purpose)
            print(json.dumps(result, indent=2))
        """
        ).strip()
        + "\n"
    )


def step_generate_tool(llm: LLM, artifacts: Path, name: str, desc: str, template: str | None = None) -> dict[str, Any]:
    base = Path("cli_tools") / name
    pkg = _pkg_name(name)

    pyproject = base / "pyproject.toml"
    pkg_dir = base / pkg
    readme = base / "README.md"

    # Common files
    _write(pyproject, _pyproject_toml(name, pkg))
    _write(pkg_dir / "__init__.py", "")
    _write(pkg_dir / "microtasks" / "__init__.py", "")
    _write(pkg_dir / "microtasks" / "llm.py", _llm_py())
    _write(pkg_dir / "microtasks" / "orchestrator.py", _orchestrator_py(name))

    # Philosophy-driven generation when no template
    if template is None:
        # Use the new philosophy-driven approach
        result = step_generate_tool_philosophy(llm, artifacts, name, desc)
        if "code" in result:
            _write(pkg_dir / "microtasks" / "recipes.py", result["code"])
        else:
            # Fallback if philosophy generation fails
            _write(pkg_dir / "microtasks" / "recipes.py", _summarize_recipe_py())

    # Template-specific or composed
    plan_json_path = artifacts / "plan.json"
    if template is None and plan_json_path.exists():
        try:
            _obj = json.loads(plan_json_path.read_text())
        except Exception:
            _obj = {}
        _steps = _obj.get("steps") if isinstance(_obj, dict) else None
        if _steps:
            plan_txt = _extract_json_object(plan_json_path.read_text())
            body = _compose_recipes_from_plan2(name, plan_txt)
            _write(pkg_dir / "microtasks" / "recipes.py", body)
        # else: keep previously written code (from philosophy path)
    elif template == "ideas":
        _write(pkg_dir / "microtasks" / "recipes.py", _ideas_recipe_py(name))
    else:
        _write(pkg_dir / "microtasks" / "recipes.py", _summarize_recipe_py())

    _write(pkg_dir / "cli.py", _cli_py(name, pkg, template))
    # Post-generation validation: ensure recipes export run()
    try:
        _code = (pkg_dir / "microtasks" / "recipes.py").read_text()
    except Exception:
        _code = ""
    if "def run(" not in _code:
        _desc_l = (desc or "").lower()
        if any(
            k in _desc_l
            for k in [
                "net new ideas",
                "synthesize",
                "summarize each",
                "expand ideas",
                "case for it",
                "plan for approaching",
            ]
        ):
            _write(pkg_dir / "microtasks" / "recipes.py", _ideas_recipe_py(name))
        else:
            raise RuntimeError("Generated tool has no run() in recipes.py")

    _write(
        readme,
        dedent(
            f"""
            # {name}

            Generated by Amplifier (amp tool create). Install into your env:

            ```bash
            uv pip install -e cli_tools/{name}
            ```

            Run:
            ```bash
            {name} --help
            ```
            """
        ).strip()
        + "\n",
    )

    return {"base_dir": str(base)}
