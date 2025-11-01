"""Execution coordinator for parallel agent execution."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from orchestrator.classifier.agent_assigner import AgentAssignment
from orchestrator.worktree.manager import Worktree

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class AgentExecution:
    """Represents an agent execution in a worktree.

    Attributes:
        worktree: The worktree where execution happens
        assignment: The agent assignment details
        status: Current execution status
        start_time: When execution started
        end_time: When execution completed
        logs: Execution logs
        result: Execution result or error message
        return_code: Process return code
        timeout_seconds: Execution timeout in seconds
    """

    worktree: Worktree
    assignment: AgentAssignment
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    logs: List[str] = field(default_factory=list)
    result: Optional[str] = None
    return_code: Optional[int] = None
    timeout_seconds: int = 3600  # 1 hour default

    @property
    def duration(self) -> Optional[float]:
        """Calculate execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.COMPLETED and self.return_code == 0

    def add_log(self, message: str) -> None:
        """Add a log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")


class ExecutionCoordinator:
    """Coordinates parallel execution of agents in worktrees.

    This class manages the lifecycle of agent executions, including:
    - Launching agents in parallel
    - Monitoring progress
    - Handling timeouts and failures
    - Collecting results
    """

    def __init__(self, max_concurrent: int = 5):
        """Initialize the execution coordinator.

        Args:
            max_concurrent: Maximum number of concurrent executions
        """
        self.max_concurrent = max_concurrent
        self.executions: Dict[str, AgentExecution] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_parallel(
        self, assignments: List[AgentAssignment], worktrees: Dict[str, Worktree]
    ) -> List[AgentExecution]:
        """Execute multiple agent assignments in parallel.

        Args:
            assignments: List of agent assignments to execute
            worktrees: Dictionary mapping task IDs to worktrees

        Returns:
            List of execution results
        """
        # Create execution objects
        executions = []
        for assignment in assignments:
            worktree = worktrees.get(assignment.task.id)
            if not worktree:
                logger.error(f"No worktree found for task {assignment.task.id}")
                continue

            execution = AgentExecution(
                worktree=worktree,
                assignment=assignment,
            )
            self.executions[assignment.task.id] = execution
            executions.append(execution)

        # Execute in parallel with concurrency limit
        tasks = [self._execute_single(execution) for execution in executions]
        await asyncio.gather(*tasks, return_exceptions=True)

        return executions

    async def _execute_single(self, execution: AgentExecution) -> None:
        """Execute a single agent assignment.

        Args:
            execution: The execution to run
        """
        async with self._semaphore:
            execution.status = ExecutionStatus.RUNNING
            execution.start_time = datetime.now()
            execution.add_log(
                f"Starting execution: {execution.assignment.primary_agent} "
                f"on task {execution.assignment.task.id}"
            )

            try:
                # Simulate agent execution (in real implementation, this would
                # launch the actual agent process)
                result = await self._run_agent(execution)
                execution.result = result
                execution.return_code = 0
                execution.status = ExecutionStatus.COMPLETED
                execution.add_log("Execution completed successfully")

            except asyncio.TimeoutError:
                execution.status = ExecutionStatus.TIMEOUT
                execution.return_code = -1
                execution.add_log(
                    f"Execution timed out after {execution.timeout_seconds} seconds"
                )

            except Exception as e:
                execution.status = ExecutionStatus.FAILED
                execution.return_code = 1
                execution.result = str(e)
                execution.add_log(f"Execution failed: {str(e)}")
                logger.exception(f"Execution failed for task {execution.assignment.task.id}")

            finally:
                execution.end_time = datetime.now()

    async def _run_agent(self, execution: AgentExecution) -> str:
        """Run the agent in the worktree.

        This is a placeholder for the actual agent execution logic.
        In a real implementation, this would:
        1. Generate agent-specific prompts
        2. Launch the agent process in the worktree
        3. Monitor execution
        4. Collect results

        Args:
            execution: The execution to run

        Returns:
            Execution result message
        """
        # Simulate agent work
        execution.add_log(f"Working in worktree: {execution.worktree.path}")
        execution.add_log(f"Agent: {execution.assignment.primary_agent}")
        execution.add_log(f"Task: {execution.assignment.task.title}")

        # Simulate some work with timeout
        try:
            await asyncio.wait_for(
                asyncio.sleep(1),  # Simulated work
                timeout=execution.timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise

        return f"Completed task: {execution.assignment.task.title}"

    def monitor_progress(self) -> Dict[str, AgentExecution]:
        """Get current status of all executions.

        Returns:
            Dictionary mapping task IDs to execution objects
        """
        return self.executions.copy()

    def get_execution(self, task_id: str) -> Optional[AgentExecution]:
        """Get execution by task ID.

        Args:
            task_id: The task ID to look up

        Returns:
            AgentExecution if found, None otherwise
        """
        return self.executions.get(task_id)

    async def wait_for_completion(self, timeout: int = 3600) -> List[AgentExecution]:
        """Wait for all executions to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            List of all executions

        Raises:
            asyncio.TimeoutError: If timeout is exceeded
        """
        start_time = datetime.now()

        while True:
            # Check if all executions are done
            all_done = all(
                exec.status
                in [
                    ExecutionStatus.COMPLETED,
                    ExecutionStatus.FAILED,
                    ExecutionStatus.TIMEOUT,
                    ExecutionStatus.CANCELLED,
                ]
                for exec in self.executions.values()
            )

            if all_done:
                break

            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise asyncio.TimeoutError(
                    f"Wait for completion timed out after {timeout} seconds"
                )

            # Wait a bit before checking again
            await asyncio.sleep(0.5)

        return list(self.executions.values())

    def get_summary(self) -> Dict[str, int]:
        """Get execution summary statistics.

        Returns:
            Dictionary with counts by status
        """
        summary = {
            "total": len(self.executions),
            "completed": 0,
            "failed": 0,
            "timeout": 0,
            "running": 0,
            "pending": 0,
        }

        for execution in self.executions.values():
            if execution.status == ExecutionStatus.COMPLETED:
                summary["completed"] += 1
            elif execution.status == ExecutionStatus.FAILED:
                summary["failed"] += 1
            elif execution.status == ExecutionStatus.TIMEOUT:
                summary["timeout"] += 1
            elif execution.status == ExecutionStatus.RUNNING:
                summary["running"] += 1
            elif execution.status == ExecutionStatus.PENDING:
                summary["pending"] += 1

        return summary

    def cancel_all(self) -> None:
        """Cancel all running executions."""
        for execution in self.executions.values():
            if execution.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
                execution.status = ExecutionStatus.CANCELLED
                execution.end_time = datetime.now()
                execution.add_log("Execution cancelled")
