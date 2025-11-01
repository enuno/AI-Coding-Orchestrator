"""Comparison engine for analyzing parallel agent implementations."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from orchestrator.comparison.metrics import DiffAnalyzer, MetricsCollector, QualityMetrics
from orchestrator.execution.coordinator import AgentExecution


@dataclass
class ComparisonReport:
    """Report comparing multiple agent implementations.

    Attributes:
        task_id: ID of the task that was implemented
        implementations: List of agent executions to compare
        quality_scores: Quality scores for each implementation (agent -> score)
        code_diffs: Code diffs between implementations
        test_results: Test results for each implementation
        recommendation: Which implementation to merge
        confidence: Confidence in the recommendation (0-1)
        metrics: Detailed metrics for each implementation
        analysis: Additional analysis and insights
    """

    task_id: str
    implementations: List[AgentExecution]
    quality_scores: Dict[str, float] = field(default_factory=dict)
    code_diffs: Dict[str, str] = field(default_factory=dict)
    test_results: Dict[str, bool] = field(default_factory=dict)
    recommendation: str = ""
    confidence: float = 0.0
    metrics: Dict[str, QualityMetrics] = field(default_factory=dict)
    analysis: str = ""

    def get_best_implementation(self) -> Optional[str]:
        """Get the agent name of the best implementation.

        Returns:
            Agent name with highest quality score, or None if no implementations
        """
        if not self.quality_scores:
            return None

        return max(self.quality_scores.items(), key=lambda x: x[1])[0]

    def get_summary(self) -> str:
        """Generate a summary of the comparison.

        Returns:
            Human-readable summary string
        """
        if not self.quality_scores:
            return "No implementations to compare"

        summary_lines = [
            f"Comparison Report for Task: {self.task_id}",
            f"Implementations: {len(self.implementations)}",
            "",
            "Quality Scores:",
        ]

        for agent, score in sorted(
            self.quality_scores.items(), key=lambda x: x[1], reverse=True
        ):
            summary_lines.append(f"  {agent}: {score:.2f}/100")

        summary_lines.extend(
            [
                "",
                f"Recommendation: {self.recommendation}",
                f"Confidence: {self.confidence:.2%}",
            ]
        )

        if self.analysis:
            summary_lines.extend(["", "Analysis:", self.analysis])

        return "\n".join(summary_lines)


class ComparisonEngine:
    """Engine for comparing multiple agent implementations of the same task."""

    def __init__(self) -> None:
        """Initialize the comparison engine."""
        self.metrics_collector = MetricsCollector()
        self.diff_analyzer = DiffAnalyzer()

    def compare_implementations(
        self, executions: List[AgentExecution]
    ) -> ComparisonReport:
        """Compare multiple agent implementations and generate a report.

        Args:
            executions: List of agent executions for the same task

        Returns:
            ComparisonReport with analysis and recommendations
        """
        if not executions:
            raise ValueError("No executions provided for comparison")

        # Get task ID from first execution
        task_id = executions[0].assignment.task.id

        # Verify all executions are for the same task
        if not all(ex.assignment.task.id == task_id for ex in executions):
            raise ValueError("All executions must be for the same task")

        report = ComparisonReport(task_id=task_id, implementations=executions)

        # Collect metrics for each implementation
        for execution in executions:
            agent = execution.assignment.primary_agent
            worktree_path = Path(execution.worktree.path)

            # Collect quality metrics
            metrics = self.metrics_collector.collect_metrics(worktree_path)
            report.metrics[agent] = metrics
            report.quality_scores[agent] = metrics.overall_score

            # Record test results
            report.test_results[agent] = execution.is_successful

        # Generate code diffs between implementations
        report.code_diffs = self._generate_diffs(executions)

        # Generate recommendation
        report.recommendation, report.confidence = self._recommend_merge(report)

        # Generate analysis
        report.analysis = self._generate_analysis(report)

        return report

    def calculate_quality_score(self, execution: AgentExecution) -> float:
        """Calculate quality score for a single execution.

        Args:
            execution: Agent execution to score

        Returns:
            Quality score (0-100)
        """
        worktree_path = Path(execution.worktree.path)
        metrics = self.metrics_collector.collect_metrics(worktree_path)
        return metrics.overall_score

    def recommend_merge(self, report: ComparisonReport) -> str:
        """Recommend which implementation to merge based on comparison.

        Args:
            report: Comparison report

        Returns:
            Agent name to merge, or "manual_review" if unclear
        """
        recommendation, _ = self._recommend_merge(report)
        return recommendation

    def _generate_diffs(self, executions: List[AgentExecution]) -> Dict[str, str]:
        """Generate code diffs between implementations.

        Args:
            executions: List of agent executions

        Returns:
            Dictionary of diff descriptions
        """
        diffs = {}

        if len(executions) < 2:
            return diffs

        # Compare each pair of implementations
        for i in range(len(executions)):
            for j in range(i + 1, len(executions)):
                agent1 = executions[i].assignment.primary_agent
                agent2 = executions[j].assignment.primary_agent
                path1 = Path(executions[i].worktree.path)
                path2 = Path(executions[j].worktree.path)

                # Get changed files from both implementations
                files1 = self.diff_analyzer.get_changed_files(path1)
                files2 = self.diff_analyzer.get_changed_files(path2)

                # Find common files
                common_files = set(files1) & set(files2)

                diff_summary = f"{agent1} vs {agent2}:\n"
                diff_summary += f"  {agent1} changed: {len(files1)} files\n"
                diff_summary += f"  {agent2} changed: {len(files2)} files\n"
                diff_summary += f"  Common files: {len(common_files)}\n"

                # Calculate similarity for common files
                similarities = []
                for file_path in common_files:
                    diff = self.diff_analyzer.get_diff(path1, path2, file_path)
                    similarity = self.diff_analyzer.calculate_similarity(diff)
                    similarities.append(similarity)

                if similarities:
                    avg_similarity = sum(similarities) / len(similarities)
                    diff_summary += f"  Average similarity: {avg_similarity:.2%}"

                diffs[f"{agent1}_vs_{agent2}"] = diff_summary

        return diffs

    def _recommend_merge(self, report: ComparisonReport) -> tuple[str, float]:
        """Generate merge recommendation based on comparison.

        Args:
            report: Comparison report

        Returns:
            Tuple of (recommendation, confidence)
        """
        if not report.quality_scores:
            return ("manual_review", 0.0)

        # Find best implementation by quality score
        best_agent = max(report.quality_scores.items(), key=lambda x: x[1])[0]
        best_score = report.quality_scores[best_agent]

        # Calculate score gap to second-best
        scores = sorted(report.quality_scores.values(), reverse=True)
        if len(scores) > 1:
            score_gap = scores[0] - scores[1]
        else:
            score_gap = 100.0  # Only one implementation

        # Calculate confidence based on:
        # 1. Absolute quality score (higher is better)
        # 2. Score gap (larger gap = more confident)
        # 3. Test success (must pass tests)
        confidence_factors = []

        # Factor 1: Absolute quality (weight 0.4)
        confidence_factors.append(best_score / 100.0 * 0.4)

        # Factor 2: Score gap (weight 0.3)
        # Normalize gap (0-30 points -> 0-1)
        normalized_gap = min(1.0, score_gap / 30.0)
        confidence_factors.append(normalized_gap * 0.3)

        # Factor 3: Test success (weight 0.3)
        if report.test_results.get(best_agent, False):
            confidence_factors.append(0.3)
        else:
            # Test failure significantly reduces confidence
            confidence_factors.append(-0.2)

        confidence = sum(confidence_factors)
        confidence = max(0.0, min(1.0, confidence))

        # Recommend manual review if confidence is low
        if confidence < 0.5:
            return ("manual_review", confidence)

        # Recommend manual review if best quality score is too low
        if best_score < 70.0:
            return ("manual_review", confidence)

        # Recommend manual review if best implementation failed tests
        if not report.test_results.get(best_agent, False):
            return ("manual_review", confidence)

        return (best_agent, confidence)

    def _generate_analysis(self, report: ComparisonReport) -> str:
        """Generate detailed analysis of implementations.

        Args:
            report: Comparison report

        Returns:
            Analysis text
        """
        analysis_lines = []

        # Quality score distribution
        if report.quality_scores:
            scores = list(report.quality_scores.values())
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)

            analysis_lines.append(
                f"Quality scores range from {min_score:.1f} to {max_score:.1f} "
                f"(average: {avg_score:.1f})"
            )

        # Test results summary
        passed = sum(1 for result in report.test_results.values() if result)
        total = len(report.test_results)
        if total > 0:
            analysis_lines.append(f"{passed}/{total} implementations passed all tests")

        # Detailed metrics insights
        if report.metrics:
            # Compare coverage
            coverages = {
                agent: metrics.coverage_percentage
                for agent, metrics in report.metrics.items()
            }
            if coverages:
                best_coverage_agent = max(coverages.items(), key=lambda x: x[1])[0]
                best_coverage = coverages[best_coverage_agent]
                analysis_lines.append(
                    f"Best test coverage: {best_coverage_agent} ({best_coverage:.1f}%)"
                )

            # Compare complexity
            complexities = {
                agent: metrics.cyclomatic_complexity
                for agent, metrics in report.metrics.items()
            }
            if complexities:
                lowest_complexity_agent = min(complexities.items(), key=lambda x: x[1])[0]
                lowest_complexity = complexities[lowest_complexity_agent]
                analysis_lines.append(
                    f"Lowest complexity: {lowest_complexity_agent} "
                    f"(avg {lowest_complexity:.2f})"
                )

            # Compare code size
            line_counts = {
                agent: metrics.line_count for agent, metrics in report.metrics.items()
            }
            if line_counts:
                most_concise_agent = min(line_counts.items(), key=lambda x: x[1])[0]
                concise_lines = line_counts[most_concise_agent]
                analysis_lines.append(
                    f"Most concise: {most_concise_agent} ({concise_lines} lines)"
                )

        # Recommendation rationale
        if report.recommendation != "manual_review":
            rationale = (
                f"Recommended {report.recommendation} based on highest overall quality score "
                f"({report.quality_scores.get(report.recommendation, 0):.1f}/100) "
                f"and {report.confidence:.0%} confidence"
            )
            analysis_lines.append(rationale)
        else:
            analysis_lines.append(
                "Manual review recommended due to low confidence or test failures"
            )

        return "\n".join(analysis_lines)
