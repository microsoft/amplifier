"""Generate an interactive HTML dashboard for terminal-bench evaluation runs."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

DEFAULT_DASHBOARD_TITLE = "Terminal-Bench Evaluation Dashboard"


@dataclass
class TaskReport:
    task_id: str
    is_resolved: bool
    failure_mode: str | None
    parser_results: dict[str, str] | None
    markdown_path: Path | None
    markdown_content: str | None
    instruction: str | None


@dataclass
class RunData:
    run_id: str
    agent_name: str | None
    accuracy: float | None
    start_time: str | None
    end_time: str | None
    n_tasks: int
    n_resolved: int
    n_unresolved: int
    run_dir: Path
    consolidated_report: str | None
    task_reports: list[TaskReport]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an HTML dashboard comparing terminal-bench evaluation runs.")
    parser.add_argument(
        "run_dirs",
        nargs="+",
        type=Path,
        help="One or more directories containing terminal-bench run outputs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("terminal_bench_dashboard.html"),
        help="Path to write the generated HTML dashboard (default: ./terminal_bench_dashboard.html).",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=DEFAULT_DASHBOARD_TITLE,
        help="Title for the dashboard page.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Expected JSON file missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_run(run_dir: Path) -> RunData:
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    run_metadata = load_json(run_dir / "run_metadata.json")
    results_data = load_json(run_dir / "results.json")
    consolidated_report = read_text_if_exists(run_dir / "CONSOLIDATED_REPORT.md")

    task_lookup: dict[str, TaskReport] = {}
    for result in results_data.get("results", []):
        task_id = result.get("task_id")
        if not task_id:
            continue
        parser_results = result.get("parser_results") or None
        if parser_results is not None:
            parser_results = {str(key): str(value) for key, value in parser_results.items()}
        task_lookup[task_id] = TaskReport(
            task_id=task_id,
            is_resolved=bool(result.get("is_resolved")),
            failure_mode=result.get("failure_mode"),
            parser_results=parser_results,
            markdown_path=None,
            markdown_content=None,
            instruction=result.get("instruction"),
        )

    reports_dir = run_dir / "task_reports"
    if reports_dir.exists():
        for report_path in sorted(reports_dir.glob("*_report.md")):
            task_id = report_path.name.removesuffix("_report.md")
            markdown_content = read_text_if_exists(report_path)
            report = task_lookup.get(task_id)
            if report is None:
                report = TaskReport(
                    task_id=task_id,
                    is_resolved=False,
                    failure_mode=None,
                    parser_results=None,
                    markdown_path=report_path,
                    markdown_content=markdown_content,
                    instruction=None,
                )
                task_lookup[task_id] = report
            else:
                report.markdown_path = report_path
                report.markdown_content = markdown_content

    task_reports = sorted(task_lookup.values(), key=lambda item: item.task_id)

    return RunData(
        run_id=str(run_metadata.get("run_id", run_dir.name)),
        agent_name=run_metadata.get("agent_name"),
        accuracy=run_metadata.get("accuracy"),
        start_time=run_metadata.get("start_time"),
        end_time=run_metadata.get("end_time"),
        n_tasks=len(results_data.get("results", [])),
        n_resolved=int(results_data.get("n_resolved", 0)),
        n_unresolved=int(results_data.get("n_unresolved", 0)),
        run_dir=run_dir,
        consolidated_report=consolidated_report,
        task_reports=task_reports,
    )


def format_accuracy(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def format_timestamp(value: str | None) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value)
        base = dt.strftime("%Y-%m-%d %H:%M:%S")
        if dt.tzinfo:
            offset = dt.tzinfo.utcoffset(dt)
            if offset is not None:
                hours, remainder = divmod(int(offset.total_seconds()), 3600)
                minutes = remainder // 60
                sign = "+" if hours >= 0 else "-"
                return f"{base} UTC{sign}{abs(hours):02d}:{abs(minutes):02d}"
        return base
    except ValueError:
        return value


def build_run_summary_html(run: RunData) -> str:
    accuracy_text = format_accuracy(run.accuracy)
    start_text = format_timestamp(run.start_time)
    end_text = format_timestamp(run.end_time)
    start_iso = escape(run.start_time) if run.start_time else ""
    end_iso = escape(run.end_time) if run.end_time else ""

    return """
        <div class="run-summary">
          <div class="metric">
            <span class="metric-label">Agent</span>
            <span class="metric-value">{agent}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Tasks</span>
            <span class="metric-value">{tasks}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Resolved</span>
            <span class="metric-value resolved">{resolved}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Unresolved</span>
            <span class="metric-value unresolved">{unresolved}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Accuracy</span>
            <span class="metric-value">{accuracy}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Start</span>
            <span class="metric-value monospace datetime" data-iso="{start_iso}">{start}</span>
          </div>
          <div class="metric">
            <span class="metric-label">End</span>
            <span class="metric-value monospace datetime" data-iso="{end_iso}">{end}</span>
          </div>
        </div>
    """.format(
        agent=escape(run.agent_name or "—"),
        tasks=run.n_tasks,
        resolved=run.n_resolved,
        unresolved=run.n_unresolved,
        accuracy=accuracy_text,
        start=escape(start_text),
        end=escape(end_text),
        start_iso=start_iso,
        end_iso=end_iso,
    )


def build_consolidated_report_html(run: RunData, run_index: int) -> str:
    if not run.consolidated_report:
        return '<p class="empty-state">No consolidated report found.</p>'
    textarea_id = f"consolidated-{run_index}"
    return """
        <div class="markdown-block" data-source="{textarea_id}">
          <textarea id="{textarea_id}" class="markdown-source" hidden>{content}</textarea>
          <div class="markdown-render"></div>
        </div>
    """.format(
        textarea_id=escape(textarea_id),
        content=escape(run.consolidated_report),
    )


def build_parser_results_table(parser_results: dict[str, str]) -> str:
    rows = []
    for key, value in sorted(parser_results.items()):
        rows.append(
            f"""
            <tr>
              <td class="monospace">{escape(key)}</td>
              <td class="monospace">{escape(value)}</td>
            </tr>
            """
        )
    return '<table class="parser-results"><tbody>{}</tbody></table>'.format("".join(rows))


def build_task_report_html(run: RunData, report: TaskReport, run_index: int, task_index: int) -> str:
    textarea_id = f"task-{run_index}-{task_index}"
    status_text = "Resolved" if report.is_resolved else "Unresolved"
    failure_text = report.failure_mode or "—"
    instruction_html = (
        """
        <div class="instruction-block">
          <span class="instruction-label">Instruction</span>
          <pre>{instruction}</pre>
        </div>
        """.format(
            instruction=escape(report.instruction or "Not available"),
        )
        if report.instruction
        else ""
    )

    parser_results_html = build_parser_results_table(report.parser_results) if report.parser_results else ""

    markdown_source = report.markdown_content or "No task report available."
    markdown_section = """
        <div class="markdown-block" data-source="{textarea_id}">
          <textarea id="{textarea_id}" class="markdown-source" hidden>{content}</textarea>
          <div class="markdown-render"></div>
        </div>
    """.format(
        textarea_id=escape(textarea_id),
        content=escape(markdown_source),
    )

    return """
        <details class="task-report">
          <summary>
            <span class="task-id">{task_id}</span>
            <span class="task-status {status_class}">{status}</span>
            <span class="task-failure">{failure}</span>
          </summary>
          <div class="task-body">
            {instruction}
            {parser_results}
            {markdown}
          </div>
        </details>
    """.format(
        task_id=escape(report.task_id),
        status=escape(status_text),
        status_class="resolved" if report.is_resolved else "unresolved",
        failure=escape(failure_text),
        instruction=instruction_html,
        parser_results=parser_results_html,
        markdown=markdown_section,
    )


def build_run_tab_html(run: RunData, run_index: int, *, active: bool) -> str:
    summary_html = build_run_summary_html(run)
    consolidated_html = build_consolidated_report_html(run, run_index)

    task_sections = [build_task_report_html(run, report, run_index, idx) for idx, report in enumerate(run.task_reports)]

    tasks_html = (
        """
        <div class="empty-state">No task reports found for this run.</div>
        """
        if not task_sections
        else "".join(task_sections)
    )

    classes = "tab-content"
    if active:
        classes += " active"

    return """
        <div class="{classes}" data-run="{run_id}">
          <section>
            <h2>{run_id}</h2>
            {summary}
          </section>
          <section>
            <details class="consolidated-report">
              <summary>Consolidated Report</summary>
              {consolidated}
            </details>
          </section>
          <section>
            <h3>Task Reports</h3>
            <p class="hint">Task details open on click.</p>
            {tasks}
          </section>
        </div>
    """.format(
        classes=classes,
        run_id=escape(run.run_id),
        summary=summary_html,
        consolidated=consolidated_html,
        tasks=tasks_html,
    )


def build_tabs_nav(runs: list[RunData]) -> str:
    buttons = []
    for idx, run in enumerate(runs):
        classes = "tab-button"
        if idx == 0:
            classes += " active"
        buttons.append(
            f"""
            <button class="{classes}" data-run="{escape(run.run_id)}" type="button">{escape(run.run_id)}</button>
            """
        )
    return '<div class="tabs">{}</div>'.format("".join(buttons))


def build_full_html(runs: list[RunData], title: str) -> str:
    tabs_nav = build_tabs_nav(runs)
    tabs_content = "".join(build_run_tab_html(run, idx, active=(idx == 0)) for idx, run in enumerate(runs))

    css = """
    :root {
      color-scheme: light dark;
      --background: #f3f4f6;
      --surface: #ffffff;
      --surface-dark: #202124;
      --text: #1f2933;
      --text-muted: #4b5563;
      --resolved: #0f9d58;
      --unresolved: #d93025;
      --border: #d1d5db;
      --shadow: rgba(15, 23, 42, 0.08);
      font-family: "Inter", "Segoe UI", sans-serif;
    }

    body {
      margin: 0;
      padding: 2rem;
      background: var(--background);
      color: var(--text);
    }

    h1 {
      margin-top: 0;
      margin-bottom: 1rem;
      font-size: 2rem;
    }

    h2 {
      margin-top: 0;
      font-size: 1.5rem;
    }

    h3 {
      font-size: 1.25rem;
      margin-bottom: 0.5rem;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
    }

    .tabs {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
    }

    .tab-button {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 0.5rem 1.25rem;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 0.95rem;
      box-shadow: 0 1px 2px var(--shadow);
    }

    .tab-button:hover,
    .tab-button:focus {
      outline: none;
      transform: translateY(-1px);
    }

    .tab-button.active {
      background: #2563eb;
      border-color: #2563eb;
      color: #fff;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    .tab-content {
      display: none;
      background: var(--surface);
      border-radius: 16px;
      padding: 1.5rem 2rem;
      box-shadow: 0 10px 30px var(--shadow);
      border: 1px solid var(--border);
      margin-bottom: 2rem;
    }

    .tab-content.active {
      display: block;
    }

    .run-summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .metric {
      background: rgba(37, 99, 235, 0.05);
      border-radius: 12px;
      padding: 0.75rem 1rem;
    }

    .metric-label {
      display: block;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      margin-bottom: 0.25rem;
    }

    .metric-value {
      font-size: 1.1rem;
      font-weight: 600;
    }

    .metric-value.resolved {
      color: var(--resolved);
    }

    .metric-value.unresolved {
      color: var(--unresolved);
    }

    .monospace {
      font-family: "JetBrains Mono", "SFMono-Regular", ui-monospace, monospace;
      font-size: 0.9rem;
    }

    .hint {
      color: var(--text-muted);
      margin-top: 0;
      font-size: 0.9rem;
    }

    .empty-state {
      color: var(--text-muted);
      font-style: italic;
      padding: 1rem;
      background: rgba(148, 163, 184, 0.15);
      border-radius: 12px;
    }

    details.task-report {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0.75rem 1rem;
      margin-bottom: 0.75rem;
      background: rgba(255, 255, 255, 0.75);
    }

    details.consolidated-report {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0.75rem 1rem;
      background: rgba(255, 255, 255, 0.75);
      margin-bottom: 1.25rem;
    }

    details.task-report summary {
      display: flex;
      align-items: center;
      gap: 1rem;
      cursor: pointer;
      list-style: none;
    }

    details.task-report summary::-webkit-details-marker {
      display: none;
    }

    details.consolidated-report summary {
      cursor: pointer;
      font-weight: 600;
      list-style: none;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    details.consolidated-report summary::-webkit-details-marker {
      display: none;
    }

    details.consolidated-report[open] .markdown-block,
    details.consolidated-report[open] .empty-state {
      margin-top: 0.75rem;
      display: block;
    }

    .task-id {
      font-weight: 600;
      flex: 1 1 auto;
    }

    .task-status {
      font-size: 0.85rem;
      font-weight: 600;
      padding: 0.25rem 0.75rem;
      border-radius: 999px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .task-status.resolved {
      background: rgba(15, 157, 88, 0.15);
      color: var(--resolved);
    }

    .task-status.unresolved {
      background: rgba(217, 48, 37, 0.15);
      color: var(--unresolved);
    }

    .task-failure {
      color: var(--text-muted);
      font-size: 0.9rem;
    }

    .task-body {
      padding-top: 1rem;
      border-top: 1px solid var(--border);
      margin-top: 0.75rem;
      display: grid;
      gap: 1rem;
      overflow-x: auto;
    }

    .markdown-render {
      font-size: 0.95rem;
      line-height: 1.55;
      width: 100%;
      box-sizing: border-box;
    }

    .markdown-render > * {
      max-width: 100%;
      box-sizing: border-box;
    }

    .markdown-render pre {
      background: #0f172a;
      color: #e2e8f0;
      padding: 1rem;
      border-radius: 10px;
      overflow-x: auto;
      margin: 0;
    }

    .markdown-render code {
      font-family: "JetBrains Mono", "SFMono-Regular", ui-monospace, monospace;
    }

    .parser-results {
      width: 100%;
      border-collapse: collapse;
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }

    .parser-results td {
      border-bottom: 1px solid var(--border);
      padding: 0.35rem 0.5rem;
    }

    .instruction-block {
      background: rgba(15, 23, 42, 0.06);
      border-radius: 10px;
      padding: 0.75rem 1rem;
    }

    .instruction-label {
      display: block;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      margin-bottom: 0.4rem;
    }

    .instruction-block pre {
      white-space: pre-wrap;
      margin: 0;
      font-family: "Inter", "Segoe UI", sans-serif;
      font-size: 0.95rem;
    }

    @media (prefers-color-scheme: dark) {
      body {
        background: #111827;
        color: #e5e7eb;
      }
      .tab-button {
        background: #1f2937;
        border-color: #374151;
        color: #e5e7eb;
      }
      .tab-content {
        background: #1f2937;
        border-color: #374151;
        box-shadow: none;
      }
      .metric {
        background: rgba(59, 130, 246, 0.15);
      }
      .empty-state {
        background: rgba(148, 163, 184, 0.1);
      }
      details.task-report {
        background: #111827;
        border-color: #374151;
      }
      .instruction-block {
        background: rgba(59, 130, 246, 0.15);
      }
    }
    """

    script = """
    document.addEventListener("DOMContentLoaded", () => {
      const buttons = document.querySelectorAll(".tab-button");
      const tabs = document.querySelectorAll(".tab-content");

      buttons.forEach((button) => {
        button.addEventListener("click", () => {
          const run = button.dataset.run;
          buttons.forEach((btn) => btn.classList.toggle("active", btn === button));
          tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.run === run));
        });
      });

      const formatDateTimes = () => {
        const formatter = new Intl.DateTimeFormat(undefined, {
          year: "numeric",
          month: "short",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });

        document.querySelectorAll(".datetime[data-iso]").forEach((element) => {
          const iso = element.dataset.iso;
          if (!iso) {
            return;
          }
          const date = new Date(iso);
          if (Number.isNaN(date.valueOf())) {
            return;
          }
          element.textContent = formatter.format(date);
          element.title = `${date.toISOString()} (${Intl.DateTimeFormat().resolvedOptions().timeZone})`;
        });
      };

      const renderMarkdown = () => {
        document.querySelectorAll(".markdown-block").forEach((block) => {
          const sourceId = block.dataset.source;
          const textarea = document.getElementById(sourceId);
          const target = block.querySelector(".markdown-render");
          if (!textarea || !target) {
            return;
          }
          const raw = textarea.value;
          if (window.marked) {
            target.innerHTML = window.marked.parse(raw);
          } else {
            const fallback = document.createElement("pre");
            fallback.textContent = raw;
            target.appendChild(fallback);
          }
        });
      };

      formatDateTimes();
      renderMarkdown();
    });
    """

    return """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{title}</title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js" defer></script>
        <style>{css}</style>
      </head>
      <body>
        <div class="container">
          <h1>{title}</h1>
          {tabs_nav}
          {tabs_content}
        </div>
        <script>{script}</script>
      </body>
    </html>
    """.format(
        title=escape(title),
        css=css,
        tabs_nav=tabs_nav,
        tabs_content=tabs_content,
        script=script,
    )


def generate_dashboard(
    run_dirs: Sequence[Path] | Iterable[Path],
    output_path: Path,
    *,
    title: str = DEFAULT_DASHBOARD_TITLE,
) -> Path:
    """Render the evaluation dashboard for the provided run directories."""

    resolved_dirs = [Path(run_dir).resolve() for run_dir in run_dirs]
    if not resolved_dirs:
        raise ValueError("At least one run directory is required to build the dashboard.")

    runs = [load_run(run_dir) for run_dir in resolved_dirs]
    html_content = build_full_html(runs, title)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


def main() -> None:
    args = parse_args()
    output_path = generate_dashboard(args.run_dirs, args.output, title=args.title)
    print(f"Dashboard written to {output_path}")


if __name__ == "__main__":
    main()
