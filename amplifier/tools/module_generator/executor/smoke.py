"""Helpers for post-generation smoke testing."""

from __future__ import annotations

import asyncio
import sys

from ..plan_models import GenContext


async def run_sample_script(ctx: GenContext) -> tuple[bool, str]:
    """Execute the module's sample script if it exists.

    Returns a tuple of (success, combined_output). When the script is missing the
    function returns (True, "") so generation can continue without blocking.
    """
    script_path = ctx.repo_root / "scripts" / f"run_{ctx.module_name}_sample.py"
    if not script_path.exists():
        return True, ""

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script_path),
        cwd=str(ctx.repo_root),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = await proc.communicate()
    combined = (stdout_bytes or b"") + (b"\n" if stdout_bytes and stderr_bytes else b"") + (stderr_bytes or b"")
    combined_text = combined.decode("utf-8", errors="replace")
    return proc.returncode == 0, combined_text.strip()
