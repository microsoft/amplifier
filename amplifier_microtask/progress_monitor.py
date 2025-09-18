"""
Module: progress_monitor

Purpose: Track SDK operation progress without disrupting execution

Contract:
  Inputs: task_id, stage_name, timeout
  Outputs: Progress updates via file-based heartbeat
  Side Effects: Writes to .progress_{task_id}.txt file
"""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional


class ProgressMonitor:
    """Monitor progress of long-running SDK operations via file-based heartbeat."""

    def __init__(self, task_id: str, stage_name: str):
        """Initialize progress monitor.

        Args:
            task_id: Unique identifier for the task
            stage_name: Name of the current stage being executed
        """
        self.task_id = task_id
        self.stage_name = stage_name
        self.progress_file = Path(f".progress_{task_id}.txt")
        self.monitor_task: Optional[asyncio.Task] = None

    def start(self):
        """Start progress monitoring by creating initial progress file."""
        self.progress_file.write_text(f"{datetime.now()}: Starting {self.stage_name}\n")

    async def monitor_heartbeat(self, check_interval: int = 30):
        """Monitor for heartbeat updates in the background.

        Args:
            check_interval: Seconds between progress checks
        """
        last_size = 0
        last_update = datetime.now()

        while True:
            try:
                if self.progress_file.exists():
                    current_size = self.progress_file.stat().st_size
                    if current_size != last_size:
                        print(f"  📍 Progress: {self.stage_name} still active ({current_size} bytes)")
                        last_size = current_size
                        last_update = datetime.now()
                    elif (datetime.now() - last_update).seconds > 120:
                        print(f"  ⚠️  Warning: No progress for 2 minutes in {self.stage_name}")

                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Silently handle other errors to avoid disrupting main execution
                print(f"  ⚠️  Progress monitor error: {e}")
                await asyncio.sleep(check_interval)

    def update(self, message: str):
        """Update progress with a message.

        Args:
            message: Progress message to append to file
        """
        try:
            with self.progress_file.open("a") as f:
                f.write(f"{datetime.now()}: {message}\n")
        except Exception:
            # Silently ignore write errors to avoid disrupting main execution
            pass

    def cleanup(self):
        """Clean up progress file."""
        if self.progress_file.exists():
            try:
                self.progress_file.unlink()
            except Exception:
                # Silently ignore cleanup errors
                pass
