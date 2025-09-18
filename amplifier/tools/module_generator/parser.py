"""Markdown specification parser

Parses markdown module specifications into structured ModuleSpec objects.
"""

import re
from pathlib import Path

from .models import ContractSpec
from .models import FileSpec
from .models import ImplementationSpec
from .models import ModuleSpec
from .models import TestSpec


class SpecificationParser:
    """Parse markdown specifications into ModuleSpec objects"""

    def __init__(self):
        """Initialize the parser"""
        self.spec = ModuleSpec(name="", path="", purpose="")

    def parse_file(self, spec_path: str | Path) -> ModuleSpec:
        """Parse a markdown specification file

        Args:
            spec_path: Path to the markdown file

        Returns:
            Parsed ModuleSpec object

        Raises:
            ValueError: If file cannot be parsed
        """
        spec_path = Path(spec_path)
        if not spec_path.exists():
            raise ValueError(f"Specification file not found: {spec_path}")

        with open(spec_path, encoding="utf-8") as f:
            content = f.read()

        return self.parse(content)

    def parse(self, content: str) -> ModuleSpec:
        """Parse markdown content into a ModuleSpec

        Args:
            content: Markdown specification content

        Returns:
            Parsed ModuleSpec object
        """
        lines = content.split("\n")
        current_section = ""
        current_file: FileSpec | None = None
        current_test: TestSpec | None = None

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Parse headers
            if line.startswith("# "):
                # Main module name
                self.spec.name = self._extract_module_name(line[2:].strip())
                continue

            if line.startswith("## "):
                current_section = line[3:].strip().lower()
                current_file = None
                current_test = None
                continue

            if line.startswith("### "):
                subsection = line[4:].strip()

                # Check if this is a file specification
                if current_section == "files" and subsection.endswith(".py"):
                    current_file = FileSpec(filename=subsection, purpose="")
                    self.spec.files.append(current_file)

                # Check if this is a test specification
                elif current_section == "tests" and subsection.endswith(".py"):
                    current_test = TestSpec(filename=subsection, description="")
                    self.spec.tests.append(current_test)
                continue

            # Parse content based on current section
            self._parse_line(line, current_section, current_file, current_test)

        # Extract module path from name if not explicitly set
        if not self.spec.path and self.spec.name:
            self.spec.path = f"amplifier/modules/{self.spec.name}"

        return self.spec

    def _extract_module_name(self, title: str) -> str:
        """Extract module name from title

        Args:
            title: Title line from markdown

        Returns:
            Module name
        """
        # Remove "Module:" prefix if present
        if title.lower().startswith("module:"):
            title = title[7:].strip()

        # Convert to snake_case
        name = re.sub(r"[^\w\s-]", "", title)
        name = re.sub(r"[-\s]+", "_", name)
        return name.lower()

    def _parse_line(
        self, line: str, section: str, current_file: FileSpec | None, current_test: TestSpec | None
    ) -> None:
        """Parse a single line based on context

        Args:
            line: Line to parse
            section: Current section being parsed
            current_file: Current file spec being built
            current_test: Current test spec being built
        """
        line = line.strip()

        # Skip markdown formatting
        if line.startswith("```"):
            return

        # Parse based on section
        if section == "purpose":
            if self.spec.purpose:
                self.spec.purpose += " " + line
            else:
                self.spec.purpose = line

        elif section == "path":
            if line:
                self.spec.path = line

        elif section == "files" and current_file:
            self._parse_file_line(line, current_file)

        elif section == "tests" and current_test:
            self._parse_test_line(line, current_test)

        elif section == "inputs":
            self._parse_contract_line(line, self.spec.inputs)

        elif section == "outputs":
            self._parse_contract_line(line, self.spec.outputs)

        elif section == "side effects":
            if line.startswith("- "):
                self.spec.side_effects.append(line[2:])

        elif section == "dependencies":
            if line.startswith("- "):
                dep = line[2:].strip()
                if "/" in dep or dep.startswith("amplifier"):
                    self.spec.internal_deps.append(dep)
                else:
                    self.spec.external_deps.append(dep)

        elif section == "configuration":
            self._parse_config_line(line)

        elif section == "examples":
            if line:
                self.spec.examples.append(line)

        elif section == "performance":
            if self.spec.performance:
                self.spec.performance += " " + line
            else:
                self.spec.performance = line

        elif section == "error handling":
            if self.spec.error_handling:
                self.spec.error_handling += " " + line
            else:
                self.spec.error_handling = line

    def _parse_file_line(self, line: str, file_spec: FileSpec) -> None:
        """Parse a line within a file specification

        Args:
            line: Line to parse
            file_spec: FileSpec to update
        """
        if line.startswith("Purpose:"):
            file_spec.purpose = line[8:].strip()
        elif line.startswith("- "):
            # List item - could be interface or dependency
            item = line[2:].strip()
            if item.endswith(".py"):
                file_spec.dependencies.append(item)
            else:
                file_spec.public_interface.append(item)
        elif line and not file_spec.purpose:
            file_spec.purpose = line

    def _parse_test_line(self, line: str, test_spec: TestSpec) -> None:
        """Parse a line within a test specification

        Args:
            line: Line to parse
            test_spec: TestSpec to update
        """
        if line.startswith("Description:"):
            test_spec.description = line[12:].strip()
        elif line.startswith("- "):
            test_spec.test_cases.append(line[2:].strip())
        elif line and not test_spec.description:
            test_spec.description = line

    def _parse_contract_line(self, line: str, contract: dict[str, str]) -> None:
        """Parse a contract line (input/output)

        Args:
            line: Line to parse
            contract: Contract dict to update
        """
        if ":" in line and line.startswith("- "):
            line = line[2:]  # Remove bullet
            key, value = line.split(":", 1)
            contract[key.strip()] = value.strip()

    def _parse_config_line(self, line: str) -> None:
        """Parse a configuration line

        Args:
            line: Line to parse
        """
        if ":" in line:
            if line.startswith("- "):
                line = line[2:]
            key, value = line.split(":", 1)
            # Try to parse value as appropriate type
            value = value.strip()
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            self.spec.config[key.strip()] = value


async def parse_contract(file_path: Path) -> "ContractSpec":
    """Parse contract markdown file into ContractSpec

    Args:
        file_path: Path to contract markdown file

    Returns:
        Parsed ContractSpec
    """
    from .models import ContractSpec

    if not file_path.exists():
        raise ValueError(f"Contract file not found: {file_path}")

    content = file_path.read_text()

    # Extract key sections from markdown
    def extract_section(text: str, section: str) -> str:
        """Extract content under a markdown section"""
        # Fix regex pattern - no space in {1,3}
        pattern = rf"##{{1,3}}\s*{re.escape(section)}.*?\n(.*?)(?=\n##{{1,3}}\s|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    # Parse module name from filename or content
    module_name = file_path.stem.lower().replace("_contract", "").replace("-", "_")
    if "Module Identity" in content:
        name_match = re.search(r"\*\*Name\*\*:\s*(\S+)", extract_section(content, "Module Identity"))
        if name_match:
            module_name = name_match.group(1)

    # Parse purpose
    purpose = extract_section(content, "Purpose")
    if not purpose:
        # Try to get the first paragraph after ## Purpose
        purpose_match = re.search(r"##\s*Purpose\s*\n+([^#\n]+(?:\n[^#\n]+)*)", content)
        if purpose_match:
            purpose = purpose_match.group(1).strip()

    # Parse public interface
    interface_section = extract_section(content, "Public Interface")
    public_interface = []
    for line in interface_section.split("\n"):
        if "def " in line or "class " in line or "async def " in line:
            # Extract function/class name
            match = re.search(r"(def|class|async def)\s+(\w+)", line)
            if match:
                public_interface.append(match.group(2))

    # Parse inputs and outputs from Public Interface section
    inputs = {}
    outputs = {}
    # Look for Args: and Returns: in docstrings
    if interface_section:
        args_matches = re.findall(r"Args:\s*\n(.*?)(?=Returns:|\"\"\"|\'\'\'|$)", interface_section, re.DOTALL)
        for args_match in args_matches:
            for line in args_match.split("\n"):
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        param_name = parts[0].strip()
                        param_desc = parts[1].strip()
                        inputs[param_name] = param_desc

        returns_matches = re.findall(r"Returns:\s*\n(.*?)(?=\"\"\"|\'\'\'|Args:|$)", interface_section, re.DOTALL)
        for returns_match in returns_matches:
            # First non-empty line is typically the return description
            for line in returns_match.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    outputs["return_value"] = line
                    break

    # Parse dependencies
    deps_section = extract_section(content, "Dependencies")
    dependencies = []
    external_deps = []
    internal_deps = []
    if deps_section:
        # Look for External and Internal subsections
        external_match = re.search(r"###\s*External.*?\n(.*?)(?=###|$)", deps_section, re.DOTALL)
        internal_match = re.search(r"###\s*Internal.*?\n(.*?)(?=###|$)", deps_section, re.DOTALL)

        if external_match:
            for line in external_match.group(1).split("\n"):
                if line.strip().startswith("-"):
                    dep = line.strip().lstrip("- ").split()[0].strip()
                    if dep:
                        external_deps.append(dep)

        if internal_match:
            for line in internal_match.group(1).split("\n"):
                if line.strip().startswith("-"):
                    dep = line.strip().lstrip("- ")
                    if dep:
                        internal_deps.append(dep)

        # If no subsections, treat all as general dependencies
        if not external_match and not internal_match:
            for line in deps_section.split("\n"):
                if line.strip().startswith("-"):
                    dep = line.strip().lstrip("- ").split()[0]
                    if dep:
                        dependencies.append(dep)

    # Use external_deps if found, otherwise fall back to general dependencies
    if external_deps:
        dependencies = external_deps

    # Parse invariants
    invariants_section = extract_section(content, "Invariants")
    invariants = []
    if invariants_section:
        for line in invariants_section.split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                # Extract numbered invariant
                match = re.match(r"\d+\.\s*\*\*(.*?)\*\*:\s*(.*)", line)
                if match:
                    invariants.append(f"{match.group(1)}: {match.group(2)}")
                elif ". " in line:
                    invariants.append(line.split(". ", 1)[1])

    # Parse side effects
    side_effects_section = extract_section(content, "Side Effects")
    side_effects = []
    if side_effects_section:
        for line in side_effects_section.split("\n"):
            if line.strip().startswith("-"):
                side_effects.append(line.strip().lstrip("- "))

    # Parse error handling
    error_section = extract_section(content, "Error Handling")
    error_handling = {}
    if error_section:
        # Look for Expected Errors subsection
        expected_match = re.search(r"###\s*Expected Errors.*?\n(.*?)(?=###|$)", error_section, re.DOTALL)
        if expected_match:
            for line in expected_match.group(1).split("\n"):
                if line.strip().startswith("-"):
                    error_line = line.strip().lstrip("- ")
                    if ":" in error_line:
                        error_name, error_desc = error_line.split(":", 1)
                        error_handling[error_name.strip()] = error_desc.strip()

    # Parse performance specs
    perf_section = extract_section(content, "Performance Specifications")
    performance_specs = {}
    if perf_section:
        # Look for Targets subsection
        targets_match = re.search(r"###\s*Targets.*?\n(.*?)(?=###|$)", perf_section, re.DOTALL)
        if targets_match:
            for line in targets_match.group(1).split("\n"):
                if line.strip().startswith("-"):
                    spec_line = line.strip().lstrip("- ")
                    # Try to extract metric and target
                    if "<" in spec_line or ">" in spec_line or "=" in spec_line:
                        performance_specs["targets"] = performance_specs.get("targets", []) + [spec_line]

    return ContractSpec(
        module_name=module_name,
        purpose=purpose,
        public_interface=public_interface,
        dependencies=dependencies,
        inputs=inputs,
        outputs=outputs,
        side_effects=side_effects,
        invariants=invariants,
        error_handling=error_handling,
        performance_specs=performance_specs,
    )


async def parse_implementation(file_path: Path) -> "ImplementationSpec":
    """Parse implementation markdown file into ImplementationSpec

    Args:
        file_path: Path to implementation markdown file

    Returns:
        Parsed ImplementationSpec
    """
    from .models import ImplementationSpec

    if not file_path.exists():
        raise ValueError(f"Implementation file not found: {file_path}")

    content = file_path.read_text()

    # Extract key sections from markdown
    def extract_section(text: str, section: str) -> str:
        """Extract content under a markdown section"""
        # Fix regex pattern - no space in {1,3}
        pattern = rf"##{{1,3}}\s*{re.escape(section)}.*?\n(.*?)(?=\n##{{1,3}}\s|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    # Parse module name from filename
    module_name = file_path.stem.lower().replace("_impl_spec", "").replace("-", "_")

    # Parse architecture/design overview
    architecture = extract_section(content, "Design Overview")
    if not architecture:
        architecture = extract_section(content, "Architecture")
    if not architecture:
        # Try to get the first paragraph after ## Design Overview
        arch_match = re.search(r"##\s*Design Overview\s*\n+([^#]+)", content)
        if arch_match:
            # Get everything up to the next section
            architecture = arch_match.group(1).strip()
            # Clean up by removing subsections if they leaked in
            if "###" in architecture:
                architecture = architecture.split("###")[0].strip()

    # Parse key algorithms
    algorithms_section = extract_section(content, "Key Algorithms")
    key_algorithms = []
    if algorithms_section:
        # Look for algorithm definitions (### headers or code blocks with algorithm descriptions)
        algo_headers = re.findall(r"###\s*(.*?)\s*\n", algorithms_section)
        key_algorithms.extend(algo_headers)

        # Also look for def statements in code blocks
        code_algos = re.findall(r"def\s+(\w+).*?\"\"\"(.*?)\"\"\"", algorithms_section, re.DOTALL)
        for algo_name, algo_desc in code_algos:
            if algo_name not in key_algorithms:
                key_algorithms.append(f"{algo_name}: {algo_desc.strip()[:100]}")

    # Parse data models
    data_models_section = extract_section(content, "Data Models")
    data_models = {}
    if data_models_section:
        # Look for class definitions
        class_matches = re.findall(r"class\s+(\w+).*?(?:\"\"\"(.*?)\"\"\")", data_models_section, re.DOTALL)
        for class_name, class_desc in class_matches:
            data_models[class_name] = class_desc.strip()

    # Parse processing flow
    flow_section = extract_section(content, "Processing Flow")
    processing_flow = []
    if flow_section:
        # Look for Phase headers
        phases = re.findall(r"###\s*Phase\s*\d+:\s*(.*?)\n(.*?)(?=###|$)", flow_section, re.DOTALL)
        for phase_name, phase_content in phases:
            processing_flow.append(f"{phase_name}: {phase_content.strip()[:200]}")

        # If no phases, look for numbered items
        if not processing_flow:
            for line in flow_section.split("\n"):
                if re.match(r"\d+\.", line.strip()):
                    processing_flow.append(line.strip())

    # Parse testing strategy
    testing_strategy = extract_section(content, "Testing Strategy")
    if not testing_strategy:
        # Try looking for Testing subsections
        test_match = re.search(r"##\s*Testing.*?\n(.*?)(?=##|$)", content, re.DOTALL)
        if test_match:
            testing_strategy = test_match.group(1).strip()

    # Parse error handling details
    error_details = extract_section(content, "Error Handling Details")
    if not error_details:
        error_details = extract_section(content, "Error Handling")

    # Parse performance optimizations
    perf_section = extract_section(content, "Performance Optimizations")
    if not perf_section:
        perf_section = extract_section(content, "Performance")

    performance_optimizations = []
    if perf_section:
        # Look for subsection headers
        opt_headers = re.findall(r"###\s*(.*?)\s*\n", perf_section)
        performance_optimizations.extend(opt_headers)

        # Also look for bullet points
        for line in perf_section.split("\n"):
            if line.strip().startswith("-") and line.strip().lstrip("- ") not in performance_optimizations:
                performance_optimizations.append(line.strip().lstrip("- "))

    # Parse security considerations
    security_section = extract_section(content, "Security Considerations")
    security_considerations = []
    if security_section:
        # Look for subsection headers
        sec_headers = re.findall(r"###\s*(.*?)\s*\n", security_section)
        security_considerations.extend(sec_headers)

        # Also look for bullet points
        for line in security_section.split("\n"):
            if line.strip().startswith("-"):
                consideration = line.strip().lstrip("- ")
                if consideration not in security_considerations:
                    security_considerations.append(consideration)

    return ImplementationSpec(
        module_name=module_name,
        architecture=architecture,
        key_algorithms=key_algorithms,
        testing_strategy=testing_strategy,
        data_models=data_models,
        processing_flow=processing_flow,
        error_handling_details=error_details,
        performance_optimizations=performance_optimizations,
        security_considerations=security_considerations,
    )
