"""
Configuration loader for website generator.
Handles loading and merging YAML configuration files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SiteConfig:
    """Complete site configuration"""

    site: dict[str, Any]
    content_strategy: dict[str, Any]
    design_system: dict[str, Any]
    pages: list
    interactions: dict[str, Any]
    navigation: dict[str, Any]
    seo: dict[str, Any]
    build: dict[str, Any]
    responsive: dict[str, Any]


class ConfigLoader:
    """Loads and manages website generator configuration"""

    def __init__(self, config_dir: str | None = None):
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

        if not self.config_dir.exists():
            raise ValueError(f"Configuration directory does not exist: {self.config_dir}")

    def load_base_config(self) -> dict[str, Any]:
        """Load base site template configuration"""
        site_template_path = self.config_dir / "site_template.yaml"
        content_patterns_path = self.config_dir / "content_patterns.yaml"

        if not site_template_path.exists():
            raise FileNotFoundError(f"Base site template not found: {site_template_path}")

        # Load site template
        with open(site_template_path, encoding="utf-8") as f:
            site_config = yaml.safe_load(f)

        # Load content patterns if available
        if content_patterns_path.exists():
            with open(content_patterns_path, encoding="utf-8") as f:
                content_patterns = yaml.safe_load(f)
                site_config["content_patterns"] = content_patterns

        return site_config

    def load_project_config(self, config_path: str) -> dict[str, Any]:
        """Load project-specific configuration"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Project configuration not found: {config_path}")

        with open(config_file, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def merge_configs(self, base_config: dict[str, Any], project_config: dict[str, Any]) -> dict[str, Any]:
        """Merge project configuration with base configuration"""

        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(base_config, project_config)

    def load_full_config(self, project_config_path: str | None = None) -> SiteConfig:
        """Load complete configuration, merging base and project configs"""
        # Load base configuration
        base_config = self.load_base_config()

        # Merge with project configuration if provided
        if project_config_path:
            project_config = self.load_project_config(project_config_path)
            final_config = self.merge_configs(base_config, project_config)
        else:
            final_config = base_config

        # Validate required sections
        required_sections = ["site", "content_strategy", "design_system", "pages"]
        for section in required_sections:
            if section not in final_config:
                raise ValueError(f"Required configuration section missing: {section}")

        # Create SiteConfig object
        return SiteConfig(
            site=final_config.get("site", {}),
            content_strategy=final_config.get("content_strategy", {}),
            design_system=final_config.get("design_system", {}),
            pages=final_config.get("pages", []),
            interactions=final_config.get("interactions", {}),
            navigation=final_config.get("navigation", {}),
            seo=final_config.get("seo", {}),
            build=final_config.get("build", {}),
            responsive=final_config.get("responsive", {}),
        )

    def validate_config(self, config: SiteConfig) -> bool:
        """Validate configuration for completeness and consistency"""
        # Check required site information
        if not config.site.get("name"):
            raise ValueError("Site name is required")

        if not config.site.get("description"):
            raise ValueError("Site description is required")

        # Check design system
        if not config.design_system.get("colors"):
            print("Warning: No color palette defined, using defaults")

        # Check pages
        if not config.pages:
            raise ValueError("At least one page must be defined")

        # Validate page structure
        for page in config.pages:
            if not page.get("name"):
                raise ValueError("Page name is required")
            if not page.get("sections"):
                raise ValueError(f"Page {page.get('name')} must have sections")

        return True

    def get_content_patterns(self, config: SiteConfig) -> dict[str, Any]:
        """Extract content generation patterns from configuration"""
        # This will be used by the content generation engine
        return {
            "paradigm_detection": config.content_strategy.get("paradigm_shift_detection", True),
            "progressive_disclosure": config.content_strategy.get("progressive_disclosure", True),
            "trust_building": config.content_strategy.get("trust_building_focus", True),
            "role_transformation": config.content_strategy.get("role_transformation_emphasis", True),
        }

    def export_config(self, config: SiteConfig, output_path: str) -> None:
        """Export merged configuration to file"""
        config_dict = {
            "site": config.site,
            "content_strategy": config.content_strategy,
            "design_system": config.design_system,
            "pages": config.pages,
            "interactions": config.interactions,
            "navigation": config.navigation,
            "seo": config.seo,
            "build": config.build,
            "responsive": config.responsive,
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False, indent=2)

        print(f"Configuration exported to: {output_file}")


def test_config_loader():
    """Test the configuration loader with Amplifier example"""
    loader = ConfigLoader()

    try:
        # Test base config loading
        print("Loading base configuration...")
        base_config = loader.load_base_config()
        print(f"✓ Base config loaded with {len(base_config)} sections")

        # Test project config loading
        project_config_path = Path(__file__).parent.parent / "examples" / "amplifier_config.yaml"
        print(f"Loading project configuration from {project_config_path}...")

        full_config = loader.load_full_config(str(project_config_path))
        print(f"✓ Full config loaded for project: {full_config.site['name']}")

        # Test validation
        print("Validating configuration...")
        if loader.validate_config(full_config):
            print("✓ Configuration validation passed")

        # Test content patterns extraction
        content_patterns = loader.get_content_patterns(full_config)
        print(f"✓ Content patterns extracted: {list(content_patterns.keys())}")

        # Test export
        export_path = "/tmp/test_config_export.yaml"
        loader.export_config(full_config, export_path)

        print("\n📊 Configuration Summary:")
        print(f"  Site: {full_config.site['name']}")
        print(f"  Theme: {full_config.site['theme']}")
        print(f"  Pages: {len(full_config.pages)}")
        print(f"  Color Palette: {full_config.design_system['color_palette']}")
        print(f"  Animation Level: {full_config.design_system['animation_level']}")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


if __name__ == "__main__":
    test_config_loader()
