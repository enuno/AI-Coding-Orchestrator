"""Tests for agent prompt generator."""

import pytest

from orchestrator.classifier.agent_assigner import AgentAssignment
from orchestrator.core.models import Task
from orchestrator.execution.prompts import PromptGenerator


@pytest.fixture
def sample_task():
    """Create a sample task with all fields."""
    return Task(
        id="test-task-1",
        title="Implement User Authentication",
        description="Add JWT-based authentication system",
        phase="Phase 1",
        stage="Stage 1.2",
        objective="Implement secure user authentication",
        key_activities=[
            "Create user model",
            "Implement JWT token generation",
            "Add authentication middleware",
        ],
        deliverables=[
            "User authentication API",
            "JWT token handling",
            "Protected routes",
        ],
        validation_criteria=[
            "All authentication tests pass",
            "Token expiration works correctly",
            "Unauthorized access blocked",
        ],
        technical_implementation="class UserAuth:\n    def authenticate(self, user, password):\n        pass",
    )


@pytest.fixture
def minimal_task():
    """Create a minimal task."""
    return Task(
        id="minimal-1",
        title="Minimal Task",
        description="A minimal task",
        phase="Phase 1",
        stage="Stage 1.1",
    )


@pytest.fixture
def sample_assignment(sample_task):
    """Create a sample agent assignment."""
    return AgentAssignment(
        task=sample_task,
        primary_agent="claude",
        secondary_agents=[],
        phase="implementation",
        justification="Claude is best suited for implementing authentication systems with its large context window and security expertise",
        confidence=0.95,
        task_type="backend_api",
        complexity="medium",
        tech_stack=["python", "jwt"],
    )


def test_prompt_generator_init():
    """Test PromptGenerator initialization."""
    generator = PromptGenerator()
    assert generator is not None


def test_generate_task_prompt_full(sample_assignment):
    """Test generating a complete task prompt."""
    generator = PromptGenerator()
    prompt = generator.generate_task_prompt(sample_assignment, "/tmp/worktree")

    # Check header
    assert "# Task Assignment for Claude" in prompt

    # Check task overview
    assert "test-task-1" in prompt
    assert "Implement User Authentication" in prompt
    assert "Phase 1" in prompt
    assert "Stage 1.2" in prompt

    # Check objective
    assert "Implement secure user authentication" in prompt

    # Check key activities
    assert "Create user model" in prompt
    assert "Implement JWT token generation" in prompt
    assert "Add authentication middleware" in prompt

    # Check deliverables
    assert "User authentication API" in prompt
    assert "JWT token handling" in prompt
    assert "Protected routes" in prompt

    # Check validation criteria
    assert "All authentication tests pass" in prompt
    assert "Token expiration works correctly" in prompt
    assert "Unauthorized access blocked" in prompt

    # Check technical implementation
    assert "class UserAuth:" in prompt
    assert "def authenticate(self, user, password):" in prompt

    # Check environment
    assert "/tmp/worktree" in prompt

    # Check justification
    assert "Claude is best suited" in prompt

    # Check instructions
    assert "Instructions" in prompt


def test_generate_task_prompt_minimal(minimal_task):
    """Test generating prompt for minimal task."""
    generator = PromptGenerator()
    assignment = AgentAssignment(
        task=minimal_task,
        primary_agent="cursor",
        secondary_agents=[],
        phase="implementation",
        justification="Cursor handles simple tasks well",
        confidence=0.8,
        task_type="feature",
        complexity="simple",
        tech_stack=["python"],
    )

    prompt = generator.generate_task_prompt(assignment, "/tmp/test")

    # Should handle missing fields gracefully
    assert "Minimal Task" in prompt
    assert "minimal-1" in prompt
    assert "(No specific activities listed)" in prompt
    assert "(No specific deliverables listed)" in prompt
    assert "(No specific criteria listed)" in prompt
    assert "Technical Implementation" not in prompt  # No implementation provided


def test_agent_specific_instructions_claude():
    """Test Claude-specific instructions."""
    generator = PromptGenerator()
    instructions = generator._get_agent_specific_instructions("claude")

    assert "Review the task objectives" in instructions
    assert "minimum 85% coverage" in instructions
    assert "best practices" in instructions


def test_agent_specific_instructions_cursor():
    """Test Cursor-specific instructions."""
    generator = PromptGenerator()
    instructions = generator._get_agent_specific_instructions("cursor")

    assert "Agent or Composer mode" in instructions
    assert "repository-wide context" in instructions
    assert "inline suggestions" in instructions


def test_agent_specific_instructions_copilot():
    """Test Copilot-specific instructions."""
    generator = PromptGenerator()
    instructions = generator._get_agent_specific_instructions("copilot")

    assert "autocomplete suggestions" in instructions
    assert "established code patterns" in instructions


def test_agent_specific_instructions_gemini():
    """Test Gemini-specific instructions."""
    generator = PromptGenerator()
    instructions = generator._get_agent_specific_instructions("gemini")

    assert "Review task requirements" in instructions
    assert "maintainable code" in instructions


def test_agent_specific_instructions_cline():
    """Test Cline-specific instructions."""
    generator = PromptGenerator()
    instructions = generator._get_agent_specific_instructions("cline")

    assert "Plan/Act mode" in instructions
    assert "step-by-step" in instructions


def test_agent_specific_instructions_windsurf():
    """Test Windsurf-specific instructions."""
    generator = PromptGenerator()
    instructions = generator._get_agent_specific_instructions("windsurf")

    assert "Cascade mode" in instructions
    assert "privacy-first" in instructions


def test_agent_specific_instructions_unknown():
    """Test instructions for unknown agent."""
    generator = PromptGenerator()
    instructions = generator._get_agent_specific_instructions("unknown_agent")

    # Should return generic instructions
    assert "Review the task objectives" in instructions
    assert "best practices" in instructions


def test_generate_batch_prompts(sample_assignment):
    """Test generating prompts for multiple assignments."""
    generator = PromptGenerator()

    # Create multiple assignments
    task2 = Task(
        id="task-2",
        title="Task 2",
        description="Second task",
        phase="Phase 1",
        stage="Stage 1.2",
    )
    assignment2 = AgentAssignment(
        task=task2,
        primary_agent="cursor",
        secondary_agents=[],
        phase="implementation",
        justification="Test",
        confidence=0.9,
        task_type="feature",
        complexity="simple",
        tech_stack=["python"],
    )

    assignments = [sample_assignment, assignment2]
    worktree_paths = {
        sample_assignment.task.id: "/tmp/worktree-1",
        task2.id: "/tmp/worktree-2",
    }

    prompts = generator.generate_batch_prompts(assignments, worktree_paths)

    assert len(prompts) == 2
    assert sample_assignment.task.id in prompts
    assert task2.id in prompts
    assert "/tmp/worktree-1" in prompts[sample_assignment.task.id]
    assert "/tmp/worktree-2" in prompts[task2.id]


def test_generate_context_prompt_full():
    """Test generating context prompt with all fields."""
    generator = PromptGenerator()
    task = Task(
        id="test-1",
        title="Test",
        description="Test task",
        phase="Phase 1",
        stage="Stage 1.1",
    )

    project_context = {
        "name": "My Project",
        "description": "A test project",
        "tech_stack": ["python", "react", "docker"],
        "coding_standards": ["PEP 8", "ESLint", "Type hints required"],
        "test_requirements": ["85% coverage", "All tests must pass", "Integration tests"],
    }

    context = generator.generate_context_prompt(task, project_context)

    assert "My Project" in context
    assert "A test project" in context
    assert "python, react, docker" in context
    assert "PEP 8" in context
    assert "Type hints required" in context
    assert "85% coverage" in context
    assert "Integration tests" in context


def test_generate_context_prompt_minimal():
    """Test generating context prompt with minimal fields."""
    generator = PromptGenerator()
    task = Task(
        id="test-1",
        title="Test",
        description="Test task",
        phase="Phase 1",
        stage="Stage 1.1",
    )

    project_context = {"name": "Simple Project"}

    context = generator.generate_context_prompt(task, project_context)

    assert "Simple Project" in context
    assert "Project Context" in context


def test_generate_context_prompt_empty():
    """Test generating context prompt with empty context."""
    generator = PromptGenerator()
    task = Task(
        id="test-1",
        title="Test",
        description="Test task",
        phase="Phase 1",
        stage="Stage 1.1",
    )

    project_context = {}

    context = generator.generate_context_prompt(task, project_context)

    # Should handle empty context gracefully
    assert "Project Context" in context


def test_prompt_format_consistency(sample_assignment):
    """Test that generated prompts have consistent format."""
    generator = PromptGenerator()

    prompts = []
    for agent in ["claude", "cursor", "copilot", "gemini", "cline", "windsurf"]:
        assignment = AgentAssignment(
            task=sample_assignment.task,
            primary_agent=agent,
            secondary_agents=[],
            phase="implementation",
            justification=f"{agent} is best for this",
            confidence=0.9,
            task_type="backend_api",
            complexity="medium",
            tech_stack=["python"],
        )
        prompt = generator.generate_task_prompt(assignment, "/tmp/test")
        prompts.append(prompt)

    # All prompts should have consistent sections
    for prompt in prompts:
        assert "## Task Overview" in prompt
        assert "## Objective" in prompt
        assert "## Key Activities" in prompt
        assert "## Deliverables" in prompt
        assert "## Validation Criteria" in prompt
        assert "## Execution Environment" in prompt
        assert "## Why You Were Assigned" in prompt
        assert "## Instructions" in prompt
