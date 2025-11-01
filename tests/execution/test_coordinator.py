"""Tests for execution coordinator."""

import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from orchestrator.classifier.agent_assigner import AgentAssignment
from orchestrator.core.models import Task
from orchestrator.execution.coordinator import (
    AgentExecution,
    ExecutionCoordinator,
    ExecutionStatus,
)
from orchestrator.worktree.manager import Worktree


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        id="test-task-1",
        title="Test Task",
        description="A test task",
        phase="Phase 1",
        stage="Stage 1.1",
        objective="Test objective",
        key_activities=["Activity 1", "Activity 2"],
        deliverables=["Deliverable 1"],
        validation_criteria=["Criterion 1"],
    )


@pytest.fixture
def sample_worktree():
    """Create a sample worktree."""
    return Worktree(
        path="/tmp/worktree-test",
        branch="agent/claude/test-task-1",
        agent="claude",
        task_id="test-task-1",
        port=3000,
        status="active",
    )


@pytest.fixture
def sample_assignment(sample_task):
    """Create a sample agent assignment."""
    return AgentAssignment(
        task=sample_task,
        primary_agent="claude",
        secondary_agents=[],
        phase="implementation",
        justification="Claude is best for this task",
        confidence=0.95,
        task_type="backend_api",
        complexity="medium",
        tech_stack=["python"],
    )


def test_agent_execution_creation(sample_worktree, sample_assignment):
    """Test AgentExecution dataclass creation."""
    execution = AgentExecution(worktree=sample_worktree, assignment=sample_assignment)

    assert execution.worktree == sample_worktree
    assert execution.assignment == sample_assignment
    assert execution.status == ExecutionStatus.PENDING
    assert execution.start_time is None
    assert execution.end_time is None
    assert execution.logs == []
    assert execution.result is None
    assert execution.return_code is None
    assert execution.timeout_seconds == 3600


def test_agent_execution_duration(sample_worktree, sample_assignment):
    """Test duration calculation."""
    execution = AgentExecution(worktree=sample_worktree, assignment=sample_assignment)

    # No duration when not started
    assert execution.duration is None

    # Set times and check duration
    execution.start_time = datetime(2025, 1, 1, 12, 0, 0)
    execution.end_time = datetime(2025, 1, 1, 12, 5, 30)

    assert execution.duration == 330.0  # 5 minutes 30 seconds


def test_agent_execution_is_successful(sample_worktree, sample_assignment):
    """Test success check."""
    execution = AgentExecution(worktree=sample_worktree, assignment=sample_assignment)

    # Not successful initially
    assert not execution.is_successful

    # Successful when completed with return code 0
    execution.status = ExecutionStatus.COMPLETED
    execution.return_code = 0
    assert execution.is_successful

    # Not successful if return code != 0
    execution.return_code = 1
    assert not execution.is_successful

    # Not successful if status is not COMPLETED
    execution.status = ExecutionStatus.FAILED
    execution.return_code = 0
    assert not execution.is_successful


def test_agent_execution_add_log(sample_worktree, sample_assignment):
    """Test log addition."""
    execution = AgentExecution(worktree=sample_worktree, assignment=sample_assignment)

    execution.add_log("Test message")

    assert len(execution.logs) == 1
    assert "Test message" in execution.logs[0]
    assert datetime.now().strftime("%Y-%m-%d") in execution.logs[0]


def test_execution_coordinator_init():
    """Test ExecutionCoordinator initialization."""
    coordinator = ExecutionCoordinator(max_concurrent=3)

    assert coordinator.max_concurrent == 3
    assert coordinator.executions == {}
    assert coordinator._semaphore._value == 3  # Semaphore with 3 slots


@pytest.mark.asyncio
async def test_execute_parallel_success(sample_assignment, sample_worktree):
    """Test successful parallel execution."""
    coordinator = ExecutionCoordinator(max_concurrent=2)

    # Create assignments and worktrees
    assignments = [sample_assignment]
    worktrees = {sample_assignment.task.id: sample_worktree}

    # Execute
    executions = await coordinator.execute_parallel(assignments, worktrees)

    assert len(executions) == 1
    assert executions[0].status == ExecutionStatus.COMPLETED
    assert executions[0].return_code == 0
    assert executions[0].start_time is not None
    assert executions[0].end_time is not None
    assert len(executions[0].logs) > 0


@pytest.mark.asyncio
async def test_execute_parallel_multiple(sample_task, sample_worktree):
    """Test executing multiple assignments in parallel."""
    coordinator = ExecutionCoordinator(max_concurrent=5)

    # Create multiple assignments
    assignments = []
    worktrees = {}
    for i in range(3):
        task = Task(
            id=f"task-{i}",
            title=f"Task {i}",
            description=f"Task {i}",
            phase="Phase 1",
            stage="Stage 1.1",
        )
        assignment = AgentAssignment(
            task=task,
            primary_agent="claude",
            secondary_agents=[],
            phase="implementation",
            justification="Test",
            confidence=0.9,
            task_type="backend_api",
            complexity="medium",
            tech_stack=["python"],
        )
        worktree = Worktree(
            path=f"/tmp/worktree-{i}",
            branch=f"agent/claude/task-{i}",
            agent="claude",
            task_id=f"task-{i}",
            port=3000 + i,
            status="active",
        )
        assignments.append(assignment)
        worktrees[task.id] = worktree

    # Execute
    executions = await coordinator.execute_parallel(assignments, worktrees)

    assert len(executions) == 3
    assert all(ex.status == ExecutionStatus.COMPLETED for ex in executions)
    assert all(ex.return_code == 0 for ex in executions)


@pytest.mark.asyncio
async def test_execute_parallel_with_timeout(sample_assignment, sample_worktree):
    """Test execution with timeout."""
    coordinator = ExecutionCoordinator()

    # Create execution with very short timeout
    execution = AgentExecution(
        worktree=sample_worktree,
        assignment=sample_assignment,
        timeout_seconds=0.01,  # Very short timeout (10ms)
    )
    coordinator.executions[sample_assignment.task.id] = execution

    # Mock _run_agent to raise TimeoutError
    async def timeout_agent(exec):
        raise asyncio.TimeoutError("Operation timed out")

    with patch.object(coordinator, "_run_agent", new=timeout_agent):
        await coordinator._execute_single(execution)

        assert execution.status == ExecutionStatus.TIMEOUT
        assert execution.return_code == -1
        assert "timed out" in execution.logs[-1].lower()


@pytest.mark.asyncio
async def test_execute_parallel_with_failure(sample_assignment, sample_worktree):
    """Test execution handling failures."""
    coordinator = ExecutionCoordinator()

    # Mock _run_agent to raise exception
    async def failing_agent(*args, **kwargs):
        raise ValueError("Test error")

    with patch.object(coordinator, "_run_agent", new=failing_agent):
        assignments = [sample_assignment]
        worktrees = {sample_assignment.task.id: sample_worktree}

        executions = await coordinator.execute_parallel(assignments, worktrees)

        assert len(executions) == 1
        assert executions[0].status == ExecutionStatus.FAILED
        assert executions[0].return_code == 1
        assert "Test error" in executions[0].result


def test_monitor_progress(sample_assignment, sample_worktree):
    """Test progress monitoring."""
    coordinator = ExecutionCoordinator()

    execution = AgentExecution(worktree=sample_worktree, assignment=sample_assignment)
    coordinator.executions[sample_assignment.task.id] = execution

    progress = coordinator.monitor_progress()

    assert len(progress) == 1
    assert sample_assignment.task.id in progress
    assert progress[sample_assignment.task.id] == execution


def test_get_execution(sample_assignment, sample_worktree):
    """Test getting execution by task ID."""
    coordinator = ExecutionCoordinator()

    execution = AgentExecution(worktree=sample_worktree, assignment=sample_assignment)
    coordinator.executions[sample_assignment.task.id] = execution

    found = coordinator.get_execution(sample_assignment.task.id)
    not_found = coordinator.get_execution("nonexistent")

    assert found == execution
    assert not_found is None


@pytest.mark.asyncio
async def test_wait_for_completion(sample_assignment, sample_worktree):
    """Test waiting for completion."""
    coordinator = ExecutionCoordinator()

    execution = AgentExecution(worktree=sample_worktree, assignment=sample_assignment)
    execution.status = ExecutionStatus.COMPLETED
    coordinator.executions[sample_assignment.task.id] = execution

    result = await coordinator.wait_for_completion(timeout=5)

    assert len(result) == 1
    assert result[0] == execution


@pytest.mark.asyncio
async def test_wait_for_completion_timeout():
    """Test wait for completion timeout."""
    coordinator = ExecutionCoordinator()

    # Create pending execution that never completes
    task = Task(
        id="pending-task",
        title="Pending",
        description="Test",
        phase="Phase 1",
        stage="Stage 1.1",
    )
    worktree = Worktree(
        path="/tmp/test",
        branch="test",
        agent="claude",
        task_id="pending-task",
        port=3000,
        status="active",
    )
    assignment = AgentAssignment(
        task=task,
        primary_agent="claude",
        secondary_agents=[],
        phase="implementation",
        justification="Test",
        confidence=0.9,
        task_type="backend_api",
        complexity="medium",
        tech_stack=["python"],
    )

    execution = AgentExecution(worktree=worktree, assignment=assignment)
    execution.status = ExecutionStatus.RUNNING  # Never completes
    coordinator.executions[task.id] = execution

    with pytest.raises(asyncio.TimeoutError):
        await coordinator.wait_for_completion(timeout=1)


def test_get_summary(sample_assignment, sample_worktree):
    """Test getting execution summary."""
    coordinator = ExecutionCoordinator()

    # Create executions with different statuses
    for status in [
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMEOUT,
        ExecutionStatus.RUNNING,
        ExecutionStatus.PENDING,
    ]:
        task = Task(
            id=f"task-{status.value}",
            title=status.value,
            description="Test",
            phase="Phase 1",
            stage="Stage 1.1",
        )
        worktree = Worktree(
            path=f"/tmp/{status.value}",
            branch="test",
            agent="claude",
            task_id=task.id,
            port=3000,
            status="active",
        )
        assignment = AgentAssignment(
            task=task,
            primary_agent="claude",
            secondary_agents=[],
            phase="implementation",
            justification="Test",
            confidence=0.9,
            task_type="backend_api",
            complexity="medium",
            tech_stack=["python"],
        )
        execution = AgentExecution(worktree=worktree, assignment=assignment)
        execution.status = status
        coordinator.executions[task.id] = execution

    summary = coordinator.get_summary()

    assert summary["total"] == 5
    assert summary["completed"] == 1
    assert summary["failed"] == 1
    assert summary["timeout"] == 1
    assert summary["running"] == 1
    assert summary["pending"] == 1


def test_cancel_all(sample_assignment, sample_worktree):
    """Test cancelling all executions."""
    coordinator = ExecutionCoordinator()

    # Create running and pending executions
    for i, status in enumerate([ExecutionStatus.RUNNING, ExecutionStatus.PENDING]):
        task = Task(
            id=f"task-{i}",
            title=f"Task {i}",
            description="Test",
            phase="Phase 1",
            stage="Stage 1.1",
        )
        worktree = Worktree(
            path=f"/tmp/{i}",
            branch="test",
            agent="claude",
            task_id=task.id,
            port=3000,
            status="active",
        )
        assignment = AgentAssignment(
            task=task,
            primary_agent="claude",
            secondary_agents=[],
            phase="implementation",
            justification="Test",
            confidence=0.9,
            task_type="backend_api",
            complexity="medium",
            tech_stack=["python"],
        )
        execution = AgentExecution(worktree=worktree, assignment=assignment)
        execution.status = status
        coordinator.executions[task.id] = execution

    # Cancel all
    coordinator.cancel_all()

    # Check all are cancelled
    assert all(
        ex.status == ExecutionStatus.CANCELLED for ex in coordinator.executions.values()
    )
    assert all(ex.end_time is not None for ex in coordinator.executions.values())
    assert all("cancelled" in ex.logs[-1].lower() for ex in coordinator.executions.values())
