#!/usr/bin/env python3
"""
Hostile Testing Suite for Super-Planner Phase 1
Testing with "Rewrite Vi Editor in Python" - A Complex Multi-Level Project

This test is designed to break things and find edge cases by:
- Creating deeply nested hierarchies (5+ levels)
- Complex dependency graphs with multiple paths
- Large numbers of tasks (100+)
- Edge case scenarios (circular deps, missing deps, etc.)
- Stress testing state transitions
- Large data serialization
- Unusual task names and characters
- Performance testing with bulk operations
"""

import json
import sys
import time
from pathlib import Path

from amplifier.planner import Project
from amplifier.planner import Task
from amplifier.planner import TaskState
from amplifier.planner import load_project
from amplifier.planner import save_project


class HostileTester:
    """Hostile testing framework for Phase 1"""

    def __init__(self):
        self.failures = []
        self.test_count = 0
        self.start_time = time.time()

    def assert_test(self, condition, message):
        """Custom assertion with failure tracking"""
        self.test_count += 1
        if not condition:
            self.failures.append(f"❌ Test {self.test_count}: {message}")
            print(f"❌ FAIL: {message}")
            return False
        print(f"✅ PASS: {message}")
        return True

    def test_edge_case_task_creation(self):
        """Test edge cases in task creation"""
        print("\n🔥 HOSTILE TEST 1: Edge Case Task Creation")

        # Test with unusual characters
        weird_task = Task(
            id="weird-chars-™️🔥💻",
            title="Task with émojis and spéciał chars: <>&\"'",
            description="Multi-line\ndescription with\ttabs and\nweird chars: 你好世界",
        )
        self.assert_test(weird_task.id == "weird-chars-™️🔥💻", "Task with weird characters created")

        # Test with very long strings
        long_id = "a" * 1000
        long_task = Task(id=long_id, title="b" * 500, description="c" * 2000)
        self.assert_test(len(long_task.description) == 2000, "Task with very long strings")

        # Test with empty/minimal data
        minimal_task = Task("", "")
        self.assert_test(minimal_task.id == "", "Task with empty ID")

        # Test with None values where optional
        task_with_nones = Task("test", "Test", assigned_to=None, parent_id=None)
        self.assert_test(task_with_nones.assigned_to is None, "Task with explicit None values")

        return True

    def test_circular_dependencies(self):
        """Test detection/handling of circular dependencies"""
        print("\n🔥 HOSTILE TEST 2: Circular Dependencies")

        project = Project("circular-test", "Circular Dependency Test")

        # Create circular dependency: A -> B -> C -> A
        task_a = Task("a", "Task A", depends_on=["c"])  # Depends on C
        task_b = Task("b", "Task B", depends_on=["a"])  # Depends on A
        task_c = Task("c", "Task C", depends_on=["b"])  # Depends on B -> Circular!

        project.add_task(task_a)
        project.add_task(task_b)
        project.add_task(task_c)

        # Test that none can start (circular dependency)
        completed = set()
        can_start_a = task_a.can_start(completed)
        can_start_b = task_b.can_start(completed)
        can_start_c = task_c.can_start(completed)

        self.assert_test(
            not can_start_a and not can_start_b and not can_start_c,
            "Circular dependencies prevent all tasks from starting",
        )

        return project

    def test_complex_dependency_graph(self):
        """Test complex dependency resolution"""
        print("\n🔥 HOSTILE TEST 3: Complex Dependency Graph")

        project = Project("complex-deps", "Complex Dependencies")

        # Create diamond dependency pattern
        root = Task("root", "Root Task")
        branch_a = Task("branch_a", "Branch A", depends_on=["root"])
        branch_b = Task("branch_b", "Branch B", depends_on=["root"])
        merge = Task("merge", "Merge Task", depends_on=["branch_a", "branch_b"])

        # Create fan-out from merge
        fan1 = Task("fan1", "Fan 1", depends_on=["merge"])
        fan2 = Task("fan2", "Fan 2", depends_on=["merge"])
        fan3 = Task("fan3", "Fan 3", depends_on=["merge"])

        # Create final convergence
        final = Task("final", "Final", depends_on=["fan1", "fan2", "fan3"])

        tasks = [root, branch_a, branch_b, merge, fan1, fan2, fan3, final]
        for task in tasks:
            project.add_task(task)

        # Test dependency resolution step by step
        completed = set()

        # Initially only root can start
        startable = [t for t in tasks if t.can_start(completed)]
        self.assert_test(len(startable) == 1 and startable[0].id == "root", "Only root task can start initially")

        # Complete root, now branches can start
        completed.add("root")
        startable = [t for t in tasks if t.can_start(completed) and t.id not in completed]
        startable_ids = {t.id for t in startable}
        self.assert_test(startable_ids == {"branch_a", "branch_b"}, "After root, both branches can start")

        # Complete both branches, merge can start
        completed.update(["branch_a", "branch_b"])
        startable = [t for t in tasks if t.can_start(completed) and t.id not in completed]
        self.assert_test(len(startable) == 1 and startable[0].id == "merge", "After branches, merge can start")

        return project

    def create_vi_editor_project(self):
        """Create the monster Vi editor rewrite project"""
        print("\n🔥 HOSTILE TEST 4: Vi Editor Project - Ultra Complex Hierarchy")

        project = Project("vi-rewrite", "Vi Editor Rewrite in Python")

        # Level 1: Major components
        architecture = Task(
            "arch", "Architecture & Design", "Define overall architecture, data structures, and interfaces"
        )

        core_engine = Task(
            "core",
            "Core Editing Engine",
            "Text buffer management, cursor handling, basic operations",
            depends_on=["arch"],
        )

        command_system = Task(
            "commands", "Command System", "Vi command parsing, execution, and modal interface", depends_on=["arch"]
        )

        ui_system = Task(
            "ui", "User Interface System", "Terminal handling, screen rendering, input processing", depends_on=["arch"]
        )

        file_system = Task(
            "filesystem", "File Operations", "File I/O, backup, recovery, file type detection", depends_on=["arch"]
        )

        # Level 2: Architecture breakdown
        arch_tasks = [
            Task(
                "arch-analysis",
                "Requirements Analysis",
                parent_id="arch",
                description="Analyze vi behavior, commands, edge cases",
            ),
            Task(
                "arch-design",
                "System Design",
                parent_id="arch",
                depends_on=["arch-analysis"],
                description="Design core data structures and interfaces",
            ),
            Task(
                "arch-patterns",
                "Design Patterns",
                parent_id="arch",
                depends_on=["arch-design"],
                description="Define patterns for extensibility",
            ),
            Task(
                "arch-docs",
                "Architecture Documentation",
                parent_id="arch",
                depends_on=["arch-patterns"],
                description="Document architecture decisions",
            ),
        ]

        # Level 2: Core engine breakdown
        core_tasks = [
            Task(
                "core-buffer",
                "Text Buffer",
                parent_id="core",
                depends_on=["core"],
                description="Efficient text storage with undo/redo",
            ),
            Task(
                "core-cursor",
                "Cursor Management",
                parent_id="core",
                depends_on=["core-buffer"],
                description="Cursor positioning, movement, selection",
            ),
            Task(
                "core-operations",
                "Basic Operations",
                parent_id="core",
                depends_on=["core-cursor"],
                description="Insert, delete, replace operations",
            ),
            Task(
                "core-marks",
                "Marks and Registers",
                parent_id="core",
                depends_on=["core-operations"],
                description="Named marks, registers, clipboard",
            ),
            Task(
                "core-search",
                "Search Engine",
                parent_id="core",
                depends_on=["core-operations"],
                description="Pattern matching, regex, search/replace",
            ),
        ]

        # Level 3: Buffer implementation details
        buffer_tasks = [
            Task(
                "buffer-gap",
                "Gap Buffer Implementation",
                parent_id="core-buffer",
                depends_on=["core-buffer"],
                description="Efficient gap buffer with automatic expansion",
            ),
            Task(
                "buffer-lines",
                "Line Management",
                parent_id="core-buffer",
                depends_on=["buffer-gap"],
                description="Line indexing, wrapping, virtual lines",
            ),
            Task(
                "buffer-encoding",
                "Text Encoding",
                parent_id="core-buffer",
                depends_on=["buffer-lines"],
                description="UTF-8, line endings, BOM handling",
            ),
            Task(
                "buffer-undo",
                "Undo System",
                parent_id="core-buffer",
                depends_on=["buffer-encoding"],
                description="Efficient undo/redo with branching",
            ),
            Task(
                "buffer-diff",
                "Change Tracking",
                parent_id="core-buffer",
                depends_on=["buffer-undo"],
                description="Track changes for diff, backup",
            ),
        ]

        # Level 2: Command system breakdown
        command_tasks = [
            Task(
                "cmd-parser",
                "Command Parser",
                parent_id="commands",
                depends_on=["commands"],
                description="Parse vi commands with error handling",
            ),
            Task(
                "cmd-modes",
                "Modal Interface",
                parent_id="commands",
                depends_on=["cmd-parser"],
                description="Normal, insert, visual, command modes",
            ),
            Task(
                "cmd-movement",
                "Movement Commands",
                parent_id="commands",
                depends_on=["cmd-modes"],
                description="h,j,k,l, w,e,b, $,^, G, etc.",
            ),
            Task(
                "cmd-editing",
                "Editing Commands",
                parent_id="commands",
                depends_on=["cmd-movement"],
                description="i,a,o, d,c,y, p, u, ., etc.",
            ),
            Task(
                "cmd-visual",
                "Visual Mode",
                parent_id="commands",
                depends_on=["cmd-editing"],
                description="Visual selection, visual block",
            ),
            Task(
                "cmd-ex",
                "Ex Commands",
                parent_id="commands",
                depends_on=["cmd-visual"],
                description=":w, :q, :s, :!, etc.",
            ),
        ]

        # Level 3: Movement command details
        movement_tasks = [
            Task(
                "move-char",
                "Character Movement",
                parent_id="cmd-movement",
                depends_on=["cmd-movement"],
                description="h,l,space,backspace movement",
            ),
            Task(
                "move-word",
                "Word Movement",
                parent_id="cmd-movement",
                depends_on=["move-char"],
                description="w,e,b,W,E,B word boundaries",
            ),
            Task(
                "move-line",
                "Line Movement",
                parent_id="cmd-movement",
                depends_on=["move-word"],
                description="j,k,$,^,0,+,- movements",
            ),
            Task(
                "move-search",
                "Search Movement",
                parent_id="cmd-movement",
                depends_on=["move-line"],
                description="f,F,t,T,;,, and /,? searches",
            ),
            Task(
                "move-jump",
                "Jump Commands",
                parent_id="cmd-movement",
                depends_on=["move-search"],
                description="G,gg,H,M,L,ctrl-f,ctrl-b",
            ),
        ]

        # Level 2: UI system breakdown
        ui_tasks = [
            Task(
                "ui-terminal",
                "Terminal Interface",
                parent_id="ui",
                depends_on=["ui"],
                description="Raw terminal control, escape sequences",
            ),
            Task(
                "ui-screen",
                "Screen Management",
                parent_id="ui",
                depends_on=["ui-terminal"],
                description="Screen buffer, scrolling, refresh",
            ),
            Task(
                "ui-input",
                "Input Processing",
                parent_id="ui",
                depends_on=["ui-screen"],
                description="Key mapping, special keys, timing",
            ),
            Task(
                "ui-rendering",
                "Text Rendering",
                parent_id="ui",
                depends_on=["ui-input"],
                description="Syntax highlighting, line numbers",
            ),
            Task(
                "ui-status",
                "Status Line",
                parent_id="ui",
                depends_on=["ui-rendering"],
                description="Mode indicator, position, filename",
            ),
        ]

        # Level 2: File system breakdown
        file_tasks = [
            Task(
                "file-io",
                "Basic File I/O",
                parent_id="filesystem",
                depends_on=["filesystem"],
                description="Read/write files, error handling",
            ),
            Task(
                "file-backup",
                "Backup System",
                parent_id="filesystem",
                depends_on=["file-io"],
                description="Swap files, backup files, recovery",
            ),
            Task(
                "file-detection",
                "File Type Detection",
                parent_id="filesystem",
                depends_on=["file-backup"],
                description="Syntax detection, file associations",
            ),
            Task(
                "file-encoding",
                "Encoding Detection",
                parent_id="filesystem",
                depends_on=["file-detection"],
                description="Auto-detect and handle encodings",
            ),
        ]

        # Integration tasks (depend on multiple components)
        integration_tasks = [
            Task(
                "integration-basic",
                "Basic Integration",
                depends_on=["core-operations", "cmd-editing", "ui-screen"],
                description="Integrate core editing with UI",
            ),
            Task(
                "integration-advanced",
                "Advanced Integration",
                depends_on=["integration-basic", "core-search", "cmd-ex"],
                description="Integrate search, ex commands",
            ),
            Task(
                "integration-files",
                "File Integration",
                depends_on=["integration-advanced", "file-encoding"],
                description="Integrate file operations",
            ),
        ]

        # Testing tasks (comprehensive testing pyramid)
        test_tasks = [
            Task(
                "test-unit",
                "Unit Tests",
                depends_on=["buffer-diff", "move-jump", "ui-status"],
                description="Unit tests for all components",
            ),
            Task(
                "test-integration",
                "Integration Tests",
                depends_on=["test-unit", "integration-files"],
                description="Integration tests across components",
            ),
            Task(
                "test-compatibility",
                "Vi Compatibility Tests",
                depends_on=["test-integration"],
                description="Test compatibility with real vi",
            ),
            Task(
                "test-performance",
                "Performance Tests",
                depends_on=["test-compatibility"],
                description="Large file performance, memory usage",
            ),
            Task(
                "test-edge-cases",
                "Edge Case Tests",
                depends_on=["test-performance"],
                description="Binary files, huge files, corner cases",
            ),
        ]

        # Polish and release tasks
        polish_tasks = [
            Task(
                "polish-docs",
                "Documentation",
                depends_on=["test-edge-cases"],
                description="User manual, developer docs",
            ),
            Task(
                "polish-package",
                "Packaging",
                depends_on=["polish-docs"],
                description="Setup.py, distribution, installation",
            ),
            Task(
                "polish-ci",
                "CI/CD Setup",
                depends_on=["polish-package"],
                description="GitHub actions, automated testing",
            ),
            Task("release-beta", "Beta Release", depends_on=["polish-ci"], description="Initial beta release"),
            Task("release-stable", "Stable Release", depends_on=["release-beta"], description="1.0 stable release"),
        ]

        # Add ALL tasks to project
        all_tasks = (
            [architecture, core_engine, command_system, ui_system, file_system]
            + arch_tasks
            + core_tasks
            + buffer_tasks
            + command_tasks
            + movement_tasks
            + ui_tasks
            + file_tasks
            + integration_tasks
            + test_tasks
            + polish_tasks
        )

        print(f"   Creating {len(all_tasks)} tasks with complex dependencies...")

        for task in all_tasks:
            project.add_task(task)

        # Add some stress test tasks with random dependencies
        import random

        for i in range(20):
            # Pick random existing tasks as dependencies
            existing_ids = list(project.tasks.keys())
            num_deps = random.randint(0, min(3, len(existing_ids)))
            deps = random.sample(existing_ids, num_deps) if num_deps > 0 else []

            stress_task = Task(
                f"stress-{i:02d}",
                f"Stress Test Task {i}",
                f"Random stress test task with {num_deps} dependencies",
                depends_on=deps,
            )
            project.add_task(stress_task)

        print(f"   Total tasks created: {len(project.tasks)}")

        self.assert_test(len(project.tasks) > 50, f"Created large project with {len(project.tasks)} tasks")

        return project

    def test_hierarchy_navigation(self, project):
        """Test complex hierarchy navigation"""
        print("\n🔥 HOSTILE TEST 5: Complex Hierarchy Navigation")

        # Test root finding
        project.get_roots()

        # Find actual roots (tasks with no parent_id and not depended on by others)
        actual_roots = []
        for task in project.tasks.values():
            if task.parent_id is None:
                # Check if it's not just a dependency
                is_dependency_only = any(
                    task.id in other_task.depends_on
                    for other_task in project.tasks.values()
                    if other_task.id != task.id
                )
                if not is_dependency_only or task.id in ["arch", "core", "commands", "ui", "filesystem"]:
                    actual_roots.append(task)

        self.assert_test(len(actual_roots) >= 5, f"Found {len(actual_roots)} root tasks in complex hierarchy")

        # Test deep hierarchy navigation
        if "arch" in project.tasks:
            arch_children = project.get_children("arch")
            self.assert_test(len(arch_children) >= 4, f"Architecture has {len(arch_children)} direct children")

            # Test grandchildren
            if arch_children:
                first_child = arch_children[0]
                grandchildren = project.get_children(first_child.id)
                print(f"   Found {len(grandchildren)} grandchildren under {first_child.title}")

        # Test that hierarchy doesn't create loops
        def check_hierarchy_loops(task_id, visited=None):
            if visited is None:
                visited = set()
            if task_id in visited:
                return True  # Loop detected
            visited.add(task_id)

            task = project.tasks.get(task_id)
            if task and task.parent_id:
                return check_hierarchy_loops(task.parent_id, visited)
            return False

        loop_count = 0
        for task_id in project.tasks:
            if check_hierarchy_loops(task_id):
                loop_count += 1

        self.assert_test(loop_count == 0, f"No hierarchy loops detected (checked {len(project.tasks)} tasks)")

        return True

    def test_dependency_resolution_stress(self, project):
        """Stress test dependency resolution"""
        print("\n🔥 HOSTILE TEST 6: Dependency Resolution Stress Test")

        # Test can_start for all tasks
        completed = set()
        start_time = time.time()

        initial_startable = []
        for task in project.tasks.values():
            if task.can_start(completed):
                initial_startable.append(task)

        resolution_time = time.time() - start_time
        self.assert_test(
            resolution_time < 1.0, f"Dependency resolution for {len(project.tasks)} tasks took {resolution_time:.3f}s"
        )

        print(f"   Initially {len(initial_startable)} tasks can start")

        # Simulate completing tasks and check resolution at each step
        simulation_steps = 0
        max_steps = min(50, len(project.tasks))  # Limit simulation for performance

        while len(completed) < max_steps and simulation_steps < max_steps:
            startable = [t for t in project.tasks.values() if t.can_start(completed) and t.id not in completed]

            if not startable:
                break

            # "Complete" the first startable task
            next_task = startable[0]
            completed.add(next_task.id)
            simulation_steps += 1

            if simulation_steps % 10 == 0:
                print(f"   Step {simulation_steps}: Completed {len(completed)} tasks, {len(startable)} available")

        self.assert_test(simulation_steps > 20, f"Successfully simulated {simulation_steps} task completions")

        # Test that we didn't get stuck (should be able to complete at least some tasks)
        progress_ratio = len(completed) / len(project.tasks)
        self.assert_test(progress_ratio > 0.1, f"Made progress on {progress_ratio:.2%} of tasks")

        return True

    def test_serialization_stress(self, project):
        """Test serialization with large, complex data"""
        print("\n🔥 HOSTILE TEST 7: Serialization Stress Test")

        # Add tasks with extreme data
        extreme_task = Task(
            "extreme-data",
            "Task with extreme data",
            "Description with every Unicode character: " + "".join(chr(i) for i in range(32, 127)),
        )

        # Add metadata stress test
        extreme_task.assigned_to = "user with 🔥émojis💻 and spëciål chars"
        project.add_task(extreme_task)

        # Test save with large project
        start_time = time.time()
        try:
            save_project(project)
            save_time = time.time() - start_time
            self.assert_test(save_time < 5.0, f"Large project save took {save_time:.3f}s (under 5s)")
        except Exception as e:
            self.assert_test(False, f"Save failed with large project: {e}")
            return False

        # Test load with large project
        start_time = time.time()
        try:
            loaded_project = load_project(project.id)
            load_time = time.time() - start_time
            self.assert_test(load_time < 2.0, f"Large project load took {load_time:.3f}s (under 2s)")
        except Exception as e:
            self.assert_test(False, f"Load failed with large project: {e}")
            return False

        # Test data integrity with complex project
        self.assert_test(loaded_project is not None, "Large project loaded successfully")
        self.assert_test(
            len(loaded_project.tasks) == len(project.tasks), f"All {len(project.tasks)} tasks preserved after save/load"
        )

        # Test specific task integrity
        if "extreme-data" in loaded_project.tasks:
            loaded_extreme = loaded_project.tasks["extreme-data"]
            self.assert_test(
                loaded_extreme.assigned_to == extreme_task.assigned_to, "Unicode characters preserved in assignment"
            )

        # Test JSON structure manually
        data_file = Path("data/planner/projects") / f"{project.id}.json"
        if data_file.exists():
            try:
                with open(data_file) as f:
                    json_data = json.load(f)

                self.assert_test("tasks" in json_data, "JSON contains tasks array")
                self.assert_test(len(json_data["tasks"]) == len(project.tasks), "JSON task count matches project")

                # Test that JSON is properly formatted (can be re-parsed)
                json_str = json.dumps(json_data, indent=2)
                reparsed = json.loads(json_str)
                self.assert_test(reparsed == json_data, "JSON round-trip successful")

            except Exception as e:
                self.assert_test(False, f"JSON validation failed: {e}")

        return loaded_project

    def test_state_transition_stress(self, project):
        """Test state transitions under stress"""
        print("\n🔥 HOSTILE TEST 8: State Transition Stress")

        # Test all possible state transitions
        test_task = Task("state-test", "State Transition Test")
        project.add_task(test_task)

        # Test each state transition
        states = [TaskState.PENDING, TaskState.IN_PROGRESS, TaskState.COMPLETED, TaskState.BLOCKED]

        for from_state in states:
            for to_state in states:
                test_task.state = from_state
                test_task.state = to_state  # Should always work (no validation in Phase 1)
                self.assert_test(test_task.state == to_state, f"Transition from {from_state.value} to {to_state.value}")

        # Test rapid state changes (performance)
        start_time = time.time()
        for i in range(1000):
            test_task.state = states[i % len(states)]

        transition_time = time.time() - start_time
        self.assert_test(transition_time < 0.1, f"1000 state transitions took {transition_time:.3f}s")

        # Test state preservation through save/load
        test_task.state = TaskState.BLOCKED
        save_project(project)

        loaded = load_project(project.id)
        if loaded and "state-test" in loaded.tasks:
            loaded_state = loaded.tasks["state-test"].state
            self.assert_test(loaded_state == TaskState.BLOCKED, "BLOCKED state preserved through save/load")

        return True

    def test_error_conditions(self):
        """Test error handling and edge cases"""
        print("\n🔥 HOSTILE TEST 9: Error Conditions & Edge Cases")

        # Test loading non-existent project
        try:
            load_project("this-project-does-not-exist-12345")
            self.assert_test(False, "Loading non-existent project should raise FileNotFoundError")
        except FileNotFoundError:
            self.assert_test(True, "Loading non-existent project raises FileNotFoundError")

        # Test with invalid task dependencies
        project = Project("error-test", "Error Test Project")

        task_with_missing_deps = Task(
            "missing-deps", "Missing Dependencies", depends_on=["non-existent-1", "non-existent-2"]
        )
        project.add_task(task_with_missing_deps)

        # Should not crash, but can't start due to missing dependencies
        completed = set()
        can_start = task_with_missing_deps.can_start(completed)
        self.assert_test(not can_start, "Task with missing dependencies cannot start")

        # Test adding dependencies that exist
        helper_task = Task("helper", "Helper Task")
        project.add_task(helper_task)
        completed.add("helper")  # Complete the helper

        # Still can't start because other deps are missing
        still_cant_start = task_with_missing_deps.can_start(completed)
        self.assert_test(not still_cant_start, "Task still blocked by remaining missing dependencies")

        # Test duplicate task IDs
        original_task = Task("duplicate-id", "Original Task")
        duplicate_task = Task("duplicate-id", "Duplicate Task")

        project.add_task(original_task)
        project.add_task(duplicate_task)  # Should overwrite

        self.assert_test(
            project.tasks["duplicate-id"].title == "Duplicate Task", "Duplicate task ID overwrites original"
        )

        return True

    def test_performance_limits(self, project):
        """Test performance with large operations"""
        print("\n🔥 HOSTILE TEST 10: Performance Limits")

        # Test bulk operations
        bulk_tasks = []
        start_time = time.time()

        for i in range(500):
            task = Task(f"bulk-{i:03d}", f"Bulk Task {i}", f"Generated task {i}")
            bulk_tasks.append(task)
            project.add_task(task)

        bulk_creation_time = time.time() - start_time
        self.assert_test(bulk_creation_time < 2.0, f"Creating 500 tasks took {bulk_creation_time:.3f}s")

        print(f"   Project now has {len(project.tasks)} total tasks")

        # Test bulk dependency checking
        completed = {f"bulk-{i:03d}" for i in range(0, 250, 2)}  # Complete every other task

        start_time = time.time()
        startable_count = 0
        for task in project.tasks.values():
            if task.can_start(completed):
                startable_count += 1

        dependency_check_time = time.time() - start_time
        self.assert_test(
            dependency_check_time < 1.0,
            f"Dependency check on {len(project.tasks)} tasks took {dependency_check_time:.3f}s",
        )

        print(f"   Found {startable_count} startable tasks with {len(completed)} completed")

        # Test memory usage (rough estimate)
        import sys

        project_size = sys.getsizeof(project) + sum(sys.getsizeof(task) for task in project.tasks.values())
        size_mb = project_size / (1024 * 1024)

        self.assert_test(size_mb < 10, f"Project memory usage {size_mb:.2f}MB (under 10MB)")

        return True

    def run_all_tests(self):
        """Run the complete hostile test suite"""
        print("🔥🔥🔥 HOSTILE TESTING SUITE - SUPER-PLANNER PHASE 1 🔥🔥🔥")
        print("Designed to break things and find every possible edge case!")
        print("=" * 80)

        # Run all tests
        self.test_edge_case_task_creation()
        self.test_circular_dependencies()
        self.test_complex_dependency_graph()

        vi_project = self.create_vi_editor_project()
        self.test_hierarchy_navigation(vi_project)
        self.test_dependency_resolution_stress(vi_project)
        loaded_project = self.test_serialization_stress(vi_project)
        self.test_state_transition_stress(loaded_project or vi_project)
        self.test_error_conditions()
        self.test_performance_limits(loaded_project or vi_project)

        # Final results
        total_time = time.time() - self.start_time

        print("\n" + "=" * 80)
        print("🔥 HOSTILE TESTING COMPLETE 🔥")
        print(f"⏱️  Total time: {total_time:.2f} seconds")
        print(f"🧪 Tests run: {self.test_count}")
        print(f"✅ Passed: {self.test_count - len(self.failures)}")
        print(f"❌ Failed: {len(self.failures)}")

        if self.failures:
            print("\n💥 FAILURES:")
            for failure in self.failures:
                print(f"   {failure}")
            print("\n🚨 PHASE 1 HAS ISSUES! 🚨")
            return False
        print("\n🎉 ALL HOSTILE TESTS PASSED! 🎉")
        print("✨ Phase 1 is BULLETPROOF! ✨")
        print(
            f"💪 Successfully handled {len(loaded_project.tasks) if 'loaded_project' in locals() and loaded_project else 'many'} tasks in complex project"
        )
        return True


def main():
    """Run the hostile test suite"""
    tester = HostileTester()
    success = tester.run_all_tests()

    print("\n📁 Test data saved to: data/planner/projects/")
    print("   Check vi-rewrite.json to see the complex project structure")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
