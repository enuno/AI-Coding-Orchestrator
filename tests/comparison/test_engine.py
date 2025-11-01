"""Tests for comparison engine."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from orchestrator.classifier.agent_assigner import AgentAssignment
from orchestrator.comparison.engine import ComparisonEngine, ComparisonReport
from orchestrator.comparison.metrics import QualityMetrics
from orchestrator.core.models import Task
from orchestrator.execution.coordinator import AgentExecution
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


@pytest.fixture
def sample_execution(sample_worktree, sample_assignment):
    """Create a sample agent execution."""
    return AgentExecution(worktree=sample_worktree, assignment=sample_assignment)


def test_comparison_report_creation(sample_task, sample_execution):
    """Test ComparisonReport dataclass creation."""
    report = ComparisonReport(
        task_id=sample_task.id, implementations=[sample_execution]
    )

    assert report.task_id == sample_task.id
    assert len(report.implementations) == 1
    assert report.quality_scores == {}
    assert report.code_diffs == {}
    assert report.test_results == {}
    assert report.recommendation == ""
    assert report.confidence == 0.0


def test_comparison_report_get_best_implementation():
    """Test getting the best implementation from report."""
    report = ComparisonReport(
        task_id="test-1",
        implementations=[],
        quality_scores={"claude": 95.0, "cursor": 85.0, "copilot": 90.0},
    )

    best = report.get_best_implementation()
    assert best == "claude"


def test_comparison_report_get_best_implementation_empty():
    """Test get_best_implementation with no scores."""
    report = ComparisonReport(task_id="test-1", implementations=[])

    best = report.get_best_implementation()
    assert best is None


def test_comparison_report_get_summary():
    """Test summary generation."""
    report = ComparisonReport(
        task_id="test-1",
        implementations=[],
        quality_scores={"claude": 95.0, "cursor": 85.0},
        recommendation="claude",
        confidence=0.92,
        analysis="Claude has better test coverage",
    )

    summary = report.get_summary()

    assert "test-1" in summary
    assert "claude: 95.00/100" in summary
    assert "cursor: 85.00/100" in summary
    assert "claude" in summary
    assert "92.00%" in summary
    assert "better test coverage" in summary


def test_comparison_report_get_summary_empty():
    """Test summary with no implementations."""
    report = ComparisonReport(task_id="test-1", implementations=[])

    summary = report.get_summary()
    assert "No implementations to compare" in summary


def test_comparison_engine_init():
    """Test ComparisonEngine initialization."""
    engine = ComparisonEngine()

    assert engine is not None
    assert engine.metrics_collector is not None
    assert engine.diff_analyzer is not None


def test_comparison_engine_compare_implementations_empty():
    """Test compare_implementations with empty list."""
    engine = ComparisonEngine()

    with pytest.raises(ValueError, match="No executions provided"):
        engine.compare_implementations([])


def test_comparison_engine_compare_implementations_different_tasks(
    sample_execution, sample_worktree
):
    """Test compare_implementations with executions for different tasks."""
    engine = ComparisonEngine()

    # Create execution for different task
    task2 = Task(
        id="task-2",
        title="Task 2",
        description="Different task",
        phase="Phase 1",
        stage="Stage 1.1",
    )
    assignment2 = AgentAssignment(
        task=task2,
        primary_agent="cursor",
        secondary_agents=[],
        phase="implementation",
        justification="Test",
        confidence=0.9,
        task_type="frontend",
        complexity="simple",
        tech_stack=["react"],
    )
    worktree2 = Worktree(
        path="/tmp/worktree-2",
        branch="agent/cursor/task-2",
        agent="cursor",
        task_id="task-2",
        port=3001,
        status="active",
    )
    execution2 = AgentExecution(worktree=worktree2, assignment=assignment2)

    with pytest.raises(ValueError, match="same task"):
        engine.compare_implementations([sample_execution, execution2])


def test_comparison_engine_compare_implementations_single(sample_execution):
    """Test compare_implementations with single execution."""
    engine = ComparisonEngine()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Update worktree path to temp directory
        sample_execution.worktree.path = tmpdir
        tmppath = Path(tmpdir)
        src_path = tmppath / "src"
        src_path.mkdir()

        # Mark execution as successful
        sample_execution.return_code = 0
        sample_execution.status = "completed"

        with patch.object(
            engine.metrics_collector, "collect_metrics"
        ) as mock_collect:
            mock_collect.return_value = QualityMetrics(
                coverage_percentage=90.0,
                test_pass_rate=100.0,
                static_analysis_score=95.0,
            )

            report = engine.compare_implementations([sample_execution])

            assert report.task_id == sample_execution.assignment.task.id
            assert len(report.implementations) == 1
            assert "claude" in report.quality_scores
            assert report.recommendation != ""


def test_comparison_engine_compare_implementations_multiple(sample_task):
    """Test compare_implementations with multiple executions."""
    engine = ComparisonEngine()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple executions
        executions = []
        for agent in ["claude", "cursor", "copilot"]:
            assignment = AgentAssignment(
                task=sample_task,
                primary_agent=agent,
                secondary_agents=[],
                phase="implementation",
                justification=f"{agent} is good",
                confidence=0.9,
                task_type="backend_api",
                complexity="medium",
                tech_stack=["python"],
            )

            agent_path = Path(tmpdir) / agent
            agent_path.mkdir()
            src_path = agent_path / "src"
            src_path.mkdir()

            worktree = Worktree(
                path=str(agent_path),
                branch=f"agent/{agent}/test",
                agent=agent,
                task_id=sample_task.id,
                port=3000,
                status="active",
            )

            execution = AgentExecution(worktree=worktree, assignment=assignment)
            execution.return_code = 0
            execution.status = "completed"
            executions.append(execution)

        # Mock metrics collection
        def mock_collect(path):
            agent_name = Path(path).name
            scores = {"claude": 95.0, "cursor": 85.0, "copilot": 80.0}
            return QualityMetrics(
                coverage_percentage=scores.get(agent_name, 80.0),
                test_pass_rate=100.0,
                static_analysis_score=90.0,
            )

        with patch.object(
            engine.metrics_collector, "collect_metrics", side_effect=mock_collect
        ):
            report = engine.compare_implementations(executions)

            assert len(report.implementations) == 3
            assert len(report.quality_scores) == 3
            assert "claude" in report.quality_scores
            assert "cursor" in report.quality_scores
            assert "copilot" in report.quality_scores
            assert report.recommendation != ""
            assert 0.0 <= report.confidence <= 1.0


def test_comparison_engine_calculate_quality_score(sample_execution):
    """Test calculate_quality_score method."""
    engine = ComparisonEngine()

    with tempfile.TemporaryDirectory() as tmpdir:
        sample_execution.worktree.path = tmpdir
        tmppath = Path(tmpdir)
        src_path = tmppath / "src"
        src_path.mkdir()

        with patch.object(
            engine.metrics_collector, "collect_metrics"
        ) as mock_collect:
            mock_collect.return_value = QualityMetrics(
                coverage_percentage=85.0,
                test_pass_rate=100.0,
                static_analysis_score=90.0,
                cyclomatic_complexity=3.0,
            )

            score = engine.calculate_quality_score(sample_execution)

            assert isinstance(score, float)
            assert 0.0 <= score <= 100.0


def test_comparison_engine_recommend_merge(sample_task):
    """Test recommend_merge method."""
    engine = ComparisonEngine()

    report = ComparisonReport(
        task_id=sample_task.id,
        implementations=[],
        quality_scores={"claude": 95.0, "cursor": 80.0},
        test_results={"claude": True, "cursor": True},
    )

    recommendation = engine.recommend_merge(report)

    # Should recommend claude (highest score)
    assert recommendation == "claude"


def test_comparison_engine_recommend_merge_low_confidence(sample_task):
    """Test recommendation with low confidence."""
    engine = ComparisonEngine()

    report = ComparisonReport(
        task_id=sample_task.id,
        implementations=[],
        quality_scores={"claude": 60.0, "cursor": 58.0},
        test_results={"claude": True, "cursor": True},
    )

    recommendation, confidence = engine._recommend_merge(report)

    # Low scores and small gap should result in manual review
    assert recommendation == "manual_review"


def test_comparison_engine_recommend_merge_test_failure(sample_task):
    """Test recommendation when best implementation failed tests."""
    engine = ComparisonEngine()

    report = ComparisonReport(
        task_id=sample_task.id,
        implementations=[],
        quality_scores={"claude": 95.0, "cursor": 80.0},
        test_results={"claude": False, "cursor": True},
    )

    recommendation, confidence = engine._recommend_merge(report)

    # Test failure should trigger manual review
    assert recommendation == "manual_review"


def test_comparison_engine_recommend_merge_high_confidence(sample_task):
    """Test recommendation with high confidence."""
    engine = ComparisonEngine()

    report = ComparisonReport(
        task_id=sample_task.id,
        implementations=[],
        quality_scores={"claude": 95.0, "cursor": 70.0},
        test_results={"claude": True, "cursor": True},
    )

    recommendation, confidence = engine._recommend_merge(report)

    # High score, large gap, tests pass = high confidence
    assert recommendation == "claude"
    assert confidence > 0.7


def test_comparison_engine_generate_analysis(sample_task):
    """Test analysis generation."""
    engine = ComparisonEngine()

    metrics1 = QualityMetrics(
        coverage_percentage=90.0,
        cyclomatic_complexity=2.0,
        line_count=500,
        test_pass_rate=100.0,
    )

    metrics2 = QualityMetrics(
        coverage_percentage=85.0,
        cyclomatic_complexity=3.0,
        line_count=600,
        test_pass_rate=100.0,
    )

    report = ComparisonReport(
        task_id=sample_task.id,
        implementations=[],
        quality_scores={"claude": 92.0, "cursor": 87.0},
        test_results={"claude": True, "cursor": True},
        metrics={"claude": metrics1, "cursor": metrics2},
        recommendation="claude",
        confidence=0.85,
    )

    analysis = engine._generate_analysis(report)

    assert "Quality scores" in analysis
    assert "2/2 implementations passed" in analysis
    assert "Best test coverage" in analysis
    assert "Lowest complexity" in analysis
    assert "Most concise" in analysis
    assert "claude" in analysis


def test_comparison_engine_generate_analysis_manual_review(sample_task):
    """Test analysis when manual review recommended."""
    engine = ComparisonEngine()

    report = ComparisonReport(
        task_id=sample_task.id,
        implementations=[],
        quality_scores={"claude": 60.0, "cursor": 58.0},
        test_results={"claude": True, "cursor": True},
        recommendation="manual_review",
        confidence=0.40,
    )

    analysis = engine._generate_analysis(report)

    assert "Manual review recommended" in analysis


def test_comparison_engine_generate_diffs(sample_task):
    """Test diff generation between implementations."""
    engine = ComparisonEngine()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create two executions with different content
        executions = []
        for agent in ["claude", "cursor"]:
            agent_path = tmppath / agent
            agent_path.mkdir()
            src_path = agent_path / "src"
            src_path.mkdir()

            # Create a file with different content
            test_file = src_path / "test.py"
            test_file.write_text(f"# {agent} implementation\n")

            assignment = AgentAssignment(
                task=sample_task,
                primary_agent=agent,
                secondary_agents=[],
                phase="implementation",
                justification=f"{agent} is good",
                confidence=0.9,
                task_type="backend_api",
                complexity="medium",
                tech_stack=["python"],
            )

            worktree = Worktree(
                path=str(agent_path),
                branch=f"agent/{agent}/test",
                agent=agent,
                task_id=sample_task.id,
                port=3000,
                status="active",
            )

            execution = AgentExecution(worktree=worktree, assignment=assignment)
            executions.append(execution)

        with patch.object(
            engine.diff_analyzer, "get_changed_files", return_value=["src/test.py"]
        ):
            diffs = engine._generate_diffs(executions)

            assert len(diffs) == 1
            assert "claude_vs_cursor" in diffs
            assert "changed" in diffs["claude_vs_cursor"]


def test_comparison_engine_generate_diffs_single_execution(sample_execution):
    """Test diff generation with single execution."""
    engine = ComparisonEngine()

    diffs = engine._generate_diffs([sample_execution])

    # No diffs for single execution
    assert len(diffs) == 0
