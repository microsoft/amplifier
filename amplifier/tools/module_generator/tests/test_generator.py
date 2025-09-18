"""Tests for module generator"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from ..generator import ModuleGenerator
from ..models import ContractSpec
from ..models import ImplementationSpec


@pytest.mark.asyncio
async def test_generator_with_mock():
    """Test module generation with mock generator"""
    # Create sample specifications
    contract_spec = ContractSpec(
        module_name="test_module",
        purpose="Test module for unit testing",
        inputs={"data": "Input data dictionary"},
        outputs={"result": "Processed result"},
        side_effects=[],
        dependencies=["pydantic"],
        public_interface=["process", "TestClass"],
        invariants=[],
        error_handling={},
        performance_specs={},
    )

    impl_spec = ImplementationSpec(
        module_name="test_module",
        architecture="Simple pipeline architecture",
        key_algorithms=["Basic processing"],
        data_models={},
        processing_flow=[],
        testing_strategy="Use pytest",
        error_handling_details="",
        performance_optimizations=[],
        security_considerations=[],
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        generator = ModuleGenerator(output_dir=temp_dir, permission_mode="acceptEdits")

        # Generate the module
        results = await generator.generate(contract_spec, impl_spec)

        # Check results
        assert results["module_name"] == "test_module"
        assert len(results["files_generated"]) > 0
        assert len(results["errors"]) == 0

        # Check that files were created
        module_path = Path(temp_dir) / "test_module"
        assert module_path.exists()
        assert (module_path / "__init__.py").exists()
        assert (module_path / "README.md").exists()
        assert (module_path / "core.py").exists()


@pytest.mark.asyncio
async def test_generator_plan_mode():
    """Test generator in plan-only mode"""
    contract_spec = ContractSpec(
        module_name="plan_test",
        purpose="Test planning mode",
        inputs={},
        outputs={},
        side_effects=[],
        dependencies=[],
        public_interface=[],
        invariants=[],
        error_handling={},
        performance_specs={},
    )

    impl_spec = ImplementationSpec(
        module_name="plan_test",
        architecture="Test architecture",
        key_algorithms=[],
        data_models={},
        processing_flow=[],
        testing_strategy="",
        error_handling_details="",
        performance_optimizations=[],
        security_considerations=[],
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        generator = ModuleGenerator(output_dir=temp_dir, permission_mode="plan")

        # Analyze only
        results = await generator.generate(contract_spec, impl_spec, analyze_only=True)

        # Check analysis results
        assert results["analysis"] is not None
        assert results["analysis"]["feasibility"] in ["simple", "moderate", "complex"]
        assert len(results["files_generated"]) == 0  # No files in plan mode

        # Check that no files were created
        module_path = Path(temp_dir) / "plan_test"
        assert not module_path.exists()


def test_generator_sync():
    """Test sync wrapper for generator"""
    contract_spec = ContractSpec(
        module_name="sync_test",
        purpose="Test sync operation",
        inputs={},
        outputs={},
        side_effects=[],
        dependencies=[],
        public_interface=[],
        invariants=[],
        error_handling={},
        performance_specs={},
    )

    impl_spec = ImplementationSpec(
        module_name="sync_test",
        architecture="Simple",
        key_algorithms=[],
        data_models={},
        processing_flow=[],
        testing_strategy="",
        error_handling_details="",
        performance_optimizations=[],
        security_considerations=[],
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        generator = ModuleGenerator(output_dir=temp_dir, permission_mode="plan")

        # Use asyncio.run for sync test
        results = asyncio.run(generator.generate(contract_spec, impl_spec, analyze_only=True))

        assert results["module_name"] == "sync_test"
        assert results["analysis"] is not None
