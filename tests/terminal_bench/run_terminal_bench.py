import argparse
import json
from datetime import datetime
from pathlib import Path

from terminal_bench import Harness  # type: ignore[import-untyped]


def main(agent: str) -> None:
    run_id = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
    runs_dir = Path(__file__).parents[2] / "ai_working" / "tmp"
    runs_dir.mkdir(parents=True, exist_ok=True)

    original_dataset_name = "terminal-bench-core"
    original_dataset_version = "0.1.1"

    # Load the train split from the generated split.json
    split_data = json.loads((Path(__file__).parents[0] / "split.json").read_text())
    task_ids = split_data["train"]

    agent_import_path = (
        "custom_agents:CustomAmplifierAgent" if agent == "amplifier" else "custom_agents:ClaudeCodeAgent"
    )

    harness = Harness(
        output_path=runs_dir,
        run_id=run_id,
        dataset_name=original_dataset_name,
        dataset_version=original_dataset_version,
        agent_import_path=agent_import_path,
        no_rebuild=False,
        cleanup=True,
        task_ids=task_ids,
        n_concurrent_trials=5,
        n_attempts=1,
        global_timeout_multiplier=2,
    )

    results = harness.run()
    print(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run terminal-bench with amplifier or baseline agent")
    parser.add_argument(
        "--agent",
        choices=["amplifier", "baseline"],
        default="amplifier",
        help="Agent type to use (default: amplifier)",
    )
    args = parser.parse_args()
    main(args.agent)
