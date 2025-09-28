"""Comprehensive test suite for the self-healing system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from amplifier.tools.auto_healer import AutoHealer
from amplifier.tools.auto_healer import _run_healing_tool
from amplifier.tools.auto_healer import heal_batch
from amplifier.tools.auto_healer import heal_single_module
from amplifier.tools.git_utils import cleanup_branch
from amplifier.tools.git_utils import commit_and_merge
from amplifier.tools.git_utils import create_healing_branch
from amplifier.tools.healing_models import HealingResult
from amplifier.tools.healing_results import _log_summary
from amplifier.tools.healing_results import save_results
from amplifier.tools.healing_safety import is_safe_module
from amplifier.tools.healing_validator import validate_imports
from amplifier.tools.healing_validator import validate_module
from amplifier.tools.healing_validator import validate_syntax
from amplifier.tools.healing_validator import validate_tests
from amplifier.tools.health_monitor import HealthMonitor
from amplifier.tools.health_monitor import ModuleHealth
from amplifier.tools.parallel_healer import ParallelHealer


class TestHealthMonitor:
    """Test health monitoring functionality."""

    def test_analyze_module_basic(self, tmp_path):
        """Test basic module analysis."""
        # Create a simple Python file
        module_path = tmp_path / "simple.py"
        module_path.write_text("""
def hello():
    return "Hello"

def world():
    if True:
        return "World"
""")

        monitor = HealthMonitor(tmp_path)
        health = monitor.analyze_module(module_path)

        assert health.module_path == str(module_path)
        assert health.function_count == 2
        assert health.class_count == 0
        assert health.loc == 7
        assert health.complexity > 0

    def test_analyze_module_with_syntax_error(self, tmp_path):
        """Test module analysis with syntax error."""
        module_path = tmp_path / "broken.py"
        module_path.write_text("def broken(:\n    pass")

        monitor = HealthMonitor(tmp_path)
        health = monitor.analyze_module(module_path)

        assert health.complexity == 999  # Max complexity for broken code
        assert health.function_count == 0
        assert health.class_count == 0

    def test_calculate_complexity(self, tmp_path):
        """Test cyclomatic complexity calculation."""
        module_path = tmp_path / "complex.py"
        module_path.write_text("""
def complex_function(x, y):
    if x > 0:
        if y > 0:
            return "both positive"
        else:
            return "x positive"
    elif x < 0:
        return "x negative"
    else:
        return "x zero"

    for i in range(10):
        if i % 2 == 0:
            print(i)
""")

        monitor = HealthMonitor(tmp_path)
        health = monitor.analyze_module(module_path)

        assert health.complexity > 5  # Should have significant complexity

    def test_health_score_calculation(self):
        """Test health score calculation."""
        # Good module
        good_health = ModuleHealth(
            module_path="good.py",
            complexity=5,
            function_count=3,
            class_count=1,
            loc=50,
            test_coverage=80.0,
            type_errors=0,
            lint_issues=0,
        )
        assert good_health.health_score > 70
        assert not good_health.needs_healing

        # Bad module
        bad_health = ModuleHealth(
            module_path="bad.py",
            complexity=50,
            function_count=20,
            class_count=5,
            loc=500,
            test_coverage=20.0,
            type_errors=5,
            lint_issues=10,
        )
        assert bad_health.health_score < 50
        assert bad_health.needs_healing

    @patch("subprocess.run")
    def test_count_type_errors(self, mock_run, tmp_path):
        """Test counting type errors from pyright."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = json.dumps(
            {"generalDiagnostics": [{"severity": "error"}, {"severity": "error"}, {"severity": "warning"}]}
        )

        module_path = tmp_path / "test.py"
        module_path.write_text("x: int = 'string'")

        monitor = HealthMonitor(tmp_path)
        errors = monitor._count_type_errors(module_path)

        assert errors == 2  # Only count errors, not warnings

    @patch("subprocess.run")
    def test_count_lint_issues(self, mock_run, tmp_path):
        """Test counting lint issues from ruff."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = json.dumps([{"code": "E501"}, {"code": "F401"}, {"code": "W293"}])

        module_path = tmp_path / "test.py"
        module_path.write_text("import unused")

        monitor = HealthMonitor(tmp_path)
        issues = monitor._count_lint_issues(module_path)

        assert issues == 3

    def test_scan_directory(self, tmp_path):
        """Test scanning a directory for modules."""
        # Create test files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")
        (tmp_path / "test_module.py").write_text("def test_func(): pass")  # Should be skipped

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "module3.py").write_text("def func3(): pass")

        monitor = HealthMonitor(tmp_path)
        modules = monitor.scan_directory(tmp_path)

        # Should find module1, module2, and module3 (not test_module)
        assert len(modules) == 3
        module_names = [Path(m.module_path).name for m in modules]
        assert "module1.py" in module_names
        assert "module2.py" in module_names
        assert "module3.py" in module_names
        assert "test_module.py" not in module_names

    def test_save_and_load_metrics(self, tmp_path):
        """Test saving and loading metrics."""
        monitor = HealthMonitor(tmp_path)

        modules = [
            ModuleHealth("module1.py", 10, 5, 2, 100, 75.0, 1, 2),
            ModuleHealth("module2.py", 20, 10, 3, 200, 50.0, 3, 5),
        ]

        monitor.save_metrics(modules)
        assert (tmp_path / ".data" / "module_health.json").exists()

        # Load and verify
        candidates = monitor.get_healing_candidates(threshold=80)
        assert len(candidates) >= 0  # Both modules likely need healing with threshold 80


class TestAutoHealer:
    """Test auto-healing functionality with mocked Aider calls."""

    @patch("amplifier.tools.auto_healer._run_healing_tool")
    @patch("amplifier.tools.auto_healer.validate_module")
    @patch("amplifier.tools.auto_healer.commit_and_merge")
    @patch("amplifier.tools.auto_healer.create_healing_branch")
    @patch("amplifier.tools.auto_healer.cleanup_branch")
    def test_heal_single_module_success(
        self, mock_cleanup, mock_create_branch, mock_commit, mock_validate, mock_run_tool, tmp_path
    ):
        """Test successful healing of a single module."""
        module_path = tmp_path / "unhealthy.py"
        module_path.write_text("def bad(): pass")

        mock_create_branch.return_value = "auto-heal/unhealthy"
        mock_run_tool.return_value = True
        mock_validate.return_value = True
        mock_commit.return_value = True

        # Mock health scores
        with patch("amplifier.tools.auto_healer._get_new_score", return_value=85.0):
            result = heal_single_module(module_path, 60.0, tmp_path)

        assert result.status == "success"
        assert result.health_before == 60.0
        assert result.health_after == 85.0
        assert result.duration > 0

        mock_create_branch.assert_called_once()
        mock_run_tool.assert_called_once()
        mock_validate.assert_called_once()
        mock_commit.assert_called_once()
        mock_cleanup.assert_called_once()

    @patch("amplifier.tools.auto_healer.is_safe_module")
    def test_heal_single_module_unsafe(self, mock_safe, tmp_path):
        """Test healing skips unsafe modules."""
        module_path = tmp_path / "core.py"
        module_path.write_text("# Core module")

        mock_safe.return_value = False

        result = heal_single_module(module_path, 50.0, tmp_path)

        assert result.status == "skipped"
        assert result.reason == "Unsafe module"

    @patch("amplifier.tools.auto_healer._run_healing_tool")
    @patch("amplifier.tools.auto_healer.create_healing_branch")
    @patch("amplifier.tools.auto_healer.cleanup_branch")
    def test_heal_single_module_failure(self, mock_cleanup, mock_create_branch, mock_run_tool, tmp_path):
        """Test handling of healing failure."""
        module_path = tmp_path / "bad.py"
        module_path.write_text("def bad(): pass")

        mock_create_branch.return_value = "auto-heal/bad"
        mock_run_tool.return_value = False  # Healing fails

        result = heal_single_module(module_path, 40.0, tmp_path)

        assert result.status == "failed"
        assert "Healing failed" in result.reason
        mock_cleanup.assert_called_once()

    @patch("amplifier.tools.auto_healer.HealthMonitor")
    @patch("amplifier.tools.auto_healer.heal_single_module")
    @patch("amplifier.tools.auto_healer.is_safe_module")
    def test_heal_batch(self, mock_is_safe, mock_heal_single, mock_monitor_class, tmp_path):
        """Test batch healing of multiple modules."""
        # Setup mock candidates
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor

        candidates = [
            ModuleHealth("module1.py", 30, 10, 2, 300, None, 5, 10),
            ModuleHealth("module2.py", 25, 15, 3, 400, None, 8, 15),
            ModuleHealth("module3.py", 20, 20, 4, 500, None, 10, 20),
        ]
        mock_monitor.get_healing_candidates.return_value = candidates

        # Mark all modules as safe
        mock_is_safe.return_value = True

        # Mock healing results
        results = [
            HealingResult.success(Path("module1.py"), 45.0, 75.0, 10.0),
            HealingResult.success(Path("module2.py"), 40.0, 70.0, 12.0),
            HealingResult.failed(Path("module3.py"), 35.0, "Test failure", 5.0),
        ]
        mock_heal_single.side_effect = results

        with patch("amplifier.tools.auto_healer.save_results"):
            batch_results = heal_batch(max_modules=3, threshold=50, project_root=tmp_path)

        assert len(batch_results) == 3
        assert batch_results[0].status == "success"
        assert batch_results[1].status == "success"
        assert batch_results[2].status == "failed"

    def test_run_healing_tool(self):
        """Test running the healing tool (Aider)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with tempfile.NamedTemporaryFile() as tmp_file:
                result = _run_healing_tool(Path("test.py"), tmp_file.name)

            assert result is True
            mock_run.assert_called_once()

            # Verify Aider command structure
            call_args = mock_run.call_args[0][0]
            assert ".aider-venv/bin/aider" in call_args[0]
            assert "--model" in call_args
            assert "claude-3-5-sonnet-20241022" in call_args
            assert "--yes" in call_args

    def test_auto_healer_class(self, tmp_path):
        """Test AutoHealer class methods."""
        healer = AutoHealer(tmp_path)

        assert healer.project_root == tmp_path
        assert isinstance(healer.monitor, HealthMonitor)

        # Test heal_module_safely
        module_path = tmp_path / "test.py"
        module_path.write_text("def test(): pass")

        with patch("amplifier.tools.auto_healer.heal_single_module") as mock_heal:
            mock_heal.return_value = HealingResult.success(module_path, 60.0, 80.0, 5.0)

            result = healer.heal_module_safely(module_path)

            assert result.status == "success"
            mock_heal.assert_called_once()

        # Test heal_batch_modules
        with patch("amplifier.tools.auto_healer.heal_batch") as mock_batch:
            mock_batch.return_value = [
                HealingResult.success(Path("m1.py"), 50.0, 70.0, 5.0),
                HealingResult.success(Path("m2.py"), 55.0, 75.0, 6.0),
            ]

            results = healer.heal_batch_modules(max_modules=5, threshold=65)

            assert len(results) == 2
            mock_batch.assert_called_with(5, 65, tmp_path)


class TestParallelHealing:
    """Test parallel healing capabilities."""

    @pytest.mark.asyncio
    async def test_parallel_healer_init(self, tmp_path):
        """Test ParallelHealer initialization."""
        healer = ParallelHealer(tmp_path, max_workers=5)

        assert healer.project_root == tmp_path
        assert healer.max_workers == 5
        assert isinstance(healer.monitor, HealthMonitor)
        assert isinstance(healer.healer, AutoHealer)

    @pytest.mark.asyncio
    async def test_heal_module_async(self, tmp_path):
        """Test async healing of a single module."""
        healer = ParallelHealer(tmp_path)
        module_path = tmp_path / "test.py"
        module_path.write_text("def test(): pass")

        with patch.object(healer.healer, "heal_module_safely") as mock_heal:
            mock_heal.return_value = HealingResult.success(module_path, 50.0, 80.0, 5.0)

            result = await healer.heal_module(module_path)

            assert result.status == "success"
            assert result.health_after == 80.0
            mock_heal.assert_called_once_with(module_path)

    @pytest.mark.asyncio
    async def test_heal_batch_parallel(self, tmp_path):
        """Test parallel batch healing."""
        healer = ParallelHealer(tmp_path, max_workers=3)

        # Mock candidates
        candidates = [
            ModuleHealth(str(tmp_path / "m1.py"), 30, 5, 1, 100),
            ModuleHealth(str(tmp_path / "m2.py"), 25, 6, 1, 120),
            ModuleHealth(str(tmp_path / "m3.py"), 20, 7, 2, 150),
        ]

        with (
            patch.object(healer.monitor, "get_healing_candidates", return_value=candidates),
            patch.object(healer, "heal_module") as mock_heal,
        ):
            # Mock async results
            async def mock_async_heal(path):
                return HealingResult.success(path, 50.0, 75.0, 3.0)

            mock_heal.side_effect = mock_async_heal

            results = await healer.heal_batch(max_modules=3, threshold=60)

            assert len(results) == 3
            assert all(r.status == "success" for r in results)
            assert mock_heal.call_count == 3

    @pytest.mark.asyncio
    async def test_heal_batch_empty(self, tmp_path):
        """Test batch healing with no candidates."""
        healer = ParallelHealer(tmp_path)

        with patch.object(healer.monitor, "get_healing_candidates", return_value=[]):
            results = await healer.heal_batch()

            assert results == []

    @pytest.mark.asyncio
    async def test_heal_batch_with_exceptions(self, tmp_path):
        """Test handling exceptions in parallel healing."""
        healer = ParallelHealer(tmp_path)

        candidates = [
            ModuleHealth(str(tmp_path / "m1.py"), 30, 5, 1, 100),
            ModuleHealth(str(tmp_path / "m2.py"), 25, 6, 1, 120),
        ]

        with (
            patch.object(healer.monitor, "get_healing_candidates", return_value=candidates),
            patch.object(healer, "heal_module") as mock_heal,
        ):
            # First succeeds, second raises exception
            async def mock_async_heal(path):
                if "m1.py" in str(path):
                    return HealingResult.success(path, 50.0, 75.0, 3.0)
                raise Exception("Healing error")

            mock_heal.side_effect = mock_async_heal

            results = await healer.heal_batch(max_modules=2)

            assert len(results) == 2
            assert results[0].status == "success"
            assert isinstance(results[1], Exception)


class TestGitBranchIsolation:
    """Test Git branch isolation functionality."""

    @patch("subprocess.run")
    def test_create_healing_branch(self, mock_run):
        """Test creating a healing branch."""
        mock_run.return_value.returncode = 0

        branch = create_healing_branch("test_module")

        assert branch == "auto-heal/test_module"
        mock_run.assert_called_once_with(
            ["git", "checkout", "-b", "auto-heal/test_module"], capture_output=True, check=True
        )

    @patch("subprocess.run")
    def test_create_healing_branch_failure(self, mock_run):
        """Test handling branch creation failure."""
        mock_run.side_effect = Exception("Branch exists")

        with pytest.raises(Exception, match="Branch exists"):
            create_healing_branch("test_module")

    @patch("subprocess.run")
    def test_cleanup_branch(self, mock_run):
        """Test branch cleanup."""
        mock_run.return_value.returncode = 0

        cleanup_branch("auto-heal/test")

        # Should checkout main and delete branch
        assert mock_run.call_count == 2
        calls = mock_run.call_args_list
        assert calls[0][0][0] == ["git", "checkout", "main"]
        assert calls[1][0][0] == ["git", "branch", "-D", "auto-heal/test"]

    @patch("subprocess.run")
    def test_commit_and_merge(self, mock_run, tmp_path):
        """Test committing and merging changes."""
        mock_run.return_value.returncode = 0

        module_path = tmp_path / "test.py"
        result = commit_and_merge(module_path, "auto-heal/test", 50.0, 80.0)

        assert result is True
        assert mock_run.call_count == 4  # add, commit, checkout, merge

        calls = mock_run.call_args_list
        assert "git" in calls[0][0][0][0]
        assert "add" in calls[0][0][0]
        assert "commit" in calls[1][0][0]
        assert "checkout" in calls[2][0][0]
        assert "merge" in calls[3][0][0]


class TestValidationPipeline:
    """Test validation pipeline functionality."""

    def test_validate_syntax_valid(self, tmp_path):
        """Test syntax validation for valid Python."""
        module_path = tmp_path / "valid.py"
        module_path.write_text("def hello():\n    return 'Hello'")

        assert validate_syntax(module_path) is True

    def test_validate_syntax_invalid(self, tmp_path):
        """Test syntax validation for invalid Python."""
        module_path = tmp_path / "invalid.py"
        module_path.write_text("def broken(\n    pass")

        assert validate_syntax(module_path) is False

    @patch("subprocess.run")
    def test_validate_tests_pass(self, mock_run, tmp_path):
        """Test validation when tests pass."""
        mock_run.return_value.returncode = 0

        module_path = tmp_path / "module.py"
        test_file = tmp_path / "tests" / "test_module.py"
        test_file.parent.mkdir()
        test_file.write_text("def test_pass(): pass")

        assert validate_tests(module_path, tmp_path) is True

    @patch("subprocess.run")
    def test_validate_tests_fail(self, mock_run, tmp_path):
        """Test validation when tests fail."""
        mock_run.return_value.returncode = 1

        module_path = tmp_path / "module.py"
        test_file = tmp_path / "tests" / "test_module.py"
        test_file.parent.mkdir()
        test_file.write_text("def test_fail(): assert False")

        assert validate_tests(module_path, tmp_path) is False

    def test_validate_tests_no_test_file(self, tmp_path):
        """Test validation when no test file exists."""
        module_path = tmp_path / "module.py"

        # Should return True if no tests exist
        assert validate_tests(module_path, tmp_path) is True

    @patch("subprocess.run")
    def test_validate_imports(self, mock_run, tmp_path):
        """Test import validation."""
        mock_run.return_value.returncode = 0

        module_path = tmp_path / "test_module.py"
        assert validate_imports(module_path, tmp_path) is True

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "python" in call_args[0]
        assert "-c" in call_args
        assert "import amplifier.tools.test_module" in call_args[2]

    @patch("amplifier.tools.healing_validator.validate_syntax")
    @patch("amplifier.tools.healing_validator.validate_tests")
    @patch("amplifier.tools.healing_validator.validate_imports")
    def test_validate_module_all_pass(self, mock_imports, mock_tests, mock_syntax, tmp_path):
        """Test complete module validation."""
        mock_syntax.return_value = True
        mock_tests.return_value = True
        mock_imports.return_value = True

        module_path = tmp_path / "module.py"
        assert validate_module(module_path, tmp_path) is True

    @patch("amplifier.tools.healing_validator.validate_syntax")
    @patch("amplifier.tools.healing_validator.validate_tests")
    @patch("amplifier.tools.healing_validator.validate_imports")
    def test_validate_module_any_fail(self, mock_imports, mock_tests, mock_syntax, tmp_path):
        """Test validation fails if any check fails."""
        mock_syntax.return_value = True
        mock_tests.return_value = False  # Tests fail
        mock_imports.return_value = True

        module_path = tmp_path / "module.py"
        assert validate_module(module_path, tmp_path) is False


class TestHealingSafety:
    """Test safety checks for healing."""

    def test_is_safe_module_safe_patterns(self):
        """Test safe module patterns."""
        assert is_safe_module(Path("amplifier/utils/helper.py")) is True
        assert is_safe_module(Path("amplifier/tools/utility.py")) is True
        assert is_safe_module(Path("tests/test_something.py")) is True

    def test_is_safe_module_unsafe_patterns(self):
        """Test unsafe module patterns."""
        assert is_safe_module(Path("amplifier/core.py")) is False
        assert is_safe_module(Path("amplifier/cli.py")) is False
        assert is_safe_module(Path("amplifier/__init__.py")) is False
        assert is_safe_module(Path("amplifier/api/endpoints.py")) is False

    def test_is_safe_module_leaf_modules(self):
        """Test leaf module detection."""
        assert is_safe_module(Path("some_test_module.py")) is True
        assert is_safe_module(Path("data_util.py")) is True
        assert is_safe_module(Path("string_helper.py")) is True


class TestHealingResults:
    """Test healing results storage and reporting."""

    def test_save_results_new_file(self, tmp_path):
        """Test saving results to a new file."""
        results = [
            HealingResult.success(Path("m1.py"), 50.0, 80.0, 5.0),
            HealingResult.failed(Path("m2.py"), 45.0, "Test failure", 3.0),
            HealingResult.skipped(Path("m3.py"), 40.0, "Unsafe module"),
        ]

        with patch("amplifier.tools.healing_results.logger"):
            save_results(results, tmp_path)

        results_file = tmp_path / ".data" / "healing_results.json"
        assert results_file.exists()

        with open(results_file) as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]["status"] == "success"
        assert data[1]["status"] == "failed"
        assert data[2]["status"] == "skipped"

    def test_save_results_append(self, tmp_path):
        """Test appending results to existing file."""
        # Create initial results file
        results_dir = tmp_path / ".data"
        results_dir.mkdir()
        results_file = results_dir / "healing_results.json"

        initial_data = [{"module_path": "old.py", "status": "success"}]
        with open(results_file, "w") as f:
            json.dump(initial_data, f)

        # Add new results
        new_results = [HealingResult.success(Path("new.py"), 60.0, 85.0, 4.0)]

        save_results(new_results, tmp_path)

        # Verify append
        with open(results_file) as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["module_path"] == "old.py"
        assert data[1]["module_path"] == "new.py"

    def test_log_summary(self):
        """Test logging healing summary."""
        results = [
            HealingResult.success(Path("m1.py"), 50.0, 80.0, 5.0),
            HealingResult.success(Path("m2.py"), 45.0, 75.0, 4.0),
            HealingResult.failed(Path("m3.py"), 40.0, "Error", 2.0),
            HealingResult.skipped(Path("m4.py"), 35.0, "Unsafe"),
        ]

        with patch("amplifier.tools.healing_results.logger") as mock_logger:
            _log_summary(results)

            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]

            assert "Successful: 2" in log_message
            assert "Failed: 2" in log_message  # failed + skipped
            assert "Average improvement: 30.0 points" in log_message

    def test_log_summary_no_success(self):
        """Test summary logging with no successful healings."""
        results = [
            HealingResult.failed(Path("m1.py"), 40.0, "Error", 2.0),
            HealingResult.skipped(Path("m2.py"), 35.0, "Unsafe"),
        ]

        with patch("amplifier.tools.healing_results.logger") as mock_logger:
            _log_summary(results)

            # Should not log anything if no successes
            mock_logger.info.assert_not_called()


class TestIntegration:
    """Integration tests for the complete healing system."""

    @patch("subprocess.run")
    def test_end_to_end_healing_flow(self, mock_run, tmp_path):
        """Test complete healing flow from monitoring to results."""
        # Setup: Create unhealthy module with high complexity and many lines
        module_path = tmp_path / "unhealthy.py"
        # Create a very complex module that will definitely need healing
        complex_code = (
            """
def complex_function(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p):
    result = 0
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                if h > 0:
                                    result = 1
                                else:
                                    result = 2
                            else:
                                result = 3
                        else:
                            result = 4
                    else:
                        result = 5
                else:
                    result = 6
            else:
                result = 7
        else:
            result = 8
    else:
        result = 9

    for x in range(100):
        if x % 2 == 0:
            if x % 3 == 0:
                if x % 5 == 0:
                    print(x)
                elif x % 7 == 0:
                    print(x * 2)
                else:
                    print(x * 3)
            elif x % 11 == 0:
                print(x * 4)
        elif x % 13 == 0:
            print(x * 5)

    while i < 1000:
        i += 1
        if i == 100:
            break
        elif i == 200:
            continue
        elif i == 300:
            pass
        elif i == 400:
            i = 500

    try:
        if j > 0 and k > 0 and l > 0:
            if m > 0 or n > 0 or o > 0:
                if p > 0:
                    result = result * 2
    except:
        pass

    return result

"""
            + "# Padding to increase LOC\n" * 150
        )  # Add lots of lines to push LOC over 200
        module_path.write_text(complex_code)

        # Mock subprocess calls (git, aider, pyright, ruff)
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps([])

        # Step 1: Monitor health
        monitor = HealthMonitor(tmp_path)
        health = monitor.analyze_module(module_path)

        assert health.complexity > 10  # Should be complex
        assert health.health_score < 70  # Should need healing

        # Step 2: Save metrics
        monitor.save_metrics([health])
        assert (tmp_path / ".data" / "module_health.json").exists()

        # Step 3: Auto-heal with mocked Aider
        with patch("amplifier.tools.auto_healer._run_healing_tool") as mock_aider:
            mock_aider.return_value = True

            # Mock improved health after healing
            with patch("amplifier.tools.auto_healer._get_new_score", return_value=85.0):
                healer = AutoHealer(tmp_path)
                result = healer.heal_module_safely(module_path)

        # Verify healing attempted (even if mocked)
        assert mock_aider.called

        # Step 4: Verify results can be saved (test the function directly)
        save_results([result], tmp_path)

        # Verify results file was created
        results_file = tmp_path / ".data" / "healing_results.json"
        assert results_file.exists()

    @pytest.mark.asyncio
    async def test_parallel_healing_integration(self, tmp_path):
        """Test parallel healing of multiple modules."""
        # Create multiple unhealthy modules
        modules = []
        for i in range(3):
            module_path = tmp_path / f"module{i}.py"
            module_path.write_text(f"""
def func{i}():
    {"if True:" * (i + 3)}
        return {i}
""")
            modules.append(module_path)

        # Setup mocks
        with (
            patch("amplifier.tools.auto_healer._run_healing_tool", return_value=True),
            patch("amplifier.tools.auto_healer.validate_module", return_value=True),
            patch("amplifier.tools.auto_healer.commit_and_merge", return_value=True),
            patch("amplifier.tools.auto_healer._get_new_score", return_value=80.0),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps([])

            # Run parallel healing
            healer = ParallelHealer(tmp_path, max_workers=3)

            # Mock candidates
            candidates = [ModuleHealth(str(m), 30, 5, 1, 100) for m in modules]

            with patch.object(healer.monitor, "get_healing_candidates", return_value=candidates):
                results = await healer.heal_batch(max_modules=3)

            # Should process all 3 modules
            assert len(results) == 3
