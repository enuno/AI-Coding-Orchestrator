"""Configuration file generator using Jinja2 templates."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclass
class ProjectContext:
    """Context information for generating agent configurations."""

    name: str
    description: str
    tech_stack: List[str] = field(default_factory=list)
    primary_language: str = "python"
    testing_frameworks: List[str] = field(default_factory=list)
    build_commands: Dict[str, str] = field(default_factory=dict)
    repository_url: Optional[str] = None
    coding_standards: List[str] = field(default_factory=list)


class ConfigurationGenerator:
    """Generates agent-specific configuration files from templates."""

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        """Initialize the configuration generator.

        Args:
            templates_dir: Optional path to templates directory
        """
        if templates_dir is None:
            # Default to templates directory in package
            templates_dir = Path(__file__).parent.parent / "templates"

        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_claude_md(self, context: ProjectContext) -> str:
        """Generate CLAUDE.md configuration.

        Args:
            context: Project context

        Returns:
            Generated CLAUDE.md content
        """
        template = self.env.get_template("claude.md.j2")
        return template.render(project=context)

    def generate_cursor_rules(self, context: ProjectContext) -> str:
        """Generate .cursorrules configuration.

        Args:
            context: Project context

        Returns:
            Generated .cursorrules content
        """
        template = self.env.get_template("cursorrules.j2")
        return template.render(project=context)

    def generate_copilot_instructions(self, context: ProjectContext) -> str:
        """Generate copilot-instructions.md configuration.

        Args:
            context: Project context

        Returns:
            Generated copilot-instructions.md content
        """
        template = self.env.get_template("copilot-instructions.md.j2")
        return template.render(project=context)

    def generate_gemini_settings(self, context: ProjectContext) -> str:
        """Generate gemini-settings.json configuration.

        Args:
            context: Project context

        Returns:
            Generated gemini-settings.json content
        """
        template = self.env.get_template("gemini-settings.json.j2")
        return template.render(project=context)

    def generate_cline_rules(self, context: ProjectContext) -> str:
        """Generate clinerules configuration.

        Args:
            context: Project context

        Returns:
            Generated clinerules content
        """
        template = self.env.get_template("clinerules.j2")
        return template.render(project=context)

    def generate_windsurf_rules(self, context: ProjectContext) -> str:
        """Generate windsurfrules configuration.

        Args:
            context: Project context

        Returns:
            Generated windsurfrules content
        """
        template = self.env.get_template("windsurfrules.j2")
        return template.render(project=context)

    def generate_agents_md(self, context: ProjectContext, assignments: Optional[Dict] = None) -> str:
        """Generate AGENTS.md universal documentation.

        Args:
            context: Project context
            assignments: Optional dictionary of agent assignments

        Returns:
            Generated AGENTS.md content
        """
        template = self.env.get_template("agents.md.j2")
        return template.render(project=context, assignments=assignments or {})

    def generate_all(
        self, context: ProjectContext, output_dir: Path, assignments: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Generate all configuration files.

        Args:
            context: Project context
            output_dir: Directory to write configuration files
            assignments: Optional dictionary of agent assignments

        Returns:
            Dictionary mapping filenames to their paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files: Dict[str, str] = {}

        # Generate each configuration file
        configs = {
            "AGENTS.md": self.generate_agents_md(context, assignments),
            "CLAUDE.md": self.generate_claude_md(context),
            ".cursorrules": self.generate_cursor_rules(context),
            "copilot-instructions.md": self.generate_copilot_instructions(context),
            "gemini-settings.json": self.generate_gemini_settings(context),
            ".clinerules": self.generate_cline_rules(context),
            ".windsurfrules": self.generate_windsurf_rules(context),
        }

        for filename, content in configs.items():
            filepath = output_dir / filename
            filepath.write_text(content, encoding="utf-8")
            generated_files[filename] = str(filepath)

        return generated_files
