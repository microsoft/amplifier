"""Specification validator for module contracts and specs.

This module validates YAML contract and spec files before generation,
ensuring they are well-formed, complete, and within token limits.
"""

from pathlib import Path
from typing import Any

import yaml

from module_generator.core.file_io import read_yaml


class ValidationResult:
    """Result of validation with errors, warnings and token count."""

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.token_count: int = 0

    def add_error(self, message: str) -> None:
        """Add an error message and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message (doesn't affect validity)."""
        self.warnings.append(message)


def estimate_tokens(text: str) -> int:
    """Estimate token count for text (roughly 1 token ≈ 4 characters).

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # Standard approximation: 1 token ≈ 4 characters
    return len(text) // 4


def validate_contract(contract_dict: dict[str, Any]) -> ValidationResult:
    """Validate a contract dictionary for required fields and structure.

    Args:
        contract_dict: Parsed contract YAML data

    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()

    # Check required top-level sections
    if "module" not in contract_dict:
        result.add_error("Missing required section: module")
    if "interface" not in contract_dict:
        result.add_error("Missing required section: interface")
    if "dependencies" not in contract_dict:
        result.add_error("Missing required section: dependencies")

    # Validate module section
    module = contract_dict.get("module", {})
    if module:
        # Check module.name
        module_name = module.get("name")
        if not module_name:
            result.add_error("Missing required field: module.name")
        elif not isinstance(module_name, str):
            result.add_error("module.name must be a string")
        elif not module_name.replace("_", "").replace(".", "").isalnum():
            result.add_error("module.name must contain only alphanumeric characters, underscores, and dots")

        # Check module.version
        version = module.get("version")
        if not version:
            result.add_error("Missing required field: module.version")
        elif not isinstance(version, str):
            result.add_error("module.version must be a string")

        # Check module.purpose (formerly description)
        purpose = module.get("purpose")
        if not purpose:
            result.add_error("Missing required field: module.purpose")
        elif not isinstance(purpose, str):
            result.add_error("module.purpose must be a string")
        elif len(purpose) < 10:
            result.add_warning("module.purpose is very short (< 10 characters)")

    # Validate interface section
    interface = contract_dict.get("interface", {})
    if interface:
        # Validate inputs
        inputs = interface.get("inputs", [])
        if not isinstance(inputs, list):
            result.add_error("interface.inputs must be a list")
        else:
            for i, input_spec in enumerate(inputs):
                if not isinstance(input_spec, dict):
                    result.add_error(f"Input {i} must be a dictionary")
                    continue

                # Check required input fields
                if "name" not in input_spec:
                    result.add_error(f"Input {i} missing 'name' field")
                if "type" not in input_spec:
                    result.add_error(f"Input {i} missing 'type' field")

                # Optional but recommended fields
                if "validation" not in input_spec:
                    result.add_warning(f"Input '{input_spec.get('name', i)}' has no validation rules")

        # Validate outputs
        outputs = interface.get("outputs", [])
        if not isinstance(outputs, list):
            result.add_error("interface.outputs must be a list")
        else:
            for i, output_spec in enumerate(outputs):
                if not isinstance(output_spec, dict):
                    result.add_error(f"Output {i} must be a dictionary")
                    continue

                # Check required output fields
                if "name" not in output_spec:
                    result.add_error(f"Output {i} missing 'name' field")
                if "schema" not in output_spec and "type" not in output_spec:
                    result.add_error(f"Output {i} must have either 'schema' or 'type' field")

        # Validate errors
        errors = interface.get("errors", [])
        if not isinstance(errors, list):
            result.add_error("interface.errors must be a list")
        else:
            for i, error_spec in enumerate(errors):
                if not isinstance(error_spec, dict):
                    result.add_error(f"Error {i} must be a dictionary")
                    continue

                # Check required error fields
                if "code" not in error_spec:
                    result.add_error(f"Error {i} missing 'code' field")
                if "message_template" not in error_spec:
                    result.add_error(f"Error {i} missing 'message_template' field")

        # Check for side_effects (optional)
        side_effects = interface.get("side_effects")
        if side_effects and not isinstance(side_effects, list):
            result.add_error("interface.side_effects must be a list")

    # Validate dependencies section
    deps = contract_dict.get("dependencies", {})
    if deps:
        # Handle both list (simple format) and dict (with external/internal) formats
        if isinstance(deps, list):
            # Simple list format - treat as external dependencies
            if not deps:
                result.add_warning("No dependencies specified - module may be too simple")
        elif isinstance(deps, dict):
            # Dict format with external/internal keys
            external = deps.get("external", [])
            if not isinstance(external, list):
                result.add_error("dependencies.external must be a list")
            elif not external:
                result.add_warning("No external dependencies specified - module may be too simple")

            # Check internal dependencies (optional)
            internal = deps.get("internal", [])
            if internal and not isinstance(internal, list):
                result.add_error("dependencies.internal must be a list")
        else:
            result.add_error("dependencies must be either a list or a dict with 'external' and/or 'internal' keys")

    # Estimate token count for contract
    contract_yaml = yaml.dump(contract_dict, default_flow_style=False)
    result.token_count = estimate_tokens(contract_yaml)

    return result


def validate_spec(spec_dict: dict[str, Any]) -> ValidationResult:
    """Validate a specification dictionary for required fields and structure.

    Args:
        spec_dict: Parsed specification YAML data

    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()

    # Check required top-level sections
    if "implementation" not in spec_dict:
        result.add_error("Missing required section: implementation")

    # Validate implementation section
    implementation = spec_dict.get("implementation", {})
    if implementation:
        # Check implementation.behaviors
        behaviors = implementation.get("behaviors", [])
        if not isinstance(behaviors, list):
            result.add_error("implementation.behaviors must be a list")
        elif not behaviors:
            result.add_error("implementation.behaviors list cannot be empty")
        else:
            for i, behavior in enumerate(behaviors):
                if not isinstance(behavior, str | dict):
                    result.add_error(f"Behavior {i} must be a string or dictionary")

    # Validate algorithms (optional but check if present)
    if "algorithms" in implementation:
        algorithms = implementation["algorithms"]
        if not isinstance(algorithms, list):
            result.add_error("algorithms must be a list")
        else:
            # Check each algorithm entry
            for i, alg_spec in enumerate(algorithms):
                if not isinstance(alg_spec, dict):
                    result.add_warning(f"Algorithm {i} should be a dictionary")
                elif "operation" not in alg_spec:
                    result.add_warning(f"Algorithm {i} missing 'operation' field")

    # Validate data_flow
    data_flow = implementation.get("data_flow", [])
    if not isinstance(data_flow, list):
        result.add_error("data_flow must be a list")
    elif not data_flow:
        result.add_error("data_flow list cannot be empty")
    else:
        for i, step in enumerate(data_flow):
            if not isinstance(step, dict):
                result.add_error(f"Data flow step {i} must be a dictionary")
            elif "step" not in step:
                result.add_error(f"Data flow step {i} missing 'step' field")

    # Validate test_requirements section
    test_requirements = implementation.get("test_requirements", [])
    if test_requirements:
        # test_requirements is a list of test categories
        if not isinstance(test_requirements, list):
            result.add_error("test_requirements must be a list")
        else:
            # Check that we have some test categories
            if not test_requirements:
                result.add_warning("No test requirements specified")
            else:
                # Validate each test category
                for i, test_cat in enumerate(test_requirements):
                    if not isinstance(test_cat, dict):
                        result.add_error(f"Test requirement {i} must be a dictionary")
                    else:
                        if "category" not in test_cat:
                            result.add_error(f"Test requirement {i} missing 'category' field")
                        if "coverage" not in test_cat:
                            result.add_warning(f"Test requirement {i} missing 'coverage' field")

    # Check non_functional requirements (optional but recommended)
    non_functional = implementation.get("non_functional", {})
    if not non_functional:
        result.add_warning("No non_functional requirements specified")
    else:
        # Check performance
        performance = non_functional.get("performance", [])
        if performance and not isinstance(performance, list):
            result.add_error("non_functional.performance must be a list")
        elif not performance:
            result.add_warning("No performance requirements specified")

        # Check security
        security = non_functional.get("security", [])
        if security and not isinstance(security, list):
            result.add_error("non_functional.security must be a list")
        elif not security:
            result.add_warning("No security considerations specified")

    # Estimate token count for spec
    spec_yaml = yaml.dump(spec_dict, default_flow_style=False)
    result.token_count = estimate_tokens(spec_yaml)

    return result


def check_alignment(contract_dict: dict[str, Any], spec_dict: dict[str, Any]) -> ValidationResult:
    """Check alignment between contract and specification.

    Args:
        contract_dict: Parsed contract YAML data
        spec_dict: Parsed specification YAML data

    Returns:
        ValidationResult with alignment issues
    """
    result = ValidationResult()

    # Get module name from nested structure
    contract_module_name = contract_dict.get("module", {}).get("name")
    spec_module_name = spec_dict.get("module", {}).get("name")

    # Check that spec references correct module (if spec has module section)
    if spec_module_name and contract_module_name and spec_module_name != contract_module_name:
        result.add_error(
            f"Module name mismatch: contract says '{contract_module_name}', spec says '{spec_module_name}'"
        )

    # Check that spec addresses all inputs from contract
    interface = contract_dict.get("interface", {})
    inputs = interface.get("inputs", [])
    if inputs and isinstance(inputs, list):
        contract_input_names = {inp.get("name") for inp in inputs if isinstance(inp, dict) and "name" in inp}

        # Look for input handling in spec behaviors or data_flow
        spec_content = yaml.dump(spec_dict, default_flow_style=False).lower()
        for input_name in contract_input_names:
            if input_name and input_name.lower() not in spec_content:
                result.add_warning(f"Input '{input_name}' from contract not mentioned in spec")

    # Check that spec addresses all outputs from contract
    outputs = interface.get("outputs", [])
    if outputs and isinstance(outputs, list):
        contract_output_names = {out.get("name") for out in outputs if isinstance(out, dict) and "name" in out}

        spec_content = yaml.dump(spec_dict, default_flow_style=False).lower()
        for output_name in contract_output_names:
            if output_name and output_name.lower() not in spec_content:
                result.add_warning(f"Output '{output_name}' from contract not mentioned in spec")

    # Check that spec addresses error handling
    errors = interface.get("errors", [])
    if errors and isinstance(errors, list):
        spec_content = yaml.dump(spec_dict, default_flow_style=False).lower()
        # Look for error handling mentions
        error_keywords = ["error", "exception", "failure", "validation", "handle"]
        has_error_handling = any(keyword in spec_content for keyword in error_keywords)

        if not has_error_handling:
            result.add_warning("Contract defines errors but spec doesn't mention error handling")

    # Check dependencies alignment
    contract_deps_section = contract_dict.get("dependencies", {})
    if contract_deps_section:
        # Get external dependencies from contract
        # Handle both list and dict formats
        if isinstance(contract_deps_section, list):
            # Simple list format - treat as external dependencies
            all_contract_deps = {
                dep.get("name", dep) if isinstance(dep, dict) else dep for dep in contract_deps_section
            }
            contract_external = all_contract_deps
            contract_internal = set()
        elif isinstance(contract_deps_section, dict):
            contract_external = set(contract_deps_section.get("external", []))
            contract_internal = set(contract_deps_section.get("internal", []))
            all_contract_deps = contract_external | contract_internal
        else:
            all_contract_deps = set()
            contract_external = set()
            contract_internal = set()

        # Check if spec has dependencies section
        spec_deps_section = spec_dict.get("dependencies", {})
        if spec_deps_section:
            # Handle both list and dict formats for spec too
            if isinstance(spec_deps_section, list):
                all_spec_deps = {dep.get("name", dep) if isinstance(dep, dict) else dep for dep in spec_deps_section}
                spec_external = all_spec_deps
                spec_internal = set()
            elif isinstance(spec_deps_section, dict):
                spec_external = set(spec_deps_section.get("external", []))
                spec_internal = set(spec_deps_section.get("internal", []))
                all_spec_deps = spec_external | spec_internal
            else:
                all_spec_deps = set()
                spec_external = set()
                spec_internal = set()

            # Dependencies in contract but not in spec
            missing_in_spec = all_contract_deps - all_spec_deps
            for dep in missing_in_spec:
                result.add_warning(f"Dependency '{dep}' in contract but not in spec")

            # Dependencies in spec but not in contract
            extra_in_spec = all_spec_deps - all_contract_deps
            for dep in extra_in_spec:
                result.add_warning(f"Dependency '{dep}' in spec but not in contract")

    return result


def validate_files(contract_path: Path | str, spec_path: Path | str) -> ValidationResult:
    """Main entry point for validating contract and spec files.

    Args:
        contract_path: Path to contract YAML file
        spec_path: Path to specification YAML file

    Returns:
        Combined ValidationResult with all issues
    """
    result = ValidationResult()

    # Convert to Path objects
    contract_path = Path(contract_path)
    spec_path = Path(spec_path)

    # Check files exist
    if not contract_path.exists():
        result.add_error(f"Contract file not found: {contract_path}")
        return result

    if not spec_path.exists():
        result.add_error(f"Spec file not found: {spec_path}")
        return result

    # Read contract file
    try:
        contract_dict = read_yaml(contract_path)
    except yaml.YAMLError as e:
        result.add_error(f"Contract file has invalid YAML: {e}")
        return result
    except Exception as e:
        result.add_error(f"Failed to read contract file: {e}")
        return result

    # Read spec file
    try:
        spec_dict = read_yaml(spec_path)
    except yaml.YAMLError as e:
        result.add_error(f"Spec file has invalid YAML: {e}")
        return result
    except Exception as e:
        result.add_error(f"Failed to read spec file: {e}")
        return result

    # Validate contract
    contract_result = validate_contract(contract_dict)
    result.errors.extend(contract_result.errors)
    result.warnings.extend(contract_result.warnings)
    total_tokens = contract_result.token_count

    # Validate spec
    spec_result = validate_spec(spec_dict)
    result.errors.extend(spec_result.errors)
    result.warnings.extend(spec_result.warnings)
    total_tokens += spec_result.token_count

    # Check alignment
    alignment_result = check_alignment(contract_dict, spec_dict)
    result.errors.extend(alignment_result.errors)
    result.warnings.extend(alignment_result.warnings)

    # Set total token count
    result.token_count = total_tokens

    # Check token limit (15,000 tokens)
    if total_tokens > 15000:
        result.add_error(
            f"Combined token count ({total_tokens}) exceeds limit of 15,000. "
            "Consider simplifying the contract/spec or splitting into smaller modules."
        )
    elif total_tokens > 12000:
        result.add_warning(
            f"Combined token count ({total_tokens}) is close to 15,000 limit. Consider keeping specs concise."
        )

    # Update is_valid based on errors
    result.is_valid = len(result.errors) == 0

    return result
