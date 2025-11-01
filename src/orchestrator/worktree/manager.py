"""Git worktree manager for parallel agent execution."""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from orchestrator.core.models import Task


@dataclass
class Worktree:
    """Represents a git worktree for agent execution."""

    path: str
    branch: str
    agent: str
    task_id: str
    port: Optional[int] = None
    env_file: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    status: str = "active"  # active, completed, failed


class WorktreeManager:
    """Manages git worktrees for parallel agent execution."""

    def __init__(self, repo_path: Optional[Path] = None, worktree_base_dir: Optional[Path] = None) -> None:
        """Initialize the worktree manager.

        Args:
            repo_path: Path to the git repository (defaults to current directory)
            worktree_base_dir: Base directory for worktrees (defaults to ../worktrees)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.worktree_base_dir = worktree_base_dir or self.repo_path.parent / "worktrees"
        self.worktrees: Dict[str, Worktree] = {}
        self._port_counter = 3000  # Starting port for dev servers

    def create_worktree(
        self,
        agent: str,
        task: Task,
        base_branch: str = "main",
    ) -> Worktree:
        """Create an isolated worktree for agent execution.

        Args:
            agent: Name of the AI agent
            task: Task to be executed
            base_branch: Base branch to branch from

        Returns:
            Created Worktree object
        """
        # Generate branch name: agent/{agent-name}/{task-id}
        branch_name = self._generate_branch_name(agent, task.id)

        # Generate worktree path
        worktree_path = self.worktree_base_dir / f"worktree-{agent}-{task.id}"

        # Ensure base directory exists
        self.worktree_base_dir.mkdir(parents=True, exist_ok=True)

        # Create the worktree
        try:
            # Create new branch from base
            subprocess.run(
                ["git", "branch", branch_name, base_branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Create worktree
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Allocate port for this worktree
            port = self._allocate_port()

            # Create worktree object
            worktree = Worktree(
                path=str(worktree_path),
                branch=branch_name,
                agent=agent,
                task_id=task.id,
                port=port,
                status="active",
            )

            # Track the worktree
            self.worktrees[task.id] = worktree

            return worktree

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create worktree: {e.stderr}") from e

    def _generate_branch_name(self, agent: str, task_id: str) -> str:
        """Generate branch name following convention.

        Args:
            agent: Agent name
            task_id: Task ID

        Returns:
            Branch name string
        """
        # Naming convention: agent/{agent-name}/{task-id}
        return f"agent/{agent}/{task_id}"

    def _allocate_port(self) -> int:
        """Allocate a unique port for the worktree.

        Returns:
            Allocated port number
        """
        port = self._port_counter
        self._port_counter += 1
        return port

    def configure_environment(
        self, worktree: Worktree, env_vars: Optional[Dict[str, str]] = None
    ) -> None:
        """Configure environment variables for the worktree.

        Args:
            worktree: Worktree to configure
            env_vars: Environment variables to set
        """
        env_vars = env_vars or {}

        # Add port to environment
        env_vars["PORT"] = str(worktree.port)
        env_vars["DEV_SERVER_PORT"] = str(worktree.port)

        # Set environment variables
        worktree.env_vars = env_vars

        # Create .env file in worktree
        env_file_path = Path(worktree.path) / ".env"
        with open(env_file_path, "w", encoding="utf-8") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        worktree.env_file = str(env_file_path)

    def list_worktrees(self) -> List[Worktree]:
        """List all managed worktrees.

        Returns:
            List of Worktree objects
        """
        return list(self.worktrees.values())

    def get_worktree(self, task_id: str) -> Optional[Worktree]:
        """Get worktree by task ID.

        Args:
            task_id: Task ID

        Returns:
            Worktree object or None if not found
        """
        return self.worktrees.get(task_id)

    def cleanup_worktree(self, worktree: Worktree, force: bool = False) -> None:
        """Safely remove worktree and artifacts.

        Args:
            worktree: Worktree to clean up
            force: Force cleanup even if worktree has uncommitted changes
        """
        worktree_path = Path(worktree.path)

        # Check if worktree exists
        if not worktree_path.exists():
            # Remove from tracking
            if worktree.task_id in self.worktrees:
                del self.worktrees[worktree.task_id]
            return

        # Check for uncommitted changes
        if not force:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                raise RuntimeError(
                    f"Worktree {worktree.path} has uncommitted changes. "
                    "Use force=True to cleanup anyway."
                )

        # Remove worktree
        try:
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path)],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            # Try with force if initial attempt fails
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

        # Delete branch (optional, can be kept for history)
        try:
            subprocess.run(
                ["git", "branch", "-D", worktree.branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            # Branch might not exist or already deleted
            pass

        # Remove from tracking
        if worktree.task_id in self.worktrees:
            del self.worktrees[worktree.task_id]

    def cleanup_all(self, force: bool = False) -> None:
        """Clean up all managed worktrees.

        Args:
            force: Force cleanup even if worktrees have uncommitted changes
        """
        worktrees_to_cleanup = list(self.worktrees.values())
        for worktree in worktrees_to_cleanup:
            try:
                self.cleanup_worktree(worktree, force=force)
            except RuntimeError as e:
                # Log error but continue with other worktrees
                print(f"Warning: {e}")
                continue
