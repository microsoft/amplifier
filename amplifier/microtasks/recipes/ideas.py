"""
Batch Ideation Recipe

Implements the 4-step pipeline:
1) Discover first N markdown files from a source dir
2) Summarize each (skip existing summaries) to a working dir
3) Synthesize net-new ideas across summaries, with per-idea sources
4) Expand each idea using relevant sources (skip existing)

All steps write to disk incrementally to support resume.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..llm import LLM


@dataclass
class IdeasConfig:
    src_dir: Path
    limit: int = 5
    work_dir: Path = Path(".data/ideas_work")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def step_discover(_: LLM, artifacts: Path, cfg: IdeasConfig) -> dict[str, Any]:
    files = sorted(Path(cfg.src_dir).glob("*.md"))[: cfg.limit]
    listing = artifacts / "discover.json"
    listing.write_text(json.dumps([str(p) for p in files], indent=2), encoding="utf-8")
    return {"count": len(files), "files": [str(p) for p in files]}


def step_summarize_each(llm: LLM, artifacts: Path, cfg: IdeasConfig) -> dict[str, Any]:
    listing = json.loads((artifacts / "discover.json").read_text())
    files = [Path(p) for p in listing]
    summaries_dir = cfg.work_dir / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)
    summary_index = []
    total = len(files)
    status_path = artifacts / "status.json"
    for i, p in enumerate(files, 1):
        out = summaries_dir / f"{p.stem}.summary.md"
        if out.exists():
            summary_index.append(str(out))
            status_path.write_text(json.dumps({"stage": "summarize_each", "done": i, "total": total, "file": str(p)}))
            continue
        prompt = "Summarize the following markdown with key points and actionable insights.\n\n" + _load_text(p)
        summary = llm.complete(
            prompt,
            system="You are a concise analyst. Return a markdown bullet list of 5-10 key points. No preamble.",
        )
        bad_patterns = ["i'll", "i will", "let me", "i am going to", "i'm going to"]
        if len(summary.strip()) < 120 or any(pat in summary.lower() for pat in bad_patterns):
            prompt2 = (
                "Rewrite the summary as a markdown bullet list of 5-10 concrete points.\n"
                "Avoid meta-commentary (e.g., 'I'll do X'). Provide content only.\n\n" + _load_text(p)
            )
            summary = llm.complete(prompt2, system="You write concise, content-only summaries.")
        _write(out, summary)
        summary_index.append(str(out))
        status_path.write_text(json.dumps({"stage": "summarize_each", "done": i, "total": total, "file": str(p)}))
        print(f"[summarize] {i}/{total}: {p.name}")
    (artifacts / "summaries.json").write_text(json.dumps(summary_index, indent=2))
    return {"summaries": summary_index}


def step_synthesize_ideas(llm: LLM, artifacts: Path, cfg: IdeasConfig) -> dict[str, Any]:
    summaries = json.loads((artifacts / "summaries.json").read_text())
    docs = []
    for s in summaries:
        docs.append({"path": s, "text": _load_text(Path(s))})

    def _extract_json_array(text: str) -> list:
        import re

        m = re.search(r"```json\n(.*?)```", text, flags=re.S | re.I)
        block = m.group(1) if m else None
        if not block:
            s = text.find("[")
            e = text.rfind("]")
            if s != -1 and e != -1 and e > s:
                block = text[s : e + 1]
        if not block:
            return []
        try:
            return json.loads(block)
        except Exception:
            return []

    allowed = [d["path"] for d in docs]
    prompt = (
        "You are an idea synthesizer. From the following set of summaries, propose net-new ideas that\n"
        "emerge by combining insights across documents (not stated explicitly in any single file).\n"
        'Return ONLY a JSON array with objects of the form: {"title": string, "rationale": string, "sources": [string]}.\n'
        "Pick sources ONLY from this allowed list (use exact strings):\n"
        + json.dumps(allowed)
        + "\n\n"
        + json.dumps(docs)[:90000]
    )
    raw = llm.complete(prompt, system="You combine insights across documents and output strict JSON.")
    ideas = _extract_json_array(raw)
    # Filter/repair sources to allowed list
    fixed = []
    for it in ideas or []:
        srcs = [s for s in (it.get("sources") or []) if s in allowed]
        it["sources"] = srcs
        fixed.append(it)
    ideas = fixed
    if not ideas:
        strict = (
            "Return ONLY a valid JSON array with at least 3 items, using sources ONLY from this allowed list:\n"
            + json.dumps(allowed)
        )
        raw2 = llm.complete(strict, system="You return strict JSON only.")
        ideas = _extract_json_array(raw2)
        fixed = []
        for it in ideas or []:
            srcs = [s for s in (it.get("sources") or []) if s in allowed]
            it["sources"] = srcs
            fixed.append(it)
        ideas = fixed
    (artifacts / "ideas.json").write_text(json.dumps(ideas, indent=2), encoding="utf-8")
    print(f"[ideas] synthesized: {len(ideas)}")
    return {"ideas_count": len(ideas)}


def step_expand_ideas(llm: LLM, artifacts: Path, cfg: IdeasConfig) -> dict[str, Any]:
    sources_dir = Path(cfg.src_dir)
    ideas = json.loads((artifacts / "ideas.json").read_text())
    out_dir = cfg.work_dir / "ideas"
    out_dir.mkdir(parents=True, exist_ok=True)
    expanded = 0
    total = len(ideas)
    status_path = artifacts / "status.json"

    def _map_source_to_original(src: str) -> Path:
        p = Path(src)
        # If this is a summary file, map back to original source by basename
        if p.name.endswith(".summary.md"):
            candidate = sources_dir / p.name.replace(".summary.md", ".md")
            if candidate.exists():
                return candidate
        # If absolute path exists, use it
        if p.exists():
            return p
        # Fallback to same name under sources_dir
        q = sources_dir / p.name
        return q if q.exists() else p

    for idx, idea in enumerate(ideas, 1):
        title = idea.get("title") or f"idea_{idx:03d}"
        outfile = out_dir / f"{title.replace(' ', '_').lower()}.md"
        if outfile.exists():
            status_path.write_text(
                json.dumps({"stage": "expand_ideas", "done": idx, "total": total, "title": title, "skipped": True})
            )
            continue
        srcs = [_map_source_to_original(p) for p in idea.get("sources", [])]
        body = ("\n\n".join(_load_text(p) for p in srcs if p and p.exists()))[:120000]
        prompt = (
            f"Idea: {title}\n\nRationale: {idea.get('rationale', '')}\n\n"
            "Given the relevant source excerpts below, write a persuasive, well-structured case for this idea and a concrete plan of action.\n"
            "Include: context, benefits, risks, and a step-by-step plan.\n\n"
            "Relevant sources (may be partial excerpts):\n" + body
        )
        text = llm.complete(
            prompt,
            system="You are a pragmatic strategist. Use clear headings and cite sources by filename where relevant.",
        )
        needs_fix = (
            ("## Context" not in text)
            or ("## Benefits" not in text)
            or ("## Risks" not in text)
            or ("## Plan" not in text)
            or (len(text) < 600)
        )
        if needs_fix:
            critique = llm.complete(
                "Critique the draft. List missing required sections and weak areas. Then propose concrete fixes.",
                system="You are an analysis expert.",
            )
            text = llm.complete(
                "Improve the draft by applying the critique. Return only the improved markdown. Ensure all required sections exist.\n\n"
                f"Critique:\n{critique}\n\nDraft to improve:\n{text}",
                system="You are a synthesis master.",
            )
        _write(outfile, text)
        expanded += 1
        status_path.write_text(json.dumps({"stage": "expand_ideas", "done": idx, "total": total, "title": title}))
        print(f"[expand] {idx}/{total}: {title}")
    return {"expanded": expanded}


def run_ideas_recipe(src_dir: str, limit: int = 5, work_dir: str | None = None, progress=None) -> dict[str, Any]:
    from ..orchestrator import MicrotaskOrchestrator

    cfg = IdeasConfig(
        src_dir=Path(src_dir), limit=limit, work_dir=Path(work_dir) if work_dir else Path(".data/ideas_work")
    )
    orch = MicrotaskOrchestrator()

    def _discover(llm: LLM, art: Path) -> dict[str, Any]:
        return step_discover(llm, art, cfg)

    def _sum(llm: LLM, art: Path) -> dict[str, Any]:
        return step_summarize_each(llm, art, cfg)

    def _ideate(llm: LLM, art: Path) -> dict[str, Any]:
        return step_synthesize_ideas(llm, art, cfg)

    def _expand(llm: LLM, art: Path) -> dict[str, Any]:
        return step_expand_ideas(llm, art, cfg)

    steps = [
        ("discover", _discover),
        ("summarize_each", _sum),
        ("synthesize_ideas", _ideate),
        ("expand_ideas", _expand),
    ]
    summary = orch.run(
        "ideas",
        steps,
        meta={"src_dir": str(cfg.src_dir), "limit": cfg.limit, "work_dir": str(cfg.work_dir)},
        fail_fast=True,
        on_event=progress,
    )
    return summary.model_dump()
