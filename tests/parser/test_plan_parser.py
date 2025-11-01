"""Tests for plan_parser module."""

from pathlib import Path

import pytest

from orchestrator.parser.plan_parser import PlanParser


@pytest.fixture
def simple_plan_path():
    """Path to the simple test plan."""
    return Path(__file__).parent.parent / "fixtures" / "simple_plan.md"


@pytest.fixture
def parser():
    """Create a PlanParser instance."""
    return PlanParser()


def test_parser_initialization(parser):
    """Test parser initializes correctly."""
    assert parser is not None
    assert parser.md is not None


def test_parse_nonexistent_file(parser):
    """Test parsing non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        parser.parse_file("nonexistent.md")


def test_parse_simple_plan(parser, simple_plan_path):
    """Test parsing a simple valid plan."""
    plan = parser.parse_file(simple_plan_path)

    assert plan is not None
    assert plan.title == "Test Development Plan"
    assert plan.executive_summary is not None
    assert "test plan" in plan.executive_summary.lower()


def test_extract_core_principles(parser, simple_plan_path):
    """Test extraction of core principles."""
    plan = parser.parse_file(simple_plan_path)

    assert len(plan.core_principles) >= 2
    assert any("Test-Driven Development" in p for p in plan.core_principles)
    assert any("Iterative Approach" in p for p in plan.core_principles)


def test_extract_phases(parser, simple_plan_path):
    """Test extraction of phases."""
    plan = parser.parse_file(simple_plan_path)

    assert len(plan.phases) == 2
    assert plan.phases[0].phase_number == 1
    assert plan.phases[0].phase_name == "Foundation"
    assert plan.phases[1].phase_number == 2
    assert plan.phases[1].phase_name == "Implementation"


def test_extract_stages(parser, simple_plan_path):
    """Test extraction of stages from phases."""
    plan = parser.parse_file(simple_plan_path)

    # Phase 1 should have 1 stage
    assert len(plan.phases[0].stages) == 1
    stage = plan.phases[0].stages[0]
    assert stage.stage_number == "1.1"
    assert stage.stage_name == "Setup"
    assert stage.week_range == "Week 1-2"

    # Phase 2 should have 1 stage
    assert len(plan.phases[1].stages) == 1
    stage2 = plan.phases[1].stages[0]
    assert stage2.stage_number == "2.1"
    assert stage2.stage_name == "Core Features"


def test_extract_objective(parser, simple_plan_path):
    """Test extraction of stage objectives."""
    plan = parser.parse_file(simple_plan_path)

    stage = plan.phases[0].stages[0]
    assert stage.objective == "Set up the project infrastructure."


def test_extract_key_activities(parser, simple_plan_path):
    """Test extraction of key activities."""
    plan = parser.parse_file(simple_plan_path)

    stage = plan.phases[0].stages[0]
    assert len(stage.key_activities) == 3
    assert "Create project structure" in stage.key_activities
    assert "Set up testing framework" in stage.key_activities
    assert "Configure CI/CD" in stage.key_activities


def test_extract_deliverables(parser, simple_plan_path):
    """Test extraction of deliverables."""
    plan = parser.parse_file(simple_plan_path)

    stage = plan.phases[0].stages[0]
    assert len(stage.deliverables) == 3
    assert "Project repository" in stage.deliverables
    assert "Test framework" in stage.deliverables
    assert "CI pipeline" in stage.deliverables


def test_extract_validation_criteria(parser, simple_plan_path):
    """Test extraction of validation criteria."""
    plan = parser.parse_file(simple_plan_path)

    stage = plan.phases[0].stages[0]
    assert len(stage.validation_criteria) == 2
    assert "Tests pass" in stage.validation_criteria
    assert "CI runs successfully" in stage.validation_criteria


def test_extract_technical_implementation(parser, simple_plan_path):
    """Test extraction of technical implementation."""
    plan = parser.parse_file(simple_plan_path)

    stage = plan.phases[0].stages[0]
    assert stage.technical_implementation is not None
    assert "def setup_project():" in stage.technical_implementation


def test_extract_quality_metrics(parser, simple_plan_path):
    """Test extraction of quality metrics."""
    plan = parser.parse_file(simple_plan_path)

    assert "test_coverage_minimum" in plan.quality_metrics
    assert plan.quality_metrics["test_coverage_minimum"] == 85


def test_extract_risks(parser, simple_plan_path):
    """Test extraction of risks."""
    plan = parser.parse_file(simple_plan_path)

    assert len(plan.risks) == 2
    assert plan.risks[0]["risk_name"] == "Complexity Overload"
    assert plan.risks[1]["risk_name"] == "Integration Failures"
    assert all(risk["priority"] == "high" for risk in plan.risks)


def test_get_all_tasks(parser, simple_plan_path):
    """Test getting all tasks from plan."""
    plan = parser.parse_file(simple_plan_path)

    tasks = plan.get_all_tasks()
    assert len(tasks) == 2  # 2 stages = 2 tasks
    assert tasks[0].id == "phase1-stage1.1"
    assert tasks[1].id == "phase2-stage2.1"


def test_get_tasks_by_phase(parser, simple_plan_path):
    """Test getting tasks for specific phase."""
    plan = parser.parse_file(simple_plan_path)

    phase1_tasks = plan.get_tasks_by_phase(1)
    assert len(phase1_tasks) == 1
    assert phase1_tasks[0].phase == "Phase 1"

    phase2_tasks = plan.get_tasks_by_phase(2)
    assert len(phase2_tasks) == 1
    assert phase2_tasks[0].phase == "Phase 2"


def test_task_to_dict(parser, simple_plan_path):
    """Test converting task to dictionary."""
    plan = parser.parse_file(simple_plan_path)
    tasks = plan.get_all_tasks()

    task_dict = tasks[0].to_dict()
    assert isinstance(task_dict, dict)
    assert task_dict["id"] == "phase1-stage1.1"
    assert task_dict["title"] == "Setup"
    assert task_dict["phase"] == "Phase 1"
    assert "task_type" in task_dict
    assert "complexity" in task_dict


def test_parse_content_string(parser):
    """Test parsing plan from string content."""
    content = """# Test Plan

## Phase 1: Testing

### Stage 1.1: Unit Tests

**Objective**: Write unit tests.

**Deliverables:**
- Test files
"""
    plan = parser.parse_content(content)
    assert plan.title == "Test Plan"
    assert len(plan.phases) == 1
    assert plan.phases[0].phase_name == "Testing"
