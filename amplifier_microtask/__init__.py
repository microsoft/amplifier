"""
Amplifier Microtask - Microtask-driven AI operations with the Amplifier pattern
"""

from .storage import save_json, load_json, append_jsonl, ensure_directory
from .session import Session, SessionInfo, create_session, load_session, save_checkpoint
from .agent import execute_task_sync, check_sdk_available
from .orchestrator import Task, TaskResult, run_pipeline_sync

__version__ = "0.1.0"

__all__ = [
    # Storage
    "save_json",
    "load_json",
    "append_jsonl",
    "ensure_directory",
    # Session
    "Session",
    "SessionInfo",
    "create_session",
    "load_session",
    "save_checkpoint",
    # Agent
    "execute_task_sync",
    "check_sdk_available",
    # Orchestrator
    "Task",
    "TaskResult",
    "run_pipeline_sync",
]
