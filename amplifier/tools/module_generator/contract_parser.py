"""
Enhanced contract parser that extracts structured requirements from module contracts.

This parser identifies:
- Required functions with signatures
- Required classes and methods
- Data models with all fields
- Error types
- Dependencies
- Configuration parameters
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class FunctionSignature:
    """Represents a function signature from the contract."""

    name: str
    params: list[tuple[str, str]]  # (param_name, type_hint)
    return_type: str | None = None
    is_async: bool = False
    description: str = ""


@dataclass
class ClassDefinition:
    """Represents a class definition from the contract."""

    name: str
    methods: list[FunctionSignature]
    attributes: list[tuple[str, str, Any]]  # (attr_name, type_hint, default)
    description: str = ""


@dataclass
class DataModel:
    """Represents a data model/schema from the contract."""

    name: str
    fields: list[DataField]
    description: str = ""
    json_schema: bool = False


@dataclass
class DataField:
    """Represents a field in a data model."""

    name: str
    type_hint: str
    required: bool = True
    default: Any = None
    description: str = ""
    constraints: list[str] = field(default_factory=list)


@dataclass
class ErrorType:
    """Represents an error/exception type."""

    name: str
    description: str = ""


@dataclass
class Dependency:
    """Represents an external dependency."""

    name: str
    version: str | None = None
    usage: str = ""


@dataclass
class ContractRequirements:
    """Structured requirements extracted from a contract."""

    module_name: str
    purpose: str
    functions: list[FunctionSignature]
    classes: list[ClassDefinition]
    data_models: list[DataModel]
    errors: list[ErrorType]
    dependencies: list[Dependency]
    inputs: list[DataField]
    outputs: list[DataField]
    config_params: list[DataField]
    invariants: list[str]
    side_effects: list[str]


class EnhancedContractParser:
    """Parse contracts to extract structured requirements."""

    def __init__(self, contract_text: str):
        self.text = contract_text
        self.lines = contract_text.split("\n")

    def parse(self) -> ContractRequirements:
        """Parse the contract and extract all requirements."""
        return ContractRequirements(
            module_name=self._extract_module_name(),
            purpose=self._extract_purpose(),
            functions=self._extract_functions(),
            classes=self._extract_classes(),
            data_models=self._extract_data_models(),
            errors=self._extract_errors(),
            dependencies=self._extract_dependencies(),
            inputs=self._extract_inputs(),
            outputs=self._extract_outputs(),
            config_params=self._extract_config_params(),
            invariants=self._extract_invariants(),
            side_effects=self._extract_side_effects(),
        )

    def _extract_module_name(self) -> str:
        """Extract module name from header."""
        header_pattern = re.compile(r"^#\s*(?:Module\s*(?:Contract)?:?)?\s*(.+)$", re.M | re.I)
        match = header_pattern.search(self.text)
        if match:
            name = match.group(1).strip()
            # Clean up the name
            name = re.sub(r"[^a-zA-Z0-9\s_-]", "", name)
            name = re.sub(r"\s+", "_", name)
            return name.lower()
        return "unknown_module"

    def _extract_purpose(self) -> str:
        """Extract purpose statement."""
        purpose_pattern = re.compile(r"^##\s*Purpose\s*\n(.+?)(?:\n##|\Z)", re.S | re.M | re.I)
        match = purpose_pattern.search(self.text)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_functions(self) -> list[FunctionSignature]:
        """Extract function signatures from contract."""
        functions = []

        # Look for function definitions in code blocks
        code_block_pattern = re.compile(r"```(?:python)?\n(.+?)\n```", re.S)
        for code_match in code_block_pattern.finditer(self.text):
            code = code_match.group(1)

            # Find function definitions
            func_pattern = re.compile(r"(async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?\s*:")
            for func_match in func_pattern.finditer(code):
                is_async = bool(func_match.group(1))
                name = func_match.group(2)
                params_str = func_match.group(3)
                return_type = func_match.group(4)

                # Skip private functions
                if name.startswith("_"):
                    continue

                # Parse parameters
                params = []
                if params_str.strip():
                    for param in params_str.split(","):
                        param = param.strip()
                        if ":" in param:
                            param_name, param_type = param.split(":", 1)
                            param_name = param_name.strip()
                            param_type = param_type.strip()
                            # Remove default values
                            if "=" in param_type:
                                param_type = param_type.split("=")[0].strip()
                            params.append((param_name, param_type))
                        elif param and param != "self":
                            params.append((param, "Any"))

                functions.append(
                    FunctionSignature(
                        name=name,
                        params=params,
                        return_type=return_type.strip() if return_type else None,
                        is_async=is_async,
                    )
                )

        # Also look for function descriptions in text
        func_desc_pattern = re.compile(r"`(\w+)\s*\([^)]*\)`\s*[:-]?\s*(.+?)(?:\n|$)")
        for match in func_desc_pattern.finditer(self.text):
            func_name = match.group(1)
            description = match.group(2)

            # Check if we already have this function
            existing = next((f for f in functions if f.name == func_name), None)
            if existing:
                existing.description = description
            elif not func_name.startswith("_"):
                functions.append(FunctionSignature(name=func_name, params=[], description=description))

        return functions

    def _extract_classes(self) -> list[ClassDefinition]:
        """Extract class definitions from contract."""
        classes = []

        # Look for class definitions in code blocks
        code_block_pattern = re.compile(r"```(?:python)?\n(.+?)\n```", re.S)
        for code_match in code_block_pattern.finditer(self.text):
            code = code_match.group(1)

            # Find class definitions
            class_pattern = re.compile(r"class\s+(\w+)(?:\([^)]*\))?\s*:\n((?:\s{4,}.*\n?)*)")
            for class_match in class_pattern.finditer(code):
                class_name = class_match.group(1)
                class_body = class_match.group(2)

                # Extract methods from class body
                methods = []
                method_pattern = re.compile(r"(async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?\s*:")
                for method_match in method_pattern.finditer(class_body):
                    is_async = bool(method_match.group(1))
                    method_name = method_match.group(2)
                    params_str = method_match.group(3)
                    return_type = method_match.group(4)

                    # Skip private methods
                    if method_name.startswith("_") and method_name != "__init__":
                        continue

                    # Parse parameters
                    params = []
                    if params_str.strip():
                        for param in params_str.split(","):
                            param = param.strip()
                            if param == "self":
                                continue
                            if ":" in param:
                                param_name, param_type = param.split(":", 1)
                                params.append((param_name.strip(), param_type.strip()))
                            elif param:
                                params.append((param, "Any"))

                    methods.append(
                        FunctionSignature(
                            name=method_name,
                            params=params,
                            return_type=return_type.strip() if return_type else None,
                            is_async=is_async,
                        )
                    )

                classes.append(ClassDefinition(name=class_name, methods=methods, attributes=[]))

        return classes

    def _extract_data_models(self) -> list[DataModel]:
        """Extract data models/schemas from contract."""
        models = []

        # Look for JSON schema definitions
        schema_section = re.search(
            r"##\s*Data\s+(?:Contracts?|Models?|Schemas?)\s*\n(.+?)(?:\n##|\Z)", self.text, re.S | re.I
        )
        if schema_section:
            section_text = schema_section.group(1)

            # Extract model definitions
            model_pattern = re.compile(r"###\s*`?(\w+)`?\s*(?:\([^)]+\))?\s*\n(.+?)(?:\n###|\Z)", re.S)
            for match in model_pattern.finditer(section_text):
                model_name = match.group(1)
                model_body = match.group(2)

                fields = []

                # Extract fields from bullet lists
                field_pattern = re.compile(r"^\s*[-*]\s*`(\w+)`\s*\(([^)]+)(?:,\s*(\w+))?\)\s*:?\s*(.*)$", re.M)
                for field_match in field_pattern.finditer(model_body):
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    required_str = field_match.group(3)
                    description = field_match.group(4)

                    required = True
                    if required_str:
                        required = required_str.lower() == "required"

                    fields.append(
                        DataField(
                            name=field_name,
                            type_hint=field_type,
                            required=required,
                            description=description.strip() if description else "",
                        )
                    )

                if fields:
                    models.append(DataModel(name=model_name, fields=fields, json_schema=True))

        # Also look for dataclass/Pydantic model definitions
        code_block_pattern = re.compile(r"```(?:python)?\n(.+?)\n```", re.S)
        for code_match in code_block_pattern.finditer(self.text):
            code = code_match.group(1)

            # Find dataclass definitions
            dataclass_pattern = re.compile(r"@dataclass\s*\nclass\s+(\w+).*?:\n((?:\s{4,}.*\n?)*)")
            for dc_match in dataclass_pattern.finditer(code):
                model_name = dc_match.group(1)
                class_body = dc_match.group(2)

                fields = []
                # Extract typed attributes
                attr_pattern = re.compile(r"^\s{4,}(\w+)\s*:\s*([^\n=]+)(?:\s*=\s*(.+))?$", re.M)
                for attr_match in attr_pattern.finditer(class_body):
                    field_name = attr_match.group(1)
                    field_type = attr_match.group(2).strip()
                    default = attr_match.group(3)

                    fields.append(
                        DataField(
                            name=field_name,
                            type_hint=field_type,
                            required=default is None,
                            default=default.strip() if default else None,
                        )
                    )

                if fields:
                    # Check if we already have this model from JSON schema
                    existing = next((m for m in models if m.name == model_name), None)
                    if not existing:
                        models.append(DataModel(name=model_name, fields=fields))

        return models

    def _extract_errors(self) -> list[ErrorType]:
        """Extract error types from contract."""
        errors = []

        # Look for errors section
        errors_section = re.search(r"##\s*(?:Errors?|Exceptions?)\s*\n(.+?)(?:\n##|\Z)", self.text, re.S | re.I)
        if errors_section:
            section_text = errors_section.group(1)

            # Extract error names
            error_pattern = re.compile(r"`(\w*Error\w*)`(?:\s*[:-]\s*(.+?))?(?:\n|,|$)")
            for match in error_pattern.finditer(section_text):
                error_name = match.group(1)
                description = match.group(2) or ""
                errors.append(ErrorType(name=error_name, description=description.strip()))

        return errors

    def _extract_dependencies(self) -> list[Dependency]:
        """Extract dependencies from contract."""
        deps = []

        # Look for dependencies section
        deps_section = re.search(r"##\s*Dependencies?\s*\n(.+?)(?:\n##|\Z)", self.text, re.S | re.I)
        if deps_section:
            section_text = deps_section.group(1)

            # Extract dependency mentions
            dep_pattern = re.compile(
                r"[-*]\s*([^\s:]+)(?:\s*(?:@|version)?\s*([^\s,;]+))?(?:\s*(?:for|-)?\s*(.+?))?$", re.M
            )
            for match in dep_pattern.finditer(section_text):
                dep_name = match.group(1)
                version = match.group(2)
                usage = match.group(3)

                # Clean up dependency name
                dep_name = dep_name.strip("`'\"")
                if dep_name and not dep_name.startswith("#"):
                    deps.append(
                        Dependency(
                            name=dep_name,
                            version=version.strip() if version else None,
                            usage=usage.strip() if usage else "",
                        )
                    )

        return deps

    def _extract_inputs(self) -> list[DataField]:
        """Extract input parameters from contract."""
        inputs = []

        # Look for inputs section
        inputs_section = re.search(r"##\s*Inputs?\s*\n(.+?)(?:\n##|\Z)", self.text, re.S | re.I)
        if inputs_section:
            section_text = inputs_section.group(1)

            # Extract input parameters
            input_pattern = re.compile(r"[-*]\s*`(\w+)`\s*\(([^)]+)(?:,\s*(\w+))?\)\s*:?\s*(.*)$", re.M)
            for match in input_pattern.finditer(section_text):
                param_name = match.group(1)
                param_type = match.group(2)
                required_str = match.group(3)
                description = match.group(4)

                required = True
                if required_str:
                    required = required_str.lower() == "required"

                # Extract default value from description
                default = None
                if "default" in description.lower():
                    default_match = re.search(r"default:?\s*([^,;.]+)", description, re.I)
                    if default_match:
                        default = default_match.group(1).strip()

                inputs.append(
                    DataField(
                        name=param_name,
                        type_hint=param_type,
                        required=required,
                        default=default,
                        description=description.strip() if description else "",
                    )
                )

        return inputs

    def _extract_outputs(self) -> list[DataField]:
        """Extract output specifications from contract."""
        outputs = []

        # Look for outputs section
        outputs_section = re.search(r"##\s*Outputs?\s*(?:\([^)]+\))?\s*\n(.+?)(?:\n##|\Z)", self.text, re.S | re.I)
        if outputs_section:
            section_text = outputs_section.group(1)

            # Extract output specifications
            output_pattern = re.compile(r"[-*]\s*(?:`([^`]+)`|(\w+))\s*(?:\(([^)]+)\))?\s*:?\s*(.*)$", re.M)
            for match in output_pattern.finditer(section_text):
                output_name = match.group(1) or match.group(2)
                output_type = match.group(3) or "Any"
                description = match.group(4)

                if output_name and not output_name.startswith("One file"):
                    outputs.append(
                        DataField(
                            name=output_name.replace(" ", "_").lower(),
                            type_hint=output_type,
                            required=True,
                            description=description.strip() if description else "",
                        )
                    )

        return outputs

    def _extract_config_params(self) -> list[DataField]:
        """Extract configuration parameters from implementation spec mentions."""
        config_params = []

        # Look for config mentions in the text
        config_pattern = re.compile(r"config\s*=\s*\w+Config\s*\(([^)]+)\)", re.S)
        for match in config_pattern.finditer(self.text):
            config_content = match.group(1)

            # Extract parameters
            param_pattern = re.compile(r"(\w+)\s*=\s*([^,]+)")
            for param_match in param_pattern.finditer(config_content):
                param_name = param_match.group(1)
                param_value = param_match.group(2).strip()

                # Infer type from value
                if param_value.isdigit():
                    param_type = "int"
                elif param_value in ["True", "False"]:
                    param_type = "bool"
                elif param_value.startswith('"') or param_value.startswith("'"):
                    param_type = "str"
                else:
                    param_type = "Any"

                config_params.append(
                    DataField(
                        name=param_name,
                        type_hint=param_type,
                        required=False,
                        default=param_value,
                    )
                )

        # Also look for mentions of partition_size, batch_size, etc
        special_params = ["partition_size", "batch_size", "chunk_size", "max_items", "min_items"]
        for param in special_params:
            if param in self.text.lower() and not any(p.name == param for p in config_params):
                # Try to find context
                pattern = re.compile(rf"{param}[^\w]*(?:=|:)?\s*(\d+)", re.I)
                match = pattern.search(self.text)
                if match:
                    config_params.append(
                        DataField(
                            name=param,
                            type_hint="int",
                            required=False,
                            default=match.group(1),
                        )
                    )

        return config_params

    def _extract_invariants(self) -> list[str]:
        """Extract invariants/acceptance criteria."""
        invariants = []

        # Look for invariants section
        inv_section = re.search(
            r"##\s*(?:Invariants?|Acceptance\s+Criteria)\s*\n(.+?)(?:\n##|\Z)", self.text, re.S | re.I
        )
        if inv_section:
            section_text = inv_section.group(1)

            # Extract bullet points
            bullet_pattern = re.compile(r"^\s*[-*]\s*(.+)$", re.M)
            for match in bullet_pattern.finditer(section_text):
                invariant = match.group(1).strip()
                if invariant:
                    invariants.append(invariant)

        return invariants

    def _extract_side_effects(self) -> list[str]:
        """Extract side effects mentioned in contract."""
        effects = []

        # Look for side effects mentions
        for keyword in ["side effect", "writes to", "creates", "modifies", "updates", "deletes"]:
            pattern = re.compile(rf"{keyword}[^.]*\.?", re.I)
            for match in pattern.finditer(self.text):
                effect = match.group(0).strip()
                if effect and effect not in effects:
                    effects.append(effect)

        return effects
