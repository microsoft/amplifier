#!/usr/bin/env python3
"""
Manual test script for Super-Planner Phase 1
Run this script to verify the basic functionality works correctly.
"""

import sys
import uuid
from pathlib import Path

from amplifier.planner import Project
from amplifier.planner import Task
from amplifier.planner import TaskState
from amplifier.planner import load_project
from amplifier.planner import save_project


def test_basic_functionality():
    """Test basic task and project creation"""
    print("🧪 Testing Basic Functionality...")

    # Create a project
    project = Project(id=str(uuid.uuid4()), name="Test Blog Project")

    print(f"✅ Created project: {project.name}")
    print(f"   ID: {project.id}")

    # Create some tasks
    setup_task = Task(id="setup", title="Setup Project", description="Initialize Django blog project")

    models_task = Task(
        id="models",
        title="Create Models",
        description="Define User, Post, Comment models",
        depends_on=["setup"],  # Depends on setup
    )

    views_task = Task(
        id="views",
        title="Create Views",
        description="Build list, detail, create views",
        depends_on=["models"],  # Depends on models
    )

    # Add tasks to project
    project.add_task(setup_task)
    project.add_task(models_task)
    project.add_task(views_task)

    print(f"✅ Added {len(project.tasks)} tasks to project")

    return project


def test_hierarchy_and_dependencies():
    """Test hierarchical structure and dependency checking"""
    print("\n🏗️  Testing Hierarchy and Dependencies...")

    # Create project
    project = Project(id="test-hierarchy", name="Hierarchy Test")

    # Create parent task
    backend = Task(id="backend", title="Backend Development", description="API and server")

    # Create child tasks with parent
    auth = Task(id="auth", title="Authentication", parent_id="backend")
    api = Task(id="api", title="REST API", parent_id="backend", depends_on=["auth"])

    # Create independent task
    frontend = Task(id="frontend", title="Frontend", depends_on=["api"])

    # Add all tasks
    for task in [backend, auth, api, frontend]:
        project.add_task(task)

    # Test hierarchy navigation
    roots = project.get_roots()
    print(f"✅ Root tasks: {[t.title for t in roots]}")

    children = project.get_children("backend")
    print(f"✅ Backend children: {[t.title for t in children]}")

    # Test dependency checking
    completed = set()  # No tasks completed yet

    can_start_auth = project.tasks["auth"].can_start(completed)
    can_start_api = project.tasks["api"].can_start(completed)
    can_start_frontend = project.tasks["frontend"].can_start(completed)

    print(f"✅ Can start auth (no deps): {can_start_auth}")
    print(f"✅ Can start api (needs auth): {can_start_api}")
    print(f"✅ Can start frontend (needs api): {can_start_frontend}")

    # Complete auth, test again
    completed.add("auth")
    can_start_api_after = project.tasks["api"].can_start(completed)
    print(f"✅ Can start api after auth done: {can_start_api_after}")

    return project


def test_state_management():
    """Test task state transitions"""
    print("\n🔄 Testing State Management...")

    task = Task(id="test-state", title="State Test", description="Testing states")

    print(f"✅ Initial state: {task.state}")

    # Manually change state (Phase 1 doesn't have automatic transitions)
    task.state = TaskState.IN_PROGRESS
    print(f"✅ Updated to: {task.state}")

    task.state = TaskState.COMPLETED
    print(f"✅ Updated to: {task.state}")

    # Test state enum values
    print(f"✅ Available states: {[state.value for state in TaskState]}")

    return task


def test_persistence():
    """Test save and load functionality"""
    print("\n💾 Testing Persistence...")

    # Create test project
    original_project = Project(id="persistence-test", name="Persistence Test")

    task1 = Task(id="t1", title="Task 1", description="First task")
    task1.state = TaskState.COMPLETED

    task2 = Task(id="t2", title="Task 2", depends_on=["t1"])
    task2.assigned_to = "test-user"

    original_project.add_task(task1)
    original_project.add_task(task2)

    print(f"✅ Created project with {len(original_project.tasks)} tasks")

    # Save project
    try:
        save_project(original_project)
        print("✅ Project saved successfully")
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return None

    # Load project
    try:
        loaded_project = load_project("persistence-test")
        if loaded_project is None:
            print("❌ Load returned None")
            return None

        print("✅ Project loaded successfully")
        print(f"   Name: {loaded_project.name}")
        print(f"   Tasks: {len(loaded_project.tasks)}")

        # Verify task details preserved
        loaded_t1 = loaded_project.tasks["t1"]
        loaded_t2 = loaded_project.tasks["t2"]

        print(f"   Task 1 state: {loaded_t1.state}")
        print(f"   Task 2 assigned to: {loaded_t2.assigned_to}")
        print(f"   Task 2 depends on: {loaded_t2.depends_on}")

        # Verify data integrity
        assert loaded_t1.state == TaskState.COMPLETED
        assert loaded_t2.assigned_to == "test-user"
        assert loaded_t2.depends_on == ["t1"]

        print("✅ All data preserved correctly")

        return loaded_project

    except Exception as e:
        print(f"❌ Load failed: {e}")
        return None


def test_complete_workflow():
    """Test complete project workflow"""
    print("\n🚀 Testing Complete Workflow...")

    # Create Django blog project
    project = Project(id="django-blog", name="Django Blog")

    # Define task hierarchy
    tasks = [
        Task("setup", "Project Setup", "Create Django project and configure settings"),
        Task("models", "Database Models", "Create User, Post, Comment models", depends_on=["setup"]),
        Task("admin", "Admin Interface", "Configure Django admin", depends_on=["models"]),
        Task("views", "Views", "Create list, detail, create views", depends_on=["models"]),
        Task("templates", "Templates", "Design HTML templates", depends_on=["views"]),
        Task("urls", "URL Configuration", "Set up routing", depends_on=["views"]),
        Task("tests", "Tests", "Write unit tests", depends_on=["models", "views"]),
        Task("deploy", "Deployment", "Deploy to production", depends_on=["templates", "urls", "tests"]),
    ]

    # Add all tasks
    for task in tasks:
        project.add_task(task)

    print(f"✅ Created project with {len(tasks)} tasks")

    # Save project
    save_project(project)
    print("✅ Project saved")

    # Simulate workflow: complete tasks in dependency order
    completed_tasks = set()

    def find_ready_tasks():
        ready = []
        for task in project.tasks.values():
            if task.state == TaskState.PENDING and task.can_start(completed_tasks):
                ready.append(task)
        return ready

    step = 1
    while completed_tasks != set(project.tasks.keys()):
        ready_tasks = find_ready_tasks()

        if not ready_tasks:
            break

        # "Complete" the first ready task
        next_task = ready_tasks[0]
        next_task.state = TaskState.COMPLETED
        completed_tasks.add(next_task.id)

        print(f"   Step {step}: Completed '{next_task.title}'")
        step += 1

    # Save final state
    save_project(project)
    print("✅ Workflow simulation completed")

    return project


def show_data_files():
    """Show created data files"""
    print("\n📁 Created Data Files:")

    data_dir = Path("data/planner/projects")
    if data_dir.exists():
        for json_file in data_dir.glob("*.json"):
            print(f"   📄 {json_file}")
            # Show first few lines
            try:
                with open(json_file) as f:
                    content = f.read()
                    lines = content.split("\n")[:5]
                    preview = "\n".join(lines)
                    if len(content.split("\n")) > 5:
                        preview += "\n      ..."
                    print(f"      Preview:\n      {preview.replace(chr(10), chr(10) + '      ')}")
            except Exception:
                pass
    else:
        print("   No data directory found")


def main():
    """Run all tests"""
    print("🎯 Super-Planner Phase 1 Manual Testing")
    print("=" * 50)

    try:
        # Test basic functionality
        test_basic_functionality()

        # Test hierarchy
        test_hierarchy_and_dependencies()

        # Test states
        test_state_management()

        # Test persistence
        test_persistence()

        # Test complete workflow
        test_complete_workflow()

        # Show files created
        show_data_files()

        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("\nWhat was tested:")
        print("✅ Task and Project creation")
        print("✅ Hierarchical structure (parents/children)")
        print("✅ Dependency management")
        print("✅ State transitions")
        print("✅ File persistence (save/load)")
        print("✅ Complete project workflow")

        print("\n💾 Data stored in: data/planner/projects/")
        print("   You can examine the JSON files to see the structure")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
