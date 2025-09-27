"""
YAML storage layer with defensive file I/O patterns.

Handles atomic saves, backup creation, and retry logic for cloud sync issues.
Following the single source of truth pattern with robust error handling.
"""

import shutil
import time
from pathlib import Path

import yaml
from filelock import FileLock

from amplifier.ideas.models import IdeasDocument


class IdeasStorage:
    """
    Storage layer for ideas documents with defensive patterns.

    Handles the "brick" of data persistence with atomic operations,
    cloud sync resilience, and backup management.
    """

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.lockfile = Path(f"{filepath}.lock")
        self.backup_dir = self.filepath.parent / "backups"

        # Ensure directories exist
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def load(self) -> IdeasDocument:
        """
        Load ideas document from YAML file with retry logic.

        Returns empty document if file doesn't exist.
        Retries on cloud sync delays (OneDrive, Dropbox, etc.)
        """
        if not self.filepath.exists():
            return IdeasDocument()

        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                with open(self.filepath, encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data is None:  # Empty file
                    return IdeasDocument()

                return IdeasDocument(**data)

            except OSError as e:
                if e.errno == 5 and attempt < max_retries - 1:  # I/O error, likely cloud sync
                    if attempt == 0:
                        print(f"⚠️  File I/O delay loading {self.filepath} - retrying...")
                        print("    This may be due to cloud sync (OneDrive, Dropbox, etc.)")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {self.filepath}: {e}")
            except Exception as e:
                raise RuntimeError(f"Failed to load ideas from {self.filepath}: {e}")

        raise RuntimeError(f"Failed to load after {max_retries} attempts")

    def save(self, doc: IdeasDocument, user: str = "system") -> None:
        """
        Atomic save with backup and retry logic.

        Creates backup of existing file before writing.
        Uses temp file + rename for atomicity.
        Retries on cloud sync issues.
        """
        # Update metadata
        doc.update_metadata(user)

        max_retries = 3
        retry_delay = 1.0

        with FileLock(self.lockfile, timeout=10):
            # Create backup of existing file
            if self.filepath.exists():
                backup_path = self._create_backup()
                if backup_path:
                    print(f"💾 Backed up to {backup_path.name}")

            # Atomic write with retry
            temp_file = self.filepath.with_suffix(".tmp")

            for attempt in range(max_retries):
                try:
                    # Convert to dict and write to temp file
                    data = doc.model_dump(mode="json")

                    with open(temp_file, "w", encoding="utf-8") as f:
                        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True, indent=2)
                        f.flush()

                    # Atomic rename
                    temp_file.replace(self.filepath)
                    return

                except OSError as e:
                    if e.errno == 5 and attempt < max_retries - 1:  # I/O error
                        if attempt == 0:
                            print(f"⚠️  File I/O delay saving {self.filepath} - retrying...")
                            print("    This may be due to cloud sync (OneDrive, Dropbox, etc.)")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    # Clean up temp file on error
                    if temp_file.exists():
                        temp_file.unlink()
                    raise
                except Exception as e:
                    # Clean up temp file on error
                    if temp_file.exists():
                        temp_file.unlink()
                    raise RuntimeError(f"Failed to save ideas to {self.filepath}: {e}")

        raise RuntimeError(f"Failed to save after {max_retries} attempts")

    def backup(self) -> Path | None:
        """Create a timestamped backup of the current file"""
        return self._create_backup()

    def _create_backup(self) -> Path | None:
        """Create backup with timestamp"""
        if not self.filepath.exists():
            return None

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{self.filepath.stem}_{timestamp}.yaml"

        try:
            shutil.copy2(self.filepath, backup_path)
            # Keep only last 10 backups
            self._cleanup_old_backups()
            return backup_path
        except Exception as e:
            print(f"⚠️  Warning: Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self, keep: int = 10) -> None:
        """Remove old backup files, keeping only the most recent"""
        try:
            backups = list(self.backup_dir.glob(f"{self.filepath.stem}_*.yaml"))
            if len(backups) > keep:
                # Sort by modification time, remove oldest
                backups.sort(key=lambda p: p.stat().st_mtime)
                for old_backup in backups[:-keep]:
                    old_backup.unlink()
        except Exception:
            pass  # Backup cleanup is not critical

    def exists(self) -> bool:
        """Check if the ideas file exists"""
        return self.filepath.exists()

    def get_filepath(self) -> Path:
        """Get the full file path"""
        return self.filepath

    def get_backup_dir(self) -> Path:
        """Get the backup directory path"""
        return self.backup_dir


def get_default_ideas_file() -> Path:
    """
    Get the default ideas file path.

    Uses environment variable AMPLIFIER_IDEAS_FILE if set,
    otherwise defaults to ~/amplifier/ideas.yaml
    """
    import os

    # Check environment variable first
    env_path = os.getenv("AMPLIFIER_IDEAS_FILE")
    if env_path:
        return Path(env_path).expanduser()

    # Default to home directory
    return Path.home() / "amplifier" / "ideas.yaml"


def create_sample_document() -> IdeasDocument:
    """Create a sample ideas document for testing"""
    from amplifier.ideas.models import Goal
    from amplifier.ideas.models import Idea

    doc = IdeasDocument()

    # Add sample goals
    doc.add_goal(Goal(description="Focus on improving user experience and onboarding", priority=1))

    doc.add_goal(Goal(description="Reduce technical debt and improve system reliability", priority=2))

    # Add sample ideas
    idea1 = Idea(
        title="Add dark mode toggle",
        description="Implement theme switching with user preference persistence",
        themes=["ui", "ux"],
        priority="high",
    )
    doc.add_idea(idea1)

    idea2 = Idea(
        title="Implement caching layer",
        description="Add Redis caching for frequently accessed data to improve performance",
        themes=["performance", "infrastructure"],
        priority="medium",
    )
    doc.add_idea(idea2)

    idea3 = Idea(
        title="Create user onboarding tutorial",
        description="Step-by-step walkthrough for new users",
        themes=["onboarding", "ux"],
        priority="high",
    )
    doc.add_idea(idea3)

    # Assign some ideas
    doc.assign_idea(idea1.id, "alice")
    doc.assign_idea(idea2.id, "bob")
    # idea3 remains unassigned

    return doc
