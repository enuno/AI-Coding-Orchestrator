"""Tests for CLI module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from orchestrator.cli import cli


def test_cli_version() -> None:
    """Test CLI version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help() -> None:
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "AI Coding Orchestrator" in result.output


def test_init_command() -> None:
    """Test init command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert "initialized successfully" in result.output


def test_parse_command_success() -> None:
    """Test parse command with valid plan file."""
    runner = CliRunner()

    # Create a temporary plan file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Plan

## Executive Summary
Test plan for CLI testing.

## Phase 1: Setup

### Stage 1.1: Initialize project (Week 1)

**Objective**: Set up the basic project structure.

**Key Activities:**
- Create project directories
- Initialize git repository

**Deliverables:**
- Project structure

**Validation Criteria:**
- All directories created
""")
        plan_file = f.name

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_f:
            output_file = output_f.name

        try:
            result = runner.invoke(cli, ["parse", plan_file, "--output", output_file])
            assert result.exit_code == 0
            assert "Successfully parsed plan" in result.output
            assert "Tasks:  1" in result.output

            # Check output file was created and contains expected data
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["title"] == "Initialize project"
        finally:
            Path(output_file).unlink(missing_ok=True)
    finally:
        Path(plan_file).unlink(missing_ok=True)


def test_parse_command_no_output() -> None:
    """Test parse command without output file."""
    runner = CliRunner()

    # Create a temporary plan file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Plan

## Executive Summary
Test plan for CLI testing.

## Phase 1: Setup

### Stage 1.1: Initialize project (Week 1)

**Objective**: Set up the basic project structure.

**Key Activities:**
- Create project directories
- Initialize git repository

**Deliverables:**
- Project structure

**Validation Criteria:**
- All directories created
""")
        plan_file = f.name

    try:
        result = runner.invoke(cli, ["parse", plan_file])
        assert result.exit_code == 0
        assert "Successfully parsed plan" in result.output
        assert "Tasks:  1" in result.output
    finally:
        Path(plan_file).unlink(missing_ok=True)


def test_parse_command_file_not_found() -> None:
    """Test parse command with non-existent file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["parse", "nonexistent.md"])
    assert result.exit_code != 0


def test_assign_command_success() -> None:
    """Test assign command with valid plan file."""
    runner = CliRunner()

    # Create a temporary plan file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Plan

## Executive Summary
Test plan for CLI testing.

## Phase 1: Setup

### Stage 1.1: Initialize project (Week 1)

**Objective**: Set up the basic project structure.

**Key Activities:**
- Create project directories
- Initialize git repository

**Deliverables:**
- Project structure

**Validation Criteria:**
- All directories created

### Stage 1.2: Configure environment (Week 2)

**Objective**: Set up development environment.

**Key Activities:**
- Install dependencies
- Configure Docker

**Deliverables:**
- Development environment

**Validation Criteria:**
- Docker containers running
""")
        plan_file = f.name

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_f:
            output_file = output_f.name

        try:
            result = runner.invoke(cli, ["assign", plan_file, "--output", output_file])
            assert result.exit_code == 0
            assert "Classifying tasks..." in result.output
            assert "Assigning agents..." in result.output
            assert "Assigned 2 tasks to agents" in result.output

            # Check output file was created and contains expected data
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
                for task in data:
                    assert "task_id" in task
                    assert "title" in task
                    assert "task_type" in task
                    assert "complexity" in task
                    assert "assigned_agent" in task
                    assert "tech_stack" in task
        finally:
            Path(output_file).unlink(missing_ok=True)
    finally:
        Path(plan_file).unlink(missing_ok=True)


def test_assign_command_no_output() -> None:
    """Test assign command without output file."""
    runner = CliRunner()

    # Create a temporary plan file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Plan

## Executive Summary
Test plan for CLI testing.

## Phase 1: Setup

### Stage 1.1: Initialize project (Week 1)

**Objective**: Set up the basic project structure.

**Key Activities:**
- Create project directories
- Initialize git repository

**Deliverables:**
- Project structure

**Validation Criteria:**
- All directories created
""")
        plan_file = f.name

    try:
        result = runner.invoke(cli, ["assign", plan_file])
        assert result.exit_code == 0
        assert "Classifying tasks..." in result.output
        assert "Assigning agents..." in result.output
        assert "Assigned 1 tasks to agents" in result.output
    finally:
        Path(plan_file).unlink(missing_ok=True)


def test_assign_command_file_not_found() -> None:
    """Test assign command with non-existent file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["assign", "nonexistent.md"])
    assert result.exit_code != 0


def test_generate_command_success() -> None:
    """Test generate command with required parameters."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(cli, [
            "generate",
            "--name", "Test Project",
            "--description", "A test project",
            "--tech-stack", "python",
            "--tech-stack", "react",
            "--output-dir", temp_dir
        ])

        assert result.exit_code == 0
        assert "Generating configurations for Test Project..." in result.output
        assert "Generated 7 configuration files:" in result.output

        # Check that files were created
        output_path = Path(temp_dir)
        generated_files = list(output_path.glob("*"))
        assert len(generated_files) > 0


def test_generate_command_missing_required() -> None:
    """Test generate command with missing required parameters."""
    runner = CliRunner()

    # Missing name
    result = runner.invoke(cli, [
        "generate",
        "--description", "A test project",
        "--tech-stack", "python"
    ])
    assert result.exit_code != 0

    # Missing description
    result = runner.invoke(cli, [
        "generate",
        "--name", "Test Project",
        "--tech-stack", "python"
    ])
    assert result.exit_code != 0


def test_orchestrate_command_success() -> None:
    """Test orchestrate command with valid plan file."""
    runner = CliRunner()

    # Create a temporary plan file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Orchestration Plan

## Executive Summary
Test plan for full orchestration.

## Phase 1: Setup

### Stage 1.1: Initialize project (Week 1)

**Objective**: Set up the basic project structure.

**Key Activities:**
- Create project directories
- Initialize git repository

**Deliverables:**
- Project structure

**Validation Criteria:**
- All directories created

### Stage 1.2: Configure environment (Week 2)

**Objective**: Set up development environment.

**Key Activities:**
- Install dependencies
- Configure Docker

**Deliverables:**
- Development environment

**Validation Criteria:**
- Docker containers running
""")
        plan_file = f.name

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(cli, [
                "orchestrate",
                plan_file,
                "--output-dir", temp_dir,
                "--name", "Test Orchestration",
                "--description", "Full orchestration test"
            ])

            assert result.exit_code == 0
            assert "Starting full orchestration workflow..." in result.output
            assert "1. Parsing plan..." in result.output
            assert "2. Classifying tasks..." in result.output
            assert "3. Assigning agents..." in result.output
            assert "4. Generating configurations..." in result.output
            assert "✓ Orchestration complete!" in result.output

            # Check that files were created
            output_path = Path(temp_dir)
            generated_files = list(output_path.glob("*"))
            assert len(generated_files) > 0
    finally:
        Path(plan_file).unlink(missing_ok=True)


def test_orchestrate_command_no_name_description() -> None:
    """Test orchestrate command without name and description."""
    runner = CliRunner()

    # Create a temporary plan file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Plan

## Executive Summary
Test plan for orchestration without name/description.

## Phase 1: Setup

### Stage 1.1: Initialize project (Week 1)

**Objective**: Set up the basic project structure.

**Key Activities:**
- Create project directories
- Initialize git repository

**Deliverables:**
- Project structure

**Validation Criteria:**
- All directories created
""")
        plan_file = f.name

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(cli, [
                "orchestrate",
                plan_file,
                "--output-dir", temp_dir
            ])

            assert result.exit_code == 0
            assert "Starting full orchestration workflow..." in result.output
            assert "✓ Orchestration complete!" in result.output
    finally:
        Path(plan_file).unlink(missing_ok=True)


def test_orchestrate_command_file_not_found() -> None:
    """Test orchestrate command with non-existent file."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(cli, [
            "orchestrate",
            "nonexistent.md",
            "--output-dir", temp_dir
        ])
        assert result.exit_code != 0


def test_parse_command_with_complex_plan() -> None:
    """Test parse command with the complex fixture plan."""
    runner = CliRunner()

    fixture_path = Path(__file__).parent / "fixtures" / "simple_plan.md"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_f:
        output_file = output_f.name

    try:
        result = runner.invoke(cli, ["parse", str(fixture_path), "--output", output_file])
        assert result.exit_code == 0
        assert "Successfully parsed plan" in result.output
        assert "Tasks:" in result.output

        # Check output file was created and contains expected data
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 2  # simple_plan.md has 2 stages
            for task in data:
                assert "id" in task
                assert "title" in task
                assert "description" in task
                assert "phase" in task
                assert "stage" in task
    finally:
        Path(output_file).unlink(missing_ok=True)


def test_assign_command_with_complex_plan() -> None:
    """Test assign command with the complex fixture plan."""
    runner = CliRunner()

    fixture_path = Path(__file__).parent / "fixtures" / "simple_plan.md"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_f:
        output_file = output_f.name

    try:
        result = runner.invoke(cli, ["assign", str(fixture_path), "--output", output_file])
        assert result.exit_code == 0
        assert "Classifying tasks..." in result.output
        assert "Assigning agents..." in result.output

        # Check output file was created and contains expected data
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 2  # simple_plan.md has 2 stages
            for task in data:
                assert "task_id" in task
                assert "title" in task
                assert "task_type" in task
                assert "complexity" in task
                assert "assigned_agent" in task
                assert "tech_stack" in task
    finally:
        Path(output_file).unlink(missing_ok=True)


def test_orchestrate_command_with_complex_plan() -> None:
    """Test orchestrate command with the complex fixture plan."""
    runner = CliRunner()

    fixture_path = Path(__file__).parent / "fixtures" / "simple_plan.md"

    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(cli, [
            "orchestrate",
            str(fixture_path),
            "--output-dir", temp_dir,
            "--name", "Complex Test Project",
            "--description", "Testing with complex plan"
        ])

        assert result.exit_code == 0
        assert "Starting full orchestration workflow..." in result.output
        assert "✓ Orchestration complete!" in result.output

        # Check that files were created
        output_path = Path(temp_dir)
        generated_files = list(output_path.glob("*"))
        assert len(generated_files) > 0
