"""Tests for quality metrics collection."""

import tempfile
from pathlib import Path

import pytest

from orchestrator.comparison.metrics import (
    DiffAnalyzer,
    MetricsCollector,
    QualityMetrics,
)


def test_quality_metrics_creation():
    """Test QualityMetrics dataclass creation."""
    metrics = QualityMetrics(
        coverage_percentage=85.0,
        cyclomatic_complexity=3.5,
        line_count=1000,
        file_count=10,
        test_pass_rate=100.0,
        static_analysis_score=95.0,
        issues_count=2,
        critical_issues=0,
    )

    assert metrics.coverage_percentage == 85.0
    assert metrics.cyclomatic_complexity == 3.5
    assert metrics.line_count == 1000
    assert metrics.file_count == 10
    assert metrics.test_pass_rate == 100.0
    assert metrics.static_analysis_score == 95.0
    assert metrics.issues_count == 2
    assert metrics.critical_issues == 0


def test_quality_metrics_overall_score():
    """Test overall quality score calculation."""
    # Perfect metrics
    metrics = QualityMetrics(
        coverage_percentage=100.0,
        cyclomatic_complexity=1.0,
        test_pass_rate=100.0,
        static_analysis_score=100.0,
        critical_issues=0,
    )

    score = metrics.overall_score
    assert 95.0 <= score <= 100.0  # Should be very high

    # Poor metrics
    poor_metrics = QualityMetrics(
        coverage_percentage=20.0,
        cyclomatic_complexity=15.0,
        test_pass_rate=50.0,
        static_analysis_score=60.0,
        critical_issues=5,
    )

    poor_score = poor_metrics.overall_score
    assert poor_score < 50.0  # Should be low


def test_quality_metrics_overall_score_weighted():
    """Test that coverage and test pass rate have higher weights."""
    # High coverage and test pass rate, low everything else
    high_testing = QualityMetrics(
        coverage_percentage=100.0,
        test_pass_rate=100.0,
        cyclomatic_complexity=20.0,
        static_analysis_score=50.0,
        critical_issues=3,
    )

    # Low coverage and test pass rate, high everything else
    low_testing = QualityMetrics(
        coverage_percentage=20.0,
        test_pass_rate=50.0,
        cyclomatic_complexity=1.0,
        static_analysis_score=100.0,
        critical_issues=0,
    )

    # High testing score should be higher despite worse other metrics
    assert high_testing.overall_score > low_testing.overall_score


def test_metrics_collector_init():
    """Test MetricsCollector initialization."""
    collector = MetricsCollector()
    assert collector is not None


def test_metrics_collector_count_lines():
    """Test line counting functionality."""
    collector = MetricsCollector()

    # Create temporary directory with Python files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        src_path = tmppath / "src"
        src_path.mkdir()

        # Create a Python file
        py_file = src_path / "test.py"
        py_file.write_text("# Line 1\n# Line 2\n# Line 3\n")

        line_count = collector._count_lines(tmppath)
        assert line_count == 3


def test_metrics_collector_count_lines_no_src():
    """Test line counting when src directory doesn't exist."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        line_count = collector._count_lines(tmppath)
        assert line_count == 0


def test_metrics_collector_count_files():
    """Test file counting functionality."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        src_path = tmppath / "src"
        src_path.mkdir()

        # Create multiple Python files
        (src_path / "file1.py").write_text("# File 1")
        (src_path / "file2.py").write_text("# File 2")
        subdir = src_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.py").write_text("# File 3")

        file_count = collector._count_files(tmppath)
        assert file_count == 3


def test_metrics_collector_get_coverage_no_file():
    """Test coverage extraction when no coverage file exists."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        coverage = collector._get_coverage(tmppath)
        assert coverage == 0.0


def test_metrics_collector_get_coverage_xml():
    """Test coverage extraction from coverage.xml."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a simple coverage.xml
        coverage_xml = tmppath / "coverage.xml"
        coverage_xml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<coverage line-rate="0.85" branch-rate="0.80">
</coverage>"""
        )

        coverage = collector._get_coverage(tmppath)
        assert coverage == 85.0


def test_metrics_collector_get_complexity():
    """Test complexity calculation."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        src_path = tmppath / "src"
        src_path.mkdir()

        # Create file with control flow statements
        py_file = src_path / "test.py"
        py_file.write_text(
            """
def test():
    if x > 0:
        for i in range(10):
            while True:
                pass
    elif x < 0:
        pass
"""
        )

        complexity = collector._get_complexity(tmppath)
        assert complexity > 0.0


def test_metrics_collector_get_complexity_no_src():
    """Test complexity when src directory doesn't exist."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        complexity = collector._get_complexity(tmppath)
        assert complexity == 0.0


def test_metrics_collector_get_static_analysis():
    """Test static analysis results."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        score, issues, critical = collector._get_static_analysis(tmppath)

        # Default implementation returns perfect score
        assert score == 100.0
        assert issues == 0
        assert critical == 0


def test_metrics_collector_get_test_pass_rate():
    """Test test pass rate retrieval."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        pass_rate = collector._get_test_pass_rate(tmppath)

        # Default implementation returns 100%
        assert pass_rate == 100.0


def test_metrics_collector_collect_metrics():
    """Test full metrics collection."""
    collector = MetricsCollector()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        src_path = tmppath / "src"
        src_path.mkdir()

        # Create Python files
        (src_path / "file1.py").write_text("# Line 1\n# Line 2\n")
        (src_path / "file2.py").write_text("# Line 1\n")

        metrics = collector.collect_metrics(tmppath)

        assert isinstance(metrics, QualityMetrics)
        assert metrics.line_count == 3
        assert metrics.file_count == 2
        assert metrics.coverage_percentage == 0.0  # No coverage file
        assert metrics.test_pass_rate == 100.0


def test_diff_analyzer_init():
    """Test DiffAnalyzer initialization."""
    analyzer = DiffAnalyzer()
    assert analyzer is not None


def test_diff_analyzer_get_diff_identical_files():
    """Test diff generation for identical files."""
    analyzer = DiffAnalyzer()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create two identical files
        path1 = tmppath / "path1"
        path2 = tmppath / "path2"
        path1.mkdir()
        path2.mkdir()

        file1 = path1 / "test.py"
        file2 = path2 / "test.py"
        content = "# Identical content\n"
        file1.write_text(content)
        file2.write_text(content)

        diff = analyzer.get_diff(path1, path2, "test.py")

        # Identical files should produce empty diff
        # (just headers, no + or - lines)
        assert "+" not in diff or "+++" in diff
        assert "-" not in diff or "---" in diff


def test_diff_analyzer_get_diff_different_files():
    """Test diff generation for different files."""
    analyzer = DiffAnalyzer()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        path1 = tmppath / "path1"
        path2 = tmppath / "path2"
        path1.mkdir()
        path2.mkdir()

        file1 = path1 / "test.py"
        file2 = path2 / "test.py"
        file1.write_text("# Version 1\n")
        file2.write_text("# Version 2\n")

        diff = analyzer.get_diff(path1, path2, "test.py")

        # Should contain diff markers
        assert "---" in diff
        assert "+++" in diff


def test_diff_analyzer_get_diff_missing_file():
    """Test diff when file is missing in one implementation."""
    analyzer = DiffAnalyzer()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        path1 = tmppath / "path1"
        path2 = tmppath / "path2"
        path1.mkdir()
        path2.mkdir()

        # Only create file in path1
        file1 = path1 / "test.py"
        file1.write_text("# Content\n")

        diff = analyzer.get_diff(path1, path2, "test.py")

        assert "File missing" in diff


def test_diff_analyzer_calculate_similarity_identical():
    """Test similarity calculation for identical files."""
    analyzer = DiffAnalyzer()

    diff = ""  # Empty diff = identical files
    similarity = analyzer.calculate_similarity(diff)

    assert similarity == 1.0


def test_diff_analyzer_calculate_similarity_different():
    """Test similarity calculation for different files."""
    analyzer = DiffAnalyzer()

    # Create a diff with many changes
    diff = """--- a/test.py
+++ b/test.py
""" + "\n".join(
        [f"+added line {i}" for i in range(100)]
    )

    similarity = analyzer.calculate_similarity(diff)

    # Many changes should result in low similarity
    assert similarity < 1.0


def test_diff_analyzer_calculate_similarity_error():
    """Test similarity when diff contains error."""
    analyzer = DiffAnalyzer()

    diff = "Error generating diff"
    similarity = analyzer.calculate_similarity(diff)

    assert similarity == 0.0


def test_diff_analyzer_calculate_similarity_missing_file():
    """Test similarity when file is missing."""
    analyzer = DiffAnalyzer()

    diff = "File missing in one or both implementations"
    similarity = analyzer.calculate_similarity(diff)

    assert similarity == 0.0
