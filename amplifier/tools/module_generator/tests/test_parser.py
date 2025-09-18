"""Tests for specification parser"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from ..parser import parse_contract
from ..parser import parse_implementation


@pytest.mark.asyncio
async def test_parse_contract():
    """Test parsing contract specification"""
    # Create a sample contract file
    contract_content = """# Module Contract: TestModule

## Purpose
This module provides test functionality.

## Public Interface
- def process_data(data: dict) -> dict
- class DataProcessor

## Dependencies
- pydantic
- click
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_contract.md", delete=False, prefix="testmodule") as f:
        f.write(contract_content)
        f.flush()
        contract_path = Path(f.name)

    try:
        spec = await parse_contract(contract_path)

        # Just verify basic structure is created
        assert spec.module_name
        assert isinstance(spec.inputs, dict)
        assert isinstance(spec.outputs, dict)
        assert isinstance(spec.side_effects, list)
        assert isinstance(spec.dependencies, list)
        assert isinstance(spec.public_interface, list)
    finally:
        contract_path.unlink()


@pytest.mark.asyncio
async def test_parse_implementation():
    """Test parsing implementation specification"""
    impl_content = """# Implementation Specification: TestModule

## Design Overview
The module uses a simple pipeline architecture.

## Key Algorithms
- Fast sorting algorithm
- Caching strategy for repeated operations

## Testing Strategy
Use pytest with comprehensive coverage.
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_impl_spec.md", delete=False, prefix="testmodule") as f:
        f.write(impl_content)
        f.flush()
        impl_path = Path(f.name)

    try:
        spec = await parse_implementation(impl_path)

        # Just verify basic structure is created
        assert spec.module_name
        assert isinstance(spec.architecture, str)
        assert isinstance(spec.key_algorithms, list)
        assert isinstance(spec.data_models, dict)
        assert isinstance(spec.processing_flow, list)
    finally:
        impl_path.unlink()


def test_parse_contract_sync():
    """Test sync wrapper for contract parsing"""
    # Create a sample contract file
    contract_content = """# Module Contract: SyncTest

## Purpose
Test synchronous parsing.
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix="_contract.md", delete=False, prefix="synctest") as f:
        f.write(contract_content)
        f.flush()
        contract_path = Path(f.name)

    try:
        # Use asyncio.run to test sync behavior
        spec = asyncio.run(parse_contract(contract_path))
        assert spec.module_name
        assert isinstance(spec.purpose, str)
    finally:
        contract_path.unlink()
