import subprocess
import uuid
from datetime import datetime
from pathlib import Path


def get_repo_name() -> str:
    """Get the current repository name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_path = Path(result.stdout.strip())
        return repo_path.name
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Not a git repository or git command failed: {e}")


def generate_worktree_name(prd_name: str) -> tuple[str, str]:
    """Generate a formatted worktree name and unique ID.

    Args:
        prd_name: The PRD name/number (e.g., "001_basic_functions")

    Returns:
        Tuple of (worktree_name, unique_id)
        Example: ("lamp-basic-functions-20231114-152345-claude", "basic-functions_a1b2c3d4")
    """
    # Get repo name
    repo_name = get_repo_name()

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Generate short UUID
    short_uuid = str(uuid.uuid4())[:8]

    # Clean PRD name (remove numbers and underscores, keep descriptive part)
    clean_prd = prd_name.replace("_", "-").lstrip("0123456789").lstrip("-")

    # Create worktree name: repo-prdname-timestamp-claude
    worktree_name = f"{repo_name}-{clean_prd}-{timestamp}-claude"

    # Create unique ID: prd_name_uuid
    unique_id = f"{clean_prd}_{short_uuid}"

    return worktree_name, unique_id


def create_worktree(prd_name: str, base_branch: str = "main") -> tuple[Path, str]:
    """Create a new git worktree for PRD implementation.

    Args:
        prd_name: The PRD name/number (e.g., "001_basic_functions")
        base_branch: Base branch to create worktree from (default: "main")

    Returns:
        Tuple of (worktree_path, unique_id)
    """
    # Get repo root
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    repo_root = Path(result.stdout.strip())

    # Generate worktree name and ID
    worktree_name, unique_id = generate_worktree_name(prd_name)

    # Worktree will be a sibling of the repo root
    worktree_path = repo_root.parent / worktree_name

    # Create worktree
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), base_branch],
        check=True,
    )

    print(f"✅ Created worktree: {worktree_path}")
    print(f"   ID: {unique_id}")

    return worktree_path, unique_id
