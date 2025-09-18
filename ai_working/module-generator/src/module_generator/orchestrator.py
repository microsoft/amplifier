"""Module generation orchestrator.

Coordinates all phases of module generation with checkpoint recovery support.
"""

import logging
from pathlib import Path

from module_generator.core.file_io import read_yaml
from module_generator.core.file_io import write_text
from module_generator.core.state import GenerationState

# PhaseStatus not needed - using strings for phase tracking
from module_generator.generators.implementation_generator import ImplementationGenerator
from module_generator.generators.interface_generator import InterfaceGenerator
from module_generator.models import GeneratorContext
from module_generator.validators.spec_validator import validate_files

logger = logging.getLogger(__name__)


class ModuleOrchestrator:
    """Orchestrates module generation through all phases."""

    def __init__(self, state: GenerationState, timeout: int = 300):
        """Initialize orchestrator with generation state.

        Args:
            state: Generation state for checkpoint recovery
            timeout: Timeout for Claude SDK operations (default: 300)
        """
        self.state = state
        self.timeout = timeout
        # Validator function will be used directly
        self.interface_generator = InterfaceGenerator(timeout=timeout)
        self.implementation_generator = ImplementationGenerator(timeout=timeout)

    async def generate_module(self, contract_path: Path, spec_path: Path, output_dir: Path) -> None:
        """Generate module through all phases.

        Args:
            contract_path: Path to contract JSON file
            spec_path: Path to implementation spec JSON file
            output_dir: Directory to write generated module
        """
        logger.info("Starting module generation")
        logger.info(f"Contract: {contract_path}")
        logger.info(f"Spec: {spec_path}")
        logger.info(f"Output: {output_dir}")

        # Store paths in state for recovery
        self.state.add_artifact("contract_path", str(contract_path))
        self.state.add_artifact("spec_path", str(spec_path))
        self.state.add_artifact("output_dir", str(output_dir))

        try:
            # Phase 1: Validation
            if not self._is_phase_complete("validation"):
                await self._run_validation_phase(contract_path, spec_path)
            else:
                logger.info("Skipping validation phase - already complete")

            # Phase 2: Interface Generation
            if not self._is_phase_complete("interface"):
                await self._run_interface_phase(contract_path, output_dir)
            else:
                logger.info("Skipping interface phase - already complete")

            # Phase 3: Implementation Generation
            if not self._is_phase_complete("implementation"):
                await self._run_implementation_phase(contract_path, spec_path, output_dir)
            else:
                logger.info("Skipping implementation phase - already complete")

            # Phase 4: Assembly
            if not self._is_phase_complete("assembly"):
                await self._run_assembly_phase(output_dir)
            else:
                logger.info("Skipping assembly phase - already complete")

            logger.info("Module generation complete!")

        except Exception as e:
            logger.error(f"Module generation failed: {e}")
            raise

    async def _run_validation_phase(self, contract_path: Path, spec_path: Path) -> None:
        """Run validation phase.

        Args:
            contract_path: Path to contract JSON file
            spec_path: Path to implementation spec JSON file
        """
        logger.info("Starting validation phase...")

        try:
            # Validate both files
            logger.info("Validating contract and specification...")
            validation_result = validate_files(contract_path, spec_path)

            if not validation_result.is_valid:
                error_msg = "; ".join(validation_result.errors)
                raise ValueError(f"Validation failed: {error_msg}")

            logger.info("Validation passed")

            # Log warnings if any
            for warning in validation_result.warnings:
                logger.warning(f"Validation warning: {warning}")

            # Mark phase complete
            self._mark_phase_complete("validation")
            logger.info("Validation phase complete")

        except Exception as e:
            self._mark_phase_failed("validation", str(e))
            raise

    async def _run_interface_phase(self, contract_path: Path, output_dir: Path) -> None:
        """Run interface generation phase.

        Args:
            contract_path: Path to contract JSON file
            output_dir: Directory to write generated module
        """
        logger.info("Starting interface generation phase...")

        try:
            # Read contract
            contract = read_yaml(contract_path)

            # Create generator context with module name from nested structure
            module_info = contract.get("module", {})
            module_name = module_info.get("name", "generated_module")
            context = GeneratorContext(name=module_name, output_dir=output_dir, contract=contract, spec=None)

            # Generate interface
            logger.info("Generating module interface...")
            interface_code = await self.interface_generator.generate(context)

            # Store generated interface in state for assembly
            # Store generated files in artifacts
            generated_files = self.state.get_artifact("generated_files") or {}
            generated_files["__init__.py"] = interface_code
            self.state.add_artifact("generated_files", generated_files)

            # Mark phase complete
            self._mark_phase_complete("interface")
            logger.info("Interface generation phase complete")

        except Exception as e:
            self._mark_phase_failed("interface", str(e))
            raise

    async def _run_implementation_phase(self, contract_path: Path, spec_path: Path, output_dir: Path) -> None:
        """Run implementation generation phase.

        Args:
            contract_path: Path to contract JSON file
            spec_path: Path to implementation spec JSON file
            output_dir: Directory to write generated module
        """
        logger.info("Starting implementation generation phase...")

        try:
            # Read contract and spec
            contract = read_yaml(contract_path)
            spec = read_yaml(spec_path)

            # Create generator context with both contract and spec
            module_info = contract.get("module", {})
            module_name = module_info.get("name", "generated_module")
            context = GeneratorContext(name=module_name, output_dir=output_dir, contract=contract, spec=spec)

            # Generate implementation files
            logger.info("Generating module implementation...")
            implementation_files = await self.implementation_generator.generate(context)

            # Store generated files in state for assembly
            generated_files = self.state.get_artifact("generated_files") or {}
            generated_files.update(implementation_files)
            self.state.add_artifact("generated_files", generated_files)

            # Mark phase complete
            self._mark_phase_complete("implementation")
            logger.info("Implementation generation phase complete")

        except Exception as e:
            self._mark_phase_failed("implementation", str(e))
            raise

    async def _run_assembly_phase(self, output_dir: Path) -> None:
        """Run assembly phase - write generated files.

        Args:
            output_dir: Directory to write generated module
        """
        logger.info("Starting assembly phase...")

        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)

            # Write all generated files
            files_written = 0
            generated_files = self.state.get_artifact("generated_files") or {}
            for filename, content in generated_files.items():
                file_path = output_dir / filename

                # Create subdirectories if needed
                if "/" in filename:
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                logger.info(f"Writing {file_path}")
                write_text(content, file_path)
                files_written += 1

            logger.info(f"Wrote {files_written} files to {output_dir}")

            # Mark phase complete
            self._mark_phase_complete("assembly")
            logger.info("Assembly phase complete")

        except Exception as e:
            self._mark_phase_failed("assembly", str(e))
            raise

    def _is_phase_complete(self, phase: str) -> bool:
        """Check if a phase is complete.

        Args:
            phase: Phase name to check

        Returns:
            True if phase is complete
        """
        phases = self.state.get_artifact("phases") or {}
        phase_state = phases.get(phase, {})
        return phase_state.get("status") == "completed"

    def _mark_phase_complete(self, phase: str) -> None:
        """Mark a phase as complete and save state.

        Args:
            phase: Phase name to mark complete
        """
        self.state.mark_phase_complete(phase)
        self.state.save()
        logger.debug(f"Phase '{phase}' marked complete and state saved")

    def _mark_phase_failed(self, phase: str, error: str) -> None:
        """Mark a phase as failed and save state.

        Args:
            phase: Phase name to mark failed
            error: Error message
        """
        phases = self.state.get_artifact("phases") or {}
        if phase not in phases:
            phases[phase] = {}

        phases[phase]["status"] = "failed"
        phases[phase]["error"] = error
        self.state.add_artifact("phases", phases)
        self.state.save()
        logger.error(f"Phase '{phase}' failed: {error}")

    async def resume(self) -> None:
        """Resume generation from saved state."""
        if not all(
            [
                self.state.get_artifact("contract_path"),
                self.state.get_artifact("spec_path"),
                self.state.get_artifact("output_dir"),
            ]
        ):
            raise ValueError("Cannot resume - missing required paths in state")

        logger.info("Resuming module generation from saved state")

        # Resume with saved paths - we already checked they exist
        contract_path = self.state.get_artifact("contract_path")
        spec_path = self.state.get_artifact("spec_path")
        output_dir = self.state.get_artifact("output_dir")

        # Type check for safety (should never happen due to earlier check)
        if not contract_path or not spec_path or not output_dir:
            raise ValueError("Missing paths in state after validation")

        await self.generate_module(Path(contract_path), Path(spec_path), Path(output_dir))
