"""Tests for agent_assigner module."""

import pytest

from orchestrator.classifier.agent_assigner import AgentAssigner
from orchestrator.core.models import Task, TaskType, Complexity


@pytest.fixture
def assigner():
    """Create an AgentAssigner instance."""
    return AgentAssigner()


@pytest.fixture
def backend_api_task():
    """Create a backend API task."""
    return Task(
        id="backend-1",
        title="Create REST API",
        description="Build backend API endpoints",
        phase="Phase 1",
        stage="Stage 1.1",
        task_type=TaskType.BACKEND_API,
        complexity=Complexity.MEDIUM,
        tech_stack=["python"],
    )


@pytest.fixture
def frontend_task():
    """Create a frontend component task."""
    return Task(
        id="frontend-1",
        title="Build React component",
        description="Create UI component",
        phase="Phase 1",
        stage="Stage 1.2",
        task_type=TaskType.FRONTEND_COMPONENT,
        complexity=Complexity.MEDIUM,
        tech_stack=["react", "typescript"],
    )


@pytest.fixture
def devops_task():
    """Create a DevOps infrastructure task."""
    return Task(
        id="devops-1",
        title="Configure deployment",
        description="Set up CI/CD pipeline",
        phase="Phase 2",
        stage="Stage 2.1",
        task_type=TaskType.DEVOPS_INFRASTRUCTURE,
        complexity=Complexity.MEDIUM,
        tech_stack=["docker", "kubernetes"],
    )


@pytest.fixture
def legacy_refactoring_task():
    """Create a complex legacy refactoring task."""
    return Task(
        id="refactor-1",
        title="Refactor legacy codebase",
        description="Comprehensive legacy code refactoring with architectural changes",
        phase="Phase 3",
        stage="Stage 3.1",
        task_type=TaskType.LEGACY_REFACTORING,
        complexity=Complexity.COMPLEX,
        tech_stack=["python"],
        key_activities=[
            "Analyze multi-file legacy codebase",
            "Redesign architecture",
        ],
    )


@pytest.fixture
def simple_test_task():
    """Create a simple testing task."""
    return Task(
        id="test-1",
        title="Write unit tests",
        description="Add unit tests for utility functions",
        phase="Phase 1",
        stage="Stage 1.3",
        task_type=TaskType.TESTING,
        complexity=Complexity.SIMPLE,
        tech_stack=["python"],
    )


@pytest.fixture
def mcp_task():
    """Create an MCP development task."""
    return Task(
        id="mcp-1",
        title="Build MCP server",
        description="Develop MCP server integration",
        phase="Phase 4",
        stage="Stage 4.1",
        task_type=TaskType.MCP_DEVELOPMENT,
        complexity=Complexity.MEDIUM,
        tech_stack=["python"],
    )


@pytest.fixture
def documentation_task():
    """Create a documentation task."""
    return Task(
        id="doc-1",
        title="Write API documentation",
        description="Create comprehensive API documentation",
        phase="Phase 1",
        stage="Stage 1.4",
        task_type=TaskType.DOCUMENTATION,
        complexity=Complexity.MEDIUM,
        tech_stack=[],
    )


def test_assigner_initialization(assigner):
    """Test assigner initializes correctly."""
    assert assigner is not None
    assert assigner.agents is not None
    assert assigner.assignment_rules is not None
    assert len(assigner.agents) > 0


def test_validate_agent(assigner):
    """Test agent validation."""
    assert assigner._validate_agent("claude") is True
    assert assigner._validate_agent("copilot") is True
    assert assigner._validate_agent("cursor") is True
    assert assigner._validate_agent("invalid_agent") is False


def test_assign_backend_task(assigner, backend_api_task):
    """Test assignment of backend API task."""
    assigned = assigner.assign_agent(backend_api_task)

    assert assigned.assigned_agent is not None
    # Backend tasks should typically go to Claude (primary) or Cursor
    assert assigned.assigned_agent in ["claude", "cursor", "copilot"]


def test_assign_frontend_task(assigner, frontend_task):
    """Test assignment of frontend component task."""
    assigned = assigner.assign_agent(frontend_task)

    assert assigned.assigned_agent is not None
    # Frontend tasks should typically go to Cursor (primary) or Copilot
    assert assigned.assigned_agent in ["cursor", "copilot", "claude"]


def test_assign_devops_task(assigner, devops_task):
    """Test assignment of DevOps task."""
    assigned = assigner.assign_agent(devops_task)

    assert assigned.assigned_agent is not None
    # DevOps tasks should typically go to Gemini (primary) or Claude
    assert assigned.assigned_agent in ["gemini", "claude", "cline"]


def test_assign_legacy_refactoring(assigner, legacy_refactoring_task):
    """Test assignment of complex legacy refactoring task."""
    assigned = assigner.assign_agent(legacy_refactoring_task)

    assert assigned.assigned_agent is not None
    # Complex refactoring should go to Claude (200K context, architectural planning)
    # due to high complexity score and multi-file context needs
    assert assigned.assigned_agent in ["claude", "cursor"]


def test_assign_simple_test_task(assigner, simple_test_task):
    """Test assignment of simple testing task."""
    assigned = assigner.assign_agent(simple_test_task)

    assert assigned.assigned_agent is not None
    # Simple test tasks should go to Copilot (fast, test generation strength)
    assert assigned.assigned_agent in ["copilot", "cline", "claude"]


def test_assign_mcp_task(assigner, mcp_task):
    """Test assignment of MCP development task."""
    assigned = assigner.assign_agent(mcp_task)

    assert assigned.assigned_agent is not None
    # MCP tasks should go to Cline (native MCP support) or Claude
    assert assigned.assigned_agent in ["cline", "claude", "cursor"]


def test_assign_documentation_task(assigner, documentation_task):
    """Test assignment of documentation task."""
    assigned = assigner.assign_agent(documentation_task)

    assert assigned.assigned_agent is not None
    # Documentation should go to Claude (long-form documentation strength)
    assert assigned.assigned_agent == "claude"


def test_manual_override(assigner, backend_api_task):
    """Test manual agent override."""
    assigned = assigner.assign_agent(backend_api_task, manual_override="cursor")

    assert assigned.assigned_agent == "cursor"


def test_invalid_manual_override(assigner, backend_api_task):
    """Test that invalid manual override raises error."""
    with pytest.raises(ValueError):
        assigner.assign_agent(backend_api_task, manual_override="invalid_agent")


def test_assign_multiple_tasks(assigner, backend_api_task, frontend_task, devops_task):
    """Test assigning multiple tasks."""
    tasks = [backend_api_task, frontend_task, devops_task]
    assigned_tasks = assigner.assign_agents(tasks)

    assert len(assigned_tasks) == 3
    assert all(task.assigned_agent is not None for task in assigned_tasks)


def test_assign_with_manual_overrides(assigner, backend_api_task, frontend_task):
    """Test assigning tasks with manual overrides."""
    tasks = [backend_api_task, frontend_task]
    overrides = {"backend-1": "copilot"}

    assigned_tasks = assigner.assign_agents(tasks, manual_overrides=overrides)

    assert assigned_tasks[0].assigned_agent == "copilot"
    assert assigned_tasks[1].assigned_agent is not None


def test_get_assignment_summary(assigner, backend_api_task, frontend_task, devops_task):
    """Test getting assignment summary."""
    # Manually assign agents for predictable summary
    backend_api_task.assigned_agent = "claude"
    frontend_task.assigned_agent = "cursor"
    devops_task.assigned_agent = "gemini"

    tasks = [backend_api_task, frontend_task, devops_task]
    summary = assigner.get_assignment_summary(tasks)

    assert "claude" in summary
    assert "cursor" in summary
    assert "gemini" in summary
    assert "backend-1" in summary["claude"]
    assert "frontend-1" in summary["cursor"]
    assert "devops-1" in summary["gemini"]


def test_scoring_complexity_match(assigner):
    """Test complexity matching in scoring."""
    agent_config = assigner.agents["claude"]

    # Claude should score well for complex tasks
    complex_score = assigner._score_complexity_match(Complexity.COMPLEX, agent_config)
    assert complex_score > 0

    # Copilot should score well for simple tasks
    copilot_config = assigner.agents["copilot"]
    simple_score = assigner._score_complexity_match(Complexity.SIMPLE, copilot_config)
    assert simple_score > 0


def test_scoring_tech_stack_match(assigner):
    """Test tech stack matching in scoring."""
    agent_config = assigner.agents["claude"]

    # Test Python match
    score = assigner._score_tech_stack_match(["python", "typescript"], agent_config)
    assert score > 0


def test_scoring_context_window(assigner, legacy_refactoring_task):
    """Test context window scoring."""
    # Claude has large context window (200K)
    claude_config = assigner.agents["claude"]
    score = assigner._score_context_window(legacy_refactoring_task, claude_config)
    assert score > 0

    # Copilot has smaller context window (8K)
    copilot_config = assigner.agents["copilot"]
    copilot_score = assigner._score_context_window(
        legacy_refactoring_task, copilot_config
    )
    # Claude should score higher than Copilot for large context needs
    assert score >= copilot_score


def test_unknown_task_type_assignment(assigner):
    """Test assignment of task with unknown type."""
    unknown_task = Task(
        id="unknown-1",
        title="Generic task",
        description="A task with unknown type",
        phase="Phase 1",
        stage="Stage 1.1",
        task_type=TaskType.UNKNOWN,
        complexity=Complexity.MEDIUM,
    )

    assigned = assigner.assign_agent(unknown_task)

    # Should still assign an agent (fallback logic)
    assert assigned.assigned_agent is not None
