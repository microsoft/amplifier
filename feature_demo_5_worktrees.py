#!/usr/bin/env python3
"""
Feature Demo #5: Parallel Worktrees
Shows how to work on multiple solutions simultaneously
"""
import subprocess
from pathlib import Path


def run_command(cmd, capture=True):
    """Run a shell command"""
    if capture:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    else:
        subprocess.run(cmd, shell=True)
        return ""


def main():
    print("\n" + "=" * 70)
    print("🌳 FEATURE #5: PARALLEL WORKTREES")
    print("=" * 70)

    print("\n📋 What are Git Worktrees?")
    print("   Git worktrees let you have multiple working directories")
    print("   from the same repository, each on a different branch.")
    print()
    print("   Think of it as:")
    print("   • Multiple parallel experiments")
    print("   • Each completely isolated")
    print("   • All sharing the same git history")
    print("   • No branch switching needed!")

    print("\n" + "-" * 70)
    print("🎯 WHY USE WORKTREES?")
    print("-" * 70)

    print("\n❌ Traditional Approach (Painful):")
    print("   1. Try approach A")
    print("   2. git stash")
    print("   3. git checkout -b approach-b")
    print("   4. Try approach B")
    print("   5. Compare? Need to switch back and forth!")
    print("   6. Lose context every time")

    print("\n✅ With Worktrees (Better):")
    print("   1. make worktree approach-a")
    print("   2. make worktree approach-b")
    print("   3. Work on both simultaneously")
    print("   4. Open both in separate VS Code windows")
    print("   5. Compare side-by-side")
    print("   6. Choose the winner, delete the other")

    # Show current worktrees
    print("\n" + "-" * 70)
    print("📊 CURRENT WORKTREES")
    print("-" * 70)

    print("\nChecking for existing worktrees...")
    try:
        worktrees = run_command("git worktree list")
        if worktrees:
            print("\nActive worktrees:")
            print(worktrees)
        else:
            print("\n(No additional worktrees currently)")
    except:
        print("\n(Unable to check - not in a git repository)")

    # Show the workflow
    print("\n" + "=" * 70)
    print("🔄 WORKTREE WORKFLOW")
    print("=" * 70)

    workflows = [
        {
            "title": "Create New Worktree",
            "command": "make worktree my-experiment",
            "what": [
                "Creates ../amplifier-my-experiment/",
                "New branch: my-experiment",
                "Copies .data/ for continuity",
                "Independent environment"
            ]
        },
        {
            "title": "List All Worktrees",
            "command": "make worktree-list",
            "what": [
                "Shows all active worktrees",
                "Branch and directory for each",
                "Status information"
            ]
        },
        {
            "title": "Hide Worktree (Keep Files)",
            "command": "make worktree-stash my-experiment",
            "what": [
                "Hides from VS Code workspace",
                "Files remain on disk",
                "Can restore later",
                "Useful for pausing experiments"
            ]
        },
        {
            "title": "Remove Worktree",
            "command": "make worktree-rm my-experiment",
            "what": [
                "Deletes worktree directory",
                "Deletes branch (with confirmation)",
                "Cleans up completely",
                "Use when experiment failed"
            ]
        },
        {
            "title": "Adopt Remote Branch",
            "command": "make worktree-adopt feature-from-laptop",
            "what": [
                "Creates worktree from remote branch",
                "Useful across devices",
                "Continues work from another machine"
            ]
        }
    ]

    for workflow in workflows:
        print(f"\n📌 {workflow['title']}")
        print(f"   Command: {workflow['command']}")
        print("   What happens:")
        for item in workflow['what']:
            print(f"      • {item}")

    # Real-world scenarios
    print("\n" + "=" * 70)
    print("📖 REAL-WORLD SCENARIOS")
    print("=" * 70)

    scenarios = [
        {
            "situation": "Trying Two Different Architectures",
            "approach": [
                "make worktree feature-jwt-auth",
                "make worktree feature-oauth-auth",
                "Implement both in parallel",
                "Test both thoroughly",
                "Compare: performance, complexity, security",
                "Choose winner, delete loser"
            ]
        },
        {
            "situation": "Risky Refactoring with Safety Net",
            "approach": [
                "Keep main worktree as working copy",
                "make worktree risky-refactor",
                "Try aggressive changes in worktree",
                "If it works: merge to main",
                "If it fails: delete worktree, no damage"
            ]
        },
        {
            "situation": "Working on Multiple Features",
            "approach": [
                "make worktree feature-caching",
                "make worktree feature-monitoring",
                "make worktree feature-analytics",
                "Switch contexts by switching windows",
                "Each feature stays isolated",
                "Merge when ready, independently"
            ]
        },
        {
            "situation": "Urgent Hotfix While Deep in Feature",
            "approach": [
                "Currently in feature worktree",
                "make worktree hotfix-critical-bug",
                "Fix bug in hotfix worktree",
                "Deploy from hotfix",
                "Return to feature work",
                "No branch switching, no stashing!"
            ]
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🎯 Scenario {i}: {scenario['situation']}")
        for j, step in enumerate(scenario['approach'], 1):
            print(f"   {j}. {step}")

    # Advanced tips
    print("\n" + "=" * 70)
    print("💡 PRO TIPS")
    print("=" * 70)

    tips = [
        {
            "tip": "Shared Data Directory",
            "detail": "Set AMPLIFIER_DATA_DIR in .env to share knowledge across all worktrees"
        },
        {
            "tip": "VS Code Integration",
            "detail": "Each worktree can be a separate VS Code window - true parallel development"
        },
        {
            "tip": "Worktree Naming",
            "detail": "Use descriptive names: feature-X, experiment-Y, refactor-Z, hotfix-N"
        },
        {
            "tip": "Clean Up Regularly",
            "detail": "Delete failed experiments: make worktree-rm experiment-name"
        },
        {
            "tip": "Safety Net Pattern",
            "detail": "Always keep main worktree clean, experiment in others"
        }
    ]

    for tip in tips:
        print(f"\n   ✨ {tip['tip']}")
        print(f"      {tip['detail']}")

    print("\n" + "=" * 70)
    print("✅ Parallel Worktrees Demo Complete!")
    print("=" * 70)

    print("\n💡 Key Takeaways:")
    print("   1. Work on multiple solutions simultaneously")
    print("   2. No branch switching = no context loss")
    print("   3. Compare approaches side-by-side")
    print("   4. Risk-free experimentation")
    print("   5. Each worktree is completely isolated")

    print("\n🎓 Why This Matters:")
    print("   • Stop choosing between approaches - try both!")
    print("   • Urgent hotfixes don't disrupt feature work")
    print("   • Risky experiments stay contained")
    print("   • True parallel development")
    print("   • Pick the winner after seeing results")

    print("\n🚀 Try it yourself:")
    print("   1. Create: make worktree test-experiment")
    print("   2. List: make worktree-list")
    print("   3. Open in VS Code: code ../amplifier-test-experiment")
    print("   4. Clean up: make worktree-rm test-experiment")
    print()


if __name__ == "__main__":
    main()
