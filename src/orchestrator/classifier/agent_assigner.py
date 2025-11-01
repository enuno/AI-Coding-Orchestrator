"""Agent assignment engine for task distribution."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from orchestrator.core.models import Task, TaskType, Complexity


class AgentAssigner:
    """Assigns AI agents to tasks based on capabilities and rules."""

    def __init__(self, agents_path: Optional[Path] = None) -> None:
        """Initialize the agent assigner.

        Args:
            agents_path: Optional path to agents.yaml
        """
        if agents_path is None:
            # Default to data directory
            agents_path = Path(__file__).parent.parent / "data" / "agents.yaml"

        with open(agents_path, "r", encoding="utf-8") as f:
            self.agents_config = yaml.safe_load(f)

        self.agents = self.agents_config["agents"]
        self.assignment_rules = self.agents_config["assignment_rules"]
        self.complexity_factors = self.agents_config["complexity_factors"]

    def assign_agent(
        self, task: Task, manual_override: Optional[str] = None
    ) -> Task:
        """Assign an agent to a task.

        Args:
            task: Task to assign
            manual_override: Optional manual agent selection

        Returns:
            Task with assigned_agent set
        """
        # Manual override takes precedence
        if manual_override:
            if self._validate_agent(manual_override):
                task.assigned_agent = manual_override
                return task
            else:
                raise ValueError(f"Invalid agent: {manual_override}")

        # Get agent assignment based on task type and complexity
        agent = self._determine_best_agent(task)
        task.assigned_agent = agent

        return task

    def _validate_agent(self, agent_name: str) -> bool:
        """Validate that an agent exists in the configuration.

        Args:
            agent_name: Name of the agent to validate

        Returns:
            True if agent is valid, False otherwise
        """
        return agent_name in self.agents

    def _determine_best_agent(self, task: Task) -> str:
        """Determine the best agent for a task using scoring algorithm.

        Args:
            task: Task to assign

        Returns:
            Name of the best agent
        """
        # Get assignment rules for this task type
        task_type_str = task.task_type.value
        rules = self.assignment_rules.get(task_type_str)

        if rules:
            # Use rule-based assignment
            primary = rules["primary"]
            secondary = rules.get("secondary", [])

            # Score primary and secondary agents
            scores = self._score_agents(task, [primary] + secondary)

            # Return highest scoring agent
            if scores:
                best_agent = max(scores.items(), key=lambda x: x[1])
                return best_agent[0]

        # Fallback: score all agents
        all_agents = list(self.agents.keys())
        scores = self._score_agents(task, all_agents)

        if scores:
            best_agent = max(scores.items(), key=lambda x: x[1])
            return best_agent[0]

        # Ultimate fallback: claude
        return "claude"

    def _score_agents(
        self, task: Task, candidate_agents: List[str]
    ) -> Dict[str, float]:
        """Score agents for a task based on multiple factors.

        Args:
            task: Task to score agents for
            candidate_agents: List of agent names to consider

        Returns:
            Dictionary mapping agent names to scores
        """
        scores: Dict[str, float] = {}

        for agent_name in candidate_agents:
            if agent_name not in self.agents:
                continue

            agent = self.agents[agent_name]
            score = 0.0

            # Factor 1: Task type match (highest weight)
            task_type_str = task.task_type.value
            optimal_tasks = agent.get("optimal_tasks", [])
            if task_type_str in optimal_tasks:
                score += 10.0

            # Factor 2: Complexity match
            complexity_score = self._score_complexity_match(task.complexity, agent)
            score += complexity_score

            # Factor 3: Tech stack match
            tech_score = self._score_tech_stack_match(task.tech_stack, agent)
            score += tech_score

            # Factor 4: Context window requirements
            context_score = self._score_context_window(task, agent)
            score += context_score

            # Factor 5: Cost efficiency (lower tier = slight bonus)
            cost_tier = agent.get("cost_tier", "premium")
            if cost_tier == "budget":
                score += 1.0
            elif cost_tier == "mid":
                score += 0.5

            scores[agent_name] = score

        return scores

    def _score_complexity_match(self, complexity: Complexity, agent: dict) -> float:
        """Score how well an agent matches task complexity.

        Args:
            complexity: Task complexity level
            agent: Agent configuration

        Returns:
            Complexity match score
        """
        score = 0.0

        # Get complexity factors from global config
        if complexity == Complexity.SIMPLE:
            # Fast agents (Copilot) get bonus for simple tasks
            if "autocomplete_speed" in agent.get("strengths", []):
                score += 3.0
            if "boilerplate_generation" in agent.get("strengths", []):
                score += 2.0

        elif complexity == Complexity.COMPLEX:
            # High-capability agents (Claude, Cursor) get bonus for complex tasks
            if "architectural_planning" in agent.get("strengths", []):
                score += 5.0
            if "complex_refactoring" in agent.get("strengths", []):
                score += 4.0
            if "legacy_code_understanding" in agent.get("strengths", []):
                score += 3.0

        else:  # MEDIUM
            # Most agents handle medium tasks well
            score += 2.0

        return score

    def _score_tech_stack_match(self, tech_stack: List[str], agent: dict) -> float:
        """Score tech stack compatibility.

        Args:
            tech_stack: List of technologies used in task
            agent: Agent configuration

        Returns:
            Tech stack match score
        """
        if not tech_stack:
            return 0.0

        supported_languages = agent.get("supported_languages", [])
        matches = sum(1 for tech in tech_stack if tech in supported_languages)

        return matches * 2.0

    def _score_context_window(self, task: Task, agent: dict) -> float:
        """Score context window suitability.

        Args:
            task: Task to evaluate
            agent: Agent configuration

        Returns:
            Context window score
        """
        context_window = agent.get("context_window", 0)

        # Large refactoring or multi-file tasks benefit from large context
        text_content = (
            task.description + " " + " ".join(task.key_activities)
        ).lower()

        needs_large_context = any(
            keyword in text_content
            for keyword in [
                "multi-file",
                "refactor",
                "architecture",
                "legacy",
                "comprehensive",
            ]
        )

        if needs_large_context and context_window >= 100000:
            return 3.0
        elif needs_large_context and context_window >= 50000:
            return 1.5
        elif not needs_large_context and context_window >= 8000:
            return 1.0

        return 0.0

    def assign_agents(
        self, tasks: List[Task], manual_overrides: Optional[Dict[str, str]] = None
    ) -> List[Task]:
        """Assign agents to multiple tasks.

        Args:
            tasks: List of tasks to assign
            manual_overrides: Optional dictionary mapping task IDs to agent names

        Returns:
            List of tasks with agents assigned
        """
        manual_overrides = manual_overrides or {}

        assigned_tasks = []
        for task in tasks:
            override = manual_overrides.get(task.id)
            assigned_task = self.assign_agent(task, manual_override=override)
            assigned_tasks.append(assigned_task)

        return assigned_tasks

    def get_assignment_summary(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """Get a summary of task assignments by agent.

        Args:
            tasks: List of tasks with assigned agents

        Returns:
            Dictionary mapping agent names to lists of task IDs
        """
        summary: Dict[str, List[str]] = {}

        for task in tasks:
            agent = task.assigned_agent or "unassigned"
            if agent not in summary:
                summary[agent] = []
            summary[agent].append(task.id)

        return summary
