"""Quality metrics collection for code comparison."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class QualityMetrics:
    """Quality metrics for an implementation.

    Attributes:
        coverage_percentage: Test coverage percentage (0-100)
        cyclomatic_complexity: Average cyclomatic complexity
        line_count: Total lines of code
        file_count: Number of files changed
        test_pass_rate: Percentage of tests passing (0-100)
        static_analysis_score: Static analysis quality score (0-100)
        issues_count: Number of linting/static analysis issues
        critical_issues: Number of critical issues
    """

    coverage_percentage: float = 0.0
    cyclomatic_complexity: float = 0.0
    line_count: int = 0
    file_count: int = 0
    test_pass_rate: float = 100.0
    static_analysis_score: float = 100.0
    issues_count: int = 0
    critical_issues: int = 0
    details: Dict[str, any] = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        """Calculate overall quality score (0-100).

        Weighted combination of all metrics.
        """
        # Weights for each metric
        weights = {
            "coverage": 0.30,  # 30% weight
            "test_pass_rate": 0.25,  # 25% weight
            "static_analysis": 0.20,  # 20% weight
            "complexity": 0.15,  # 15% weight (inverse)
            "critical_issues": 0.10,  # 10% weight (inverse)
        }

        # Normalize complexity (lower is better, max 20)
        complexity_score = max(0, 100 - (self.cyclomatic_complexity * 5))

        # Critical issues penalty (0 issues = 100 score)
        critical_score = max(0, 100 - (self.critical_issues * 10))

        score = (
            weights["coverage"] * self.coverage_percentage
            + weights["test_pass_rate"] * self.test_pass_rate
            + weights["static_analysis"] * self.static_analysis_score
            + weights["complexity"] * complexity_score
            + weights["critical_issues"] * critical_score
        )

        return min(100.0, max(0.0, score))


class MetricsCollector:
    """Collects quality metrics from a worktree."""

    def collect_metrics(self, worktree_path: Path) -> QualityMetrics:
        """Collect all quality metrics from a worktree.

        Args:
            worktree_path: Path to the worktree

        Returns:
            QualityMetrics object with collected metrics
        """
        metrics = QualityMetrics()

        # Collect basic code metrics
        metrics.line_count = self._count_lines(worktree_path)
        metrics.file_count = self._count_files(worktree_path)

        # Collect coverage if available
        metrics.coverage_percentage = self._get_coverage(worktree_path)

        # Collect complexity metrics
        metrics.cyclomatic_complexity = self._get_complexity(worktree_path)

        # Collect static analysis metrics
        (
            metrics.static_analysis_score,
            metrics.issues_count,
            metrics.critical_issues,
        ) = self._get_static_analysis(worktree_path)

        # Collect test results
        metrics.test_pass_rate = self._get_test_pass_rate(worktree_path)

        return metrics

    def _count_lines(self, worktree_path: Path) -> int:
        """Count total lines of code in Python files.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Total line count
        """
        total_lines = 0
        src_path = worktree_path / "src"

        if not src_path.exists():
            return 0

        for py_file in src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    total_lines += len(f.readlines())
            except Exception:
                continue

        return total_lines

    def _count_files(self, worktree_path: Path) -> int:
        """Count number of Python files.

        Args:
            worktree_path: Path to the worktree

        Returns:
            File count
        """
        src_path = worktree_path / "src"

        if not src_path.exists():
            return 0

        count = 0
        for py_file in src_path.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                count += 1

        return count

    def _get_coverage(self, worktree_path: Path) -> float:
        """Extract test coverage percentage from coverage files.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Coverage percentage (0-100)
        """
        # Try to find coverage.xml or .coverage files
        coverage_xml = worktree_path / "coverage.xml"
        if coverage_xml.exists():
            return self._parse_coverage_xml(coverage_xml)

        # Default to 0 if no coverage data found
        return 0.0

    def _parse_coverage_xml(self, coverage_file: Path) -> float:
        """Parse coverage.xml file.

        Args:
            coverage_file: Path to coverage.xml

        Returns:
            Coverage percentage
        """
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(coverage_file)
            root = tree.getroot()

            # Find coverage element with line-rate attribute
            coverage_elem = root.find(".")
            if coverage_elem is not None and "line-rate" in coverage_elem.attrib:
                line_rate = float(coverage_elem.attrib["line-rate"])
                return line_rate * 100.0

            return 0.0
        except Exception:
            return 0.0

    def _get_complexity(self, worktree_path: Path) -> float:
        """Calculate average cyclomatic complexity.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Average complexity score
        """
        # For now, use a simple heuristic based on file size
        # In production, would use radon or similar tools
        src_path = worktree_path / "src"

        if not src_path.exists():
            return 0.0

        complexities = []
        for py_file in src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Rough heuristic: count control flow statements
                    complexity = sum(
                        1
                        for line in lines
                        if any(
                            keyword in line
                            for keyword in ["if ", "for ", "while ", "except ", "elif "]
                        )
                    )
                    if complexity > 0:
                        complexities.append(complexity / max(1, len(lines) / 10))
            except Exception:
                continue

        return sum(complexities) / max(1, len(complexities)) if complexities else 1.0

    def _get_static_analysis(self, worktree_path: Path) -> tuple[float, int, int]:
        """Run static analysis and get score.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Tuple of (score, total_issues, critical_issues)
        """
        # In production, would run flake8, pylint, mypy
        # For now, return defaults
        return (100.0, 0, 0)

    def _get_test_pass_rate(self, worktree_path: Path) -> float:
        """Get test pass rate from test results.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Pass rate percentage (0-100)
        """
        # Try to find pytest results
        # For now, default to 100% (all tests passing)
        return 100.0


class DiffAnalyzer:
    """Analyzes git diffs between implementations."""

    def get_diff(self, path1: Path, path2: Path, file_path: str) -> str:
        """Get diff between two file versions.

        Args:
            path1: First worktree path
            path2: Second worktree path
            file_path: Relative file path to compare

        Returns:
            Diff string
        """
        file1 = path1 / file_path
        file2 = path2 / file_path

        if not file1.exists() or not file2.exists():
            return f"File missing in one or both implementations: {file_path}"

        try:
            import difflib

            with open(file1, "r", encoding="utf-8") as f1:
                lines1 = f1.readlines()
            with open(file2, "r", encoding="utf-8") as f2:
                lines2 = f2.readlines()

            diff = difflib.unified_diff(
                lines1, lines2, fromfile=str(file1), tofile=str(file2), lineterm=""
            )

            return "\n".join(diff)
        except Exception as e:
            return f"Error generating diff: {e}"

    def get_changed_files(self, worktree_path: Path, base_branch: str = "main") -> List[str]:
        """Get list of files changed in worktree compared to base branch.

        Args:
            worktree_path: Path to the worktree
            base_branch: Base branch to compare against

        Returns:
            List of changed file paths
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", base_branch],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split("\n") if line.strip()]

            return []
        except Exception:
            return []

    def calculate_similarity(self, diff: str) -> float:
        """Calculate similarity score between two files based on diff.

        Args:
            diff: Unified diff string

        Returns:
            Similarity score (0.0 = completely different, 1.0 = identical)
        """
        if "File missing" in diff or "Error" in diff:
            return 0.0

        if not diff:
            return 1.0  # Empty diff means identical files

        # Count added and removed lines
        lines = diff.split("\n")
        added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))

        # Total changed lines
        total_changes = added + removed

        if total_changes == 0:
            return 1.0  # Identical files

        # Similarity is inverse of change rate (rough heuristic)
        # More changes = less similar
        similarity = 1.0 - min(1.0, total_changes / 1000.0)

        return similarity
