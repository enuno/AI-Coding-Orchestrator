"""Tests for configuration generator."""

import json
import tempfile
from pathlib import Path

import pytest

from orchestrator.config.generator import ConfigurationGenerator, ProjectContext


@pytest.fixture
def project_context():
    """Create a sample project context."""
    return ProjectContext(
        name="Test Project",
        description="A test project for configuration generation",
        tech_stack=["python", "typescript", "docker"],
        primary_language="python",
        testing_frameworks=["pytest", "jest"],
        build_commands={
            "install": "poetry install",
            "test": "pytest",
            "build": "poetry build",
        },
        repository_url="https://github.com/test/project",
        coding_standards=[
            "Follow PEP 8",
            "Use type hints",
            "Write docstrings",
        ],
    )


@pytest.fixture
def generator():
    """Create a configuration generator instance."""
    return ConfigurationGenerator()


def test_generator_initialization(generator):
    """Test generator initializes correctly."""
    assert generator is not None
    assert generator.env is not None
    assert generator.templates_dir.exists()


def test_generate_claude_md(generator, project_context):
    """Test Claude.md generation."""
    content = generator.generate_claude_md(project_context)

    assert content is not None
    assert "Test Project" in content
    assert "Claude Code Instructions" in content
    assert "python" in content
    assert "typescript" in content
    assert "Follow PEP 8" in content
    assert "pytest" in content


def test_generate_cursor_rules(generator, project_context):
    """Test .cursorrules generation."""
    content = generator.generate_cursor_rules(project_context)

    assert content is not None
    assert "Test Project" in content
    assert "Cursor Rules" in content
    assert "python" in content
    assert "typescript" in content


def test_generate_copilot_instructions(generator, project_context):
    """Test copilot-instructions.md generation."""
    content = generator.generate_copilot_instructions(project_context)

    assert content is not None
    assert "Test Project" in content
    assert "GitHub Copilot Instructions" in content
    assert "python" in content


def test_generate_gemini_settings(generator, project_context):
    """Test gemini-settings.json generation."""
    content = generator.generate_gemini_settings(project_context)

    assert content is not None
    # Verify it's valid JSON
    data = json.loads(content)
    assert data["projectName"] == "Test Project"
    assert data["primaryLanguage"] == "python"
    assert "python" in data["techStack"]


def test_generate_cline_rules(generator, project_context):
    """Test .clinerules generation."""
    content = generator.generate_cline_rules(project_context)

    assert content is not None
    assert "Test Project" in content
    assert "Cline Configuration" in content
    assert "MCP Integration" in content


def test_generate_windsurf_rules(generator, project_context):
    """Test .windsurfrules generation."""
    content = generator.generate_windsurf_rules(project_context)

    assert content is not None
    assert "Test Project" in content
    assert "Windsurf Configuration" in content
    assert "Privacy & Security" in content


def test_generate_agents_md(generator, project_context):
    """Test AGENTS.md generation."""
    content = generator.generate_agents_md(project_context)

    assert content is not None
    assert "Test Project" in content
    assert "AI Agent Coordination" in content
    assert "python" in content
    assert "typescript" in content


def test_generate_agents_md_with_assignments(generator, project_context):
    """Test AGENTS.md generation with agent assignments."""
    assignments = {
        "backend_api": {
            "primary": "claude",
            "secondary": ["cursor"],
            "reasoning": "Claude for architecture, Cursor for implementation",
        },
        "frontend_component": {
            "primary": "cursor",
            "secondary": ["copilot"],
            "reasoning": "Cursor for multi-file editing",
        },
    }

    content = generator.generate_agents_md(project_context, assignments)

    assert content is not None
    assert "backend_api" in content.lower() or "Backend Api" in content
    assert "claude" in content
    assert "cursor" in content


def test_generate_all(generator, project_context):
    """Test generating all configuration files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generated_files = generator.generate_all(project_context, output_dir)

        # Verify all expected files were generated
        expected_files = [
            "AGENTS.md",
            "CLAUDE.md",
            ".cursorrules",
            "copilot-instructions.md",
            "gemini-settings.json",
            ".clinerules",
            ".windsurfrules",
        ]

        for filename in expected_files:
            assert filename in generated_files
            filepath = Path(generated_files[filename])
            assert filepath.exists()
            assert filepath.stat().st_size > 0


def test_generate_all_creates_output_dir(generator, project_context):
    """Test that generate_all creates output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "configs"
        assert not output_dir.exists()

        generated_files = generator.generate_all(project_context, output_dir)

        assert output_dir.exists()
        assert len(generated_files) > 0


def test_minimal_project_context():
    """Test configuration generation with minimal project context."""
    minimal_context = ProjectContext(
        name="Minimal Project",
        description="A minimal test project",
    )

    generator = ConfigurationGenerator()
    content = generator.generate_claude_md(minimal_context)

    assert content is not None
    assert "Minimal Project" in content
    assert "python" in content  # default primary language


def test_project_context_with_all_fields(project_context):
    """Test that all project context fields are used."""
    generator = ConfigurationGenerator()

    # Test CLAUDE.md uses all fields
    claude_md = generator.generate_claude_md(project_context)
    assert "Test Project" in claude_md
    assert "test project for configuration" in claude_md
    assert "python" in claude_md
    assert "pytest" in claude_md
    assert "poetry install" in claude_md
    assert "https://github.com/test/project" in claude_md
    assert "Follow PEP 8" in claude_md


def test_generate_all_with_assignments(generator, project_context):
    """Test generate_all includes assignments in AGENTS.md."""
    assignments = {
        "backend_api": {
            "primary": "claude",
            "secondary": [],
            "reasoning": "Best for backend work",
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generated_files = generator.generate_all(project_context, output_dir, assignments)

        agents_md_path = Path(generated_files["AGENTS.md"])
        agents_md_content = agents_md_path.read_text()

        assert "claude" in agents_md_content
        assert "Best for backend work" in agents_md_content


def test_gemini_settings_valid_json(generator, project_context):
    """Test that gemini-settings.json is always valid JSON."""
    content = generator.generate_gemini_settings(project_context)

    # Should not raise exception
    data = json.loads(content)

    # Verify structure
    assert isinstance(data, dict)
    assert "projectName" in data
    assert "techStack" in data
    assert isinstance(data["techStack"], list)


def test_empty_tech_stack():
    """Test configuration generation with empty tech stack."""
    context = ProjectContext(
        name="No Tech Stack Project",
        description="A project with no tech stack specified",
        tech_stack=[],
    )

    generator = ConfigurationGenerator()
    content = generator.generate_claude_md(context)

    # Should still generate valid content
    assert content is not None
    assert "No Tech Stack Project" in content


def test_empty_coding_standards():
    """Test configuration generation with no coding standards."""
    context = ProjectContext(
        name="No Standards Project",
        description="A project with no coding standards",
        coding_standards=[],
    )

    generator = ConfigurationGenerator()
    content = generator.generate_claude_md(context)

    # Should include default standards
    assert content is not None
    assert "best practices" in content.lower() or "self-documenting" in content


def test_file_encoding_utf8(generator, project_context):
    """Test that generated files use UTF-8 encoding."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generated_files = generator.generate_all(project_context, output_dir)

        # Read a file and verify it's valid UTF-8
        claude_md_path = Path(generated_files["CLAUDE.md"])
        content = claude_md_path.read_text(encoding="utf-8")

        assert content is not None
        assert len(content) > 0
