"""Module file writer

Handles writing generated code to the filesystem.
"""

from pathlib import Path


class ModuleWriter:
    """Write generated module files to disk"""

    def __init__(self, base_dir: str | Path):
        """Initialize the writer

        Args:
            base_dir: Base directory for output
        """
        self.base_dir = Path(base_dir)

    def write_file(self, module_path: str, filename: str, content: str) -> Path:
        """Write a module file

        Args:
            module_path: Module path (e.g., amplifier/tools/module_generator)
            filename: Filename to write
            content: File content

        Returns:
            Path to written file
        """
        # Create full path
        full_path = self.base_dir / module_path
        full_path.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path = full_path / filename
        file_path.write_text(content, encoding="utf-8")

        return file_path

    def write_test(self, module_path: str, filename: str, content: str) -> Path:
        """Write a test file

        Args:
            module_path: Module path
            filename: Test filename
            content: Test content

        Returns:
            Path to written file
        """
        # Create tests directory
        test_dir = self.base_dir / module_path / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)

        # Write test file
        file_path = test_dir / filename
        file_path.write_text(content, encoding="utf-8")

        return file_path

    def create_structure(self, module_path: str) -> None:
        """Create module directory structure

        Args:
            module_path: Module path to create
        """
        module_dir = self.base_dir / module_path
        module_dir.mkdir(parents=True, exist_ok=True)

        # Create standard subdirectories
        (module_dir / "tests").mkdir(exist_ok=True)
        (module_dir / "examples").mkdir(exist_ok=True)
        (module_dir / "docs").mkdir(exist_ok=True)

    def write_example(self, module_path: str, filename: str, content: str) -> Path:
        """Write an example file

        Args:
            module_path: Module path
            filename: Example filename
            content: Example content

        Returns:
            Path to written file
        """
        example_dir = self.base_dir / module_path / "examples"
        example_dir.mkdir(parents=True, exist_ok=True)

        file_path = example_dir / filename
        file_path.write_text(content, encoding="utf-8")

        return file_path

    def write_doc(self, module_path: str, filename: str, content: str) -> Path:
        """Write a documentation file

        Args:
            module_path: Module path
            filename: Doc filename
            content: Doc content

        Returns:
            Path to written file
        """
        doc_dir = self.base_dir / module_path / "docs"
        doc_dir.mkdir(parents=True, exist_ok=True)

        file_path = doc_dir / filename
        file_path.write_text(content, encoding="utf-8")

        return file_path

    def clean_module(self, module_path: str) -> None:
        """Clean existing module directory

        Args:
            module_path: Module path to clean
        """
        module_dir = self.base_dir / module_path
        if module_dir.exists():
            import shutil

            shutil.rmtree(module_dir)

    def module_exists(self, module_path: str) -> bool:
        """Check if module already exists

        Args:
            module_path: Module path to check

        Returns:
            True if module exists
        """
        module_dir = self.base_dir / module_path
        return module_dir.exists()

    def list_files(self, module_path: str) -> list[Path]:
        """List all files in a module

        Args:
            module_path: Module path

        Returns:
            List of file paths
        """
        module_dir = self.base_dir / module_path
        if not module_dir.exists():
            return []

        files = []
        for path in module_dir.rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                files.append(path)

        return files
