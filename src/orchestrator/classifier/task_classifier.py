"""Task classification and complexity estimation."""

from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

from orchestrator.core.models import Task, TaskType, Complexity


class TaskClassifier:
    """Classifier for determining task types and complexity."""

    def __init__(self, taxonomy_path: Optional[Path] = None) -> None:
        """Initialize the classifier.

        Args:
            taxonomy_path: Optional path to task_taxonomy.yaml
        """
        if taxonomy_path is None:
            # Default to data directory
            taxonomy_path = (
                Path(__file__).parent.parent / "data" / "task_taxonomy.yaml"
            )

        with open(taxonomy_path, "r", encoding="utf-8") as f:
            self.taxonomy = yaml.safe_load(f)

        # Build keyword index for fast lookup
        self._build_keyword_index()

    def _build_keyword_index(self) -> None:
        """Build an index of keywords to task types for efficient lookup."""
        self.keyword_index: Dict[str, List[str]] = {}

        for task_type, config in self.taxonomy["task_types"].items():
            for keyword in config.get("keywords", []):
                keyword_lower = keyword.lower()
                if keyword_lower not in self.keyword_index:
                    self.keyword_index[keyword_lower] = []
                self.keyword_index[keyword_lower].append(task_type)

    def classify_task(self, task: Task) -> Task:
        """Classify a task by determining its type and complexity.

        Args:
            task: Task to classify

        Returns:
            Task with task_type and complexity set
        """
        # Determine task type
        task.task_type = self._determine_task_type(task)

        # Estimate complexity
        task.complexity = self._estimate_complexity(task)

        # Detect technology stack
        task.tech_stack = self._detect_tech_stack(task)

        return task

    def _determine_task_type(self, task: Task) -> TaskType:
        """Determine the task type based on keywords.

        Args:
            task: Task to classify

        Returns:
            TaskType enum value
        """
        # Combine all text from task for keyword matching
        text_content = " ".join(
            [
                task.title,
                task.description,
                task.objective,
                " ".join(task.key_activities),
                " ".join(task.deliverables),
            ]
        ).lower()

        # Count matches for each task type
        task_type_scores: Dict[str, int] = {}

        for keyword, task_types in self.keyword_index.items():
            if keyword in text_content:
                for task_type in task_types:
                    task_type_scores[task_type] = task_type_scores.get(task_type, 0) + 1

        # Return the task type with the highest score
        if task_type_scores:
            best_match = max(task_type_scores.items(), key=lambda x: x[1])
            task_type_name = best_match[0]

            # Convert string to TaskType enum
            try:
                return TaskType[task_type_name.upper()]
            except KeyError:
                # If conversion fails, return UNKNOWN
                return TaskType.UNKNOWN

        return TaskType.UNKNOWN

    def _estimate_complexity(self, task: Task) -> Complexity:
        """Estimate task complexity based on indicators.

        Args:
            task: Task to estimate complexity for

        Returns:
            Complexity enum value
        """
        complexity_score = 0

        # Combine all text for complexity indicator matching
        text_content = " ".join(
            [
                task.title,
                task.description,
                task.objective,
                " ".join(task.key_activities),
                " ".join(task.deliverables),
                " ".join(task.validation_criteria),
            ]
        ).lower()

        # Get complexity estimation rules
        complexity_rules = self.taxonomy.get("complexity_estimation", {})

        # Check for simple indicators (subtract from score)
        simple_indicators = complexity_rules.get("simple", {}).get("indicators", [])
        simple_matches = sum(
            1 for indicator in simple_indicators if indicator.replace("_", " ") in text_content
        )

        # Check for medium indicators
        medium_indicators = complexity_rules.get("medium", {}).get("indicators", [])
        medium_matches = sum(
            1 for indicator in medium_indicators if indicator.replace("_", " ") in text_content
        )

        # Check for complex indicators (add to score)
        complex_indicators = complexity_rules.get("complex", {}).get("indicators", [])
        complex_matches = sum(
            1
            for indicator in complex_indicators
            if indicator.replace("_", " ") in text_content
        )

        # Also check task-type-specific complexity factors
        task_type_str = task.task_type.value if task.task_type != TaskType.UNKNOWN else None
        if task_type_str and task_type_str in self.taxonomy["task_types"]:
            complexity_factors = self.taxonomy["task_types"][task_type_str].get(
                "complexity_factors", []
            )
            factor_matches = sum(
                1
                for factor in complexity_factors
                if factor.replace("_", " ") in text_content
            )
            complexity_score += factor_matches

        # Calculate final score
        complexity_score += complex_matches * 2
        complexity_score += medium_matches
        complexity_score -= simple_matches

        # Additional heuristics
        # More deliverables = more complexity
        complexity_score += len(task.deliverables) // 3

        # More validation criteria = more complexity
        complexity_score += len(task.validation_criteria) // 3

        # Map score to complexity level
        if complexity_score <= 2:
            return Complexity.SIMPLE
        elif complexity_score <= 5:
            return Complexity.MEDIUM
        else:
            return Complexity.COMPLEX

    def _detect_tech_stack(self, task: Task) -> List[str]:
        """Detect technology stack from task content.

        Args:
            task: Task to analyze

        Returns:
            List of detected technologies
        """
        text_content = " ".join(
            [
                task.title,
                task.description,
                task.objective,
                " ".join(task.key_activities),
                " ".join(task.deliverables),
            ]
        ).lower()

        detected_techs: Set[str] = set()
        tech_keywords = self.taxonomy.get("tech_stack_keywords", {})

        for tech, config in tech_keywords.items():
            keywords = config.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_content:
                    detected_techs.add(tech)
                    break  # Only need one match per tech

        return sorted(list(detected_techs))

    def classify_tasks(self, tasks: List[Task]) -> List[Task]:
        """Classify multiple tasks.

        Args:
            tasks: List of tasks to classify

        Returns:
            List of classified tasks
        """
        return [self.classify_task(task) for task in tasks]
