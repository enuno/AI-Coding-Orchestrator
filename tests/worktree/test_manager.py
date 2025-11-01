"""Tests for worktree manager."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from orchestrator.core.models import Task
from orchestrator.worktree.manager import Worktree, WorktreeManager


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test-repo"
        repo_path.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        # Disable GPG signing for tests
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Rename default branch to 'main' for consistency
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


@pytest.fixture
def worktree_manager(temp_git_repo):
    """Create a worktree manager instance."""
    worktree_base = temp_git_repo.parent / "worktrees"
    manager = WorktreeManager(repo_path=temp_git_repo, worktree_base_dir=worktree_base)
    yield manager

    # Cleanup
    manager.cleanup_all(force=True)


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        id="test-task-1",
        title="Test Task",
        description="A test task",
        phase="Phase 1",
        stage="Stage 1.1",
    )


def test_manager_initialization(temp_git_repo):
    """Test worktree manager initializes correctly."""
    manager = WorktreeManager(repo_path=temp_git_repo)

    assert manager.repo_path == temp_git_repo
    assert manager.worktree_base_dir == temp_git_repo.parent / "worktrees"
    assert len(manager.worktrees) == 0


def test_generate_branch_name(worktree_manager):
    """Test branch name generation."""
    branch_name = worktree_manager._generate_branch_name("claude", "task-123")

    assert branch_name == "agent/claude/task-123"


def test_allocate_port(worktree_manager):
    """Test port allocation."""
    port1 = worktree_manager._allocate_port()
    port2 = worktree_manager._allocate_port()

    assert port1 == 3000
    assert port2 == 3001
    assert port1 != port2


def test_create_worktree(worktree_manager, sample_task):
    """Test worktree creation."""
    worktree = worktree_manager.create_worktree("claude", sample_task)

    assert worktree is not None
    assert worktree.agent == "claude"
    assert worktree.task_id == sample_task.id
    assert worktree.branch == "agent/claude/test-task-1"
    assert worktree.status == "active"
    assert worktree.port == 3000

    # Verify worktree path exists
    assert Path(worktree.path).exists()

    # Verify branch was created
    result = subprocess.run(
        ["git", "branch", "--list", worktree.branch],
        cwd=worktree_manager.repo_path,
        capture_output=True,
        text=True,
    )
    assert worktree.branch in result.stdout


def test_create_multiple_worktrees(worktree_manager):
    """Test creating multiple worktrees."""
    task1 = Task(
        id="task-1", title="Task 1", description="First task", phase="Phase 1", stage="Stage 1.1"
    )
    task2 = Task(
        id="task-2", title="Task 2", description="Second task", phase="Phase 1", stage="Stage 1.2"
    )

    worktree1 = worktree_manager.create_worktree("claude", task1)
    worktree2 = worktree_manager.create_worktree("cursor", task2)

    assert worktree1.task_id != worktree2.task_id
    assert worktree1.port != worktree2.port
    assert worktree1.branch != worktree2.branch
    assert Path(worktree1.path).exists()
    assert Path(worktree2.path).exists()


def test_configure_environment(worktree_manager, sample_task):
    """Test environment configuration."""
    worktree = worktree_manager.create_worktree("claude", sample_task)

    env_vars = {"API_KEY": "test-key", "DEBUG": "true"}
    worktree_manager.configure_environment(worktree, env_vars)

    # Check environment variables were set
    assert "PORT" in worktree.env_vars
    assert worktree.env_vars["API_KEY"] == "test-key"
    assert worktree.env_vars["DEBUG"] == "true"

    # Check .env file was created
    env_file = Path(worktree.path) / ".env"
    assert env_file.exists()

    content = env_file.read_text()
    assert "PORT=" in content
    assert "API_KEY=test-key" in content
    assert "DEBUG=true" in content


def test_list_worktrees(worktree_manager):
    """Test listing worktrees."""
    task1 = Task(
        id="task-1", title="Task 1", description="First task", phase="Phase 1", stage="Stage 1.1"
    )
    task2 = Task(
        id="task-2", title="Task 2", description="Second task", phase="Phase 1", stage="Stage 1.2"
    )

    worktree_manager.create_worktree("claude", task1)
    worktree_manager.create_worktree("cursor", task2)

    worktrees = worktree_manager.list_worktrees()

    assert len(worktrees) == 2
    assert all(isinstance(w, Worktree) for w in worktrees)


def test_get_worktree(worktree_manager, sample_task):
    """Test getting worktree by task ID."""
    worktree_manager.create_worktree("claude", sample_task)

    found = worktree_manager.get_worktree(sample_task.id)
    not_found = worktree_manager.get_worktree("nonexistent")

    assert found is not None
    assert found.task_id == sample_task.id
    assert not_found is None


def test_cleanup_worktree(worktree_manager, sample_task):
    """Test worktree cleanup."""
    worktree = worktree_manager.create_worktree("claude", sample_task)
    worktree_path = Path(worktree.path)

    # Verify worktree exists
    assert worktree_path.exists()

    # Cleanup
    worktree_manager.cleanup_worktree(worktree)

    # Verify worktree removed
    assert not worktree_path.exists()
    assert sample_task.id not in worktree_manager.worktrees


def test_cleanup_worktree_with_changes_requires_force(worktree_manager, sample_task):
    """Test that cleanup with uncommitted changes requires force flag."""
    worktree = worktree_manager.create_worktree("claude", sample_task)

    # Make uncommitted changes
    test_file = Path(worktree.path) / "test.txt"
    test_file.write_text("uncommitted change")

    # Cleanup without force should fail
    with pytest.raises(RuntimeError, match="uncommitted changes"):
        worktree_manager.cleanup_worktree(worktree)

    # Cleanup with force should succeed
    worktree_manager.cleanup_worktree(worktree, force=True)
    assert not Path(worktree.path).exists()


def test_cleanup_all(worktree_manager):
    """Test cleanup of all worktrees."""
    task1 = Task(
        id="task-1", title="Task 1", description="First task", phase="Phase 1", stage="Stage 1.1"
    )
    task2 = Task(
        id="task-2", title="Task 2", description="Second task", phase="Phase 1", stage="Stage 1.2"
    )

    worktree1 = worktree_manager.create_worktree("claude", task1)
    worktree2 = worktree_manager.create_worktree("cursor", task2)

    assert len(worktree_manager.worktrees) == 2

    # Cleanup all
    worktree_manager.cleanup_all(force=True)

    assert len(worktree_manager.worktrees) == 0
    assert not Path(worktree1.path).exists()
    assert not Path(worktree2.path).exists()


def test_worktree_base_dir_creation(temp_git_repo):
    """Test that worktree base directory is created if it doesn't exist."""
    worktree_base = temp_git_repo.parent / "custom-worktrees"
    assert not worktree_base.exists()

    manager = WorktreeManager(repo_path=temp_git_repo, worktree_base_dir=worktree_base)
    task = Task(
        id="test-1", title="Test", description="Test task", phase="Phase 1", stage="Stage 1.1"
    )

    manager.create_worktree("claude", task)

    assert worktree_base.exists()
    manager.cleanup_all(force=True)


def test_worktree_dataclass():
    """Test Worktree dataclass."""
    worktree = Worktree(
        path="/path/to/worktree",
        branch="agent/claude/task-1",
        agent="claude",
        task_id="task-1",
        port=3000,
        env_file="/path/to/.env",
        env_vars={"KEY": "value"},
        status="active",
    )

    assert worktree.path == "/path/to/worktree"
    assert worktree.agent == "claude"
    assert worktree.port == 3000
    assert worktree.status == "active"


def test_worktree_status(worktree_manager, sample_task):
    """Test worktree status tracking."""
    worktree = worktree_manager.create_worktree("claude", sample_task)

    assert worktree.status == "active"

    # Update status
    worktree.status = "completed"
    assert worktree.status == "completed"
