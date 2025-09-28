"""Auto-healing for Python modules."""
import json
import logging
import tempfile
import time
from pathlib import Path

from amplifier.tools.git_utils import cleanup_branch, commit_and_merge, create_healing_branch
from amplifier.tools.healing_models import HealingResult
from amplifier.tools.healing_prompts import select_best_prompt
from amplifier.tools.healing_safety import is_safe_module
from amplifier.tools.healing_validator import validate_module
from amplifier.tools.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)

def heal_single_module(module_path: Path, health_score: float, project_root: Path) -> HealingResult:
    """Attempt to heal a single module."""
    start_time = time.time()
    
    if not is_safe_module(module_path):
        return HealingResult.skipped(module_path, health_score, "Unsafe module")
        
    branch_name = create_healing_branch(module_path.stem)
    try:
        prompt = select_best_prompt(module_path.name, health_score)
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            f.write(prompt.encode())
            f.flush()
            
            if not run_healing_tool(module_path, f.name):
                raise Exception("Healing failed")
                
            if not validate_module(module_path, project_root):
                raise Exception("Validation failed")
                
            new_score = HealthMonitor(project_root).analyze_module(module_path).health_score
            if new_score <= health_score:
                raise Exception("No improvement")
                
            if commit_and_merge(module_path, branch_name, health_score, new_score):
                return HealingResult.success(module_path, health_score, new_score, time.time() - start_time)
                
    except Exception as e:
        logger.error(f"Healing failed: {e}")
        return HealingResult.failed(module_path, health_score, str(e), time.time() - start_time)
    finally:
        cleanup_branch(branch_name)
        
def run_healing_tool(module_path: Path, prompt_file: str) -> bool:
    """Run the healing tool on a module."""
    import subprocess
    result = subprocess.run(
        [
            ".aider-venv/bin/aider",
            "--model", "claude-3-5-sonnet-20241022",
            "--yes",
            "--no-auto-commits",
            "--message-file", prompt_file,
            str(module_path)
        ],
        capture_output=True,
        text=True,
        timeout=300
    )
    return result.returncode == 0

def heal_batch(max_modules: int, threshold: float, project_root: Path) -> list[HealingResult]:
    """Heal a batch of modules."""
    monitor = HealthMonitor(project_root)
    candidates = monitor.get_healing_candidates(threshold)
    safe_candidates = [h for h in candidates if is_safe_module(Path(h.module_path))]
    
    if not safe_candidates:
        logger.info("No safe modules need healing")
        return []
        
    results = []
    for health in safe_candidates[:max_modules]:
        result = heal_single_module(Path(health.module_path), health.health_score, project_root)
        results.append(result)
        if result.status == "failed":
            break
            
    save_results(results, project_root)
    return results

def save_results(results: list[HealingResult], project_root: Path):
    """Save and summarize healing results."""
    results_file = project_root / ".data" / "healing_results.json"
    
    all_results = []
    if results_file.exists():
        with open(results_file) as f:
            all_results = json.load(f)
            
    all_results.extend([r.dict() for r in results])
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
        
    successful = [r for r in results if r.status == "success"]
    if successful:
        avg_improvement = sum(r.health_after - r.health_before for r in successful) / len(successful)
        logger.info(f"\nHealing Summary:\n  Successful: {len(successful)}\n  Failed: {len(results) - len(successful)}\n  Average improvement: {avg_improvement:.1f} points")

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Auto-heal Python modules")
    parser.add_argument("--max", type=int, default=1, help="Max modules to heal")
    parser.add_argument("--threshold", type=float, default=70, help="Health threshold")
    parser.add_argument("--project-root", type=Path, default=Path("."), help="Project root directory")
    
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    
    results = heal_batch(args.max, args.threshold, args.project_root)
    for r in results:
        status = "✅" if r.status == "success" else "❌"
        print(f"{status} {Path(r.module_path).name}: {r.status}")

if __name__ == "__main__":
    main()
