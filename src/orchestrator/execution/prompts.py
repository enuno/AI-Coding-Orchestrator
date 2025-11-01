"""Agent prompt generation for task execution."""

from typing import Dict, List

from orchestrator.classifier.agent_assigner import AgentAssignment
from orchestrator.core.models import Task


class PromptGenerator:
    """Generates standardized prompts for AI agents."""

    def generate_task_prompt(
        self, assignment: AgentAssignment, worktree_path: str
    ) -> str:
        """Generate a comprehensive task prompt for an agent.

        Args:
            assignment: The agent assignment with task details
            worktree_path: Path to the worktree for execution

        Returns:
            Formatted prompt string for the agent
        """
        task = assignment.task
        agent = assignment.primary_agent

        prompt = f"""# Task Assignment for {agent.title()}

## Task Overview
**Task ID:** {task.id}
**Title:** {task.title}
**Phase:** {task.phase}
**Stage:** {task.stage}

## Objective
{task.objective or task.description}

## Key Activities
"""

        if task.key_activities:
            for activity in task.key_activities:
                prompt += f"- {activity}\n"
        else:
            prompt += "- (No specific activities listed)\n"

        prompt += "\n## Deliverables\n"
        if task.deliverables:
            for deliverable in task.deliverables:
                prompt += f"- {deliverable}\n"
        else:
            prompt += "- (No specific deliverables listed)\n"

        prompt += "\n## Validation Criteria\n"
        if task.validation_criteria:
            for criterion in task.validation_criteria:
                prompt += f"- {criterion}\n"
        else:
            prompt += "- (No specific criteria listed)\n"

        # Add technical implementation if available
        if task.technical_implementation:
            prompt += f"\n## Technical Implementation\n```python\n{task.technical_implementation}\n```\n"

        # Add worktree information
        prompt += f"\n## Execution Environment\n"
        prompt += f"- Working Directory: `{worktree_path}`\n"
        prompt += f"- Branch: (to be created in worktree)\n"

        # Add assignment justification
        prompt += f"\n## Why You Were Assigned\n{assignment.justification}\n"

        # Add instructions
        prompt += f"\n## Instructions\n"
        prompt += self._get_agent_specific_instructions(agent)

        return prompt

    def _get_agent_specific_instructions(self, agent: str) -> str:
        """Get agent-specific execution instructions.

        Args:
            agent: The agent name

        Returns:
            Agent-specific instructions
        """
        agent_instructions = {
            "claude": """
1. Review the task objectives and validation criteria carefully
2. Implement the solution following best practices
3. Write comprehensive tests (minimum 85% coverage)
4. Add clear documentation and comments
5. Validate your work against the criteria before completing
6. Update any relevant documentation files
""",
            "cursor": """
1. Use Agent or Composer mode for complex multi-file changes
2. Leverage repository-wide context for consistency
3. Follow existing code patterns and conventions
4. Write tests alongside implementation
5. Use inline suggestions for boilerplate
6. Verify all changes with local testing
""",
            "copilot": """
1. Use autocomplete suggestions for faster development
2. Follow established code patterns in the repository
3. Write clear, self-documenting code
4. Add tests for new functionality
5. Review suggestions before accepting
6. Maintain consistency with existing codebase
""",
            "gemini": """
1. Review task requirements thoroughly
2. Implement solution with clear, maintainable code
3. Write comprehensive tests
4. Document your changes
5. Validate against acceptance criteria
6. Ensure compatibility with existing systems
""",
            "cline": """
1. Use Plan/Act mode for complex tasks
2. Review the plan before execution
3. Implement solution step-by-step
4. Run tests frequently during development
5. Document your approach and decisions
6. Verify completion against criteria
""",
            "windsurf": """
1. Review task requirements in Cascade mode
2. Implement solution with privacy-first approach
3. Test changes locally before committing
4. Document implementation details
5. Ensure no sensitive data exposure
6. Validate against acceptance criteria
""",
        }

        return agent_instructions.get(
            agent.lower(),
            """
1. Review the task objectives and validation criteria
2. Implement the solution following best practices
3. Write comprehensive tests
4. Add clear documentation
5. Validate your work before completing
""",
        )

    def generate_batch_prompts(
        self, assignments: List[AgentAssignment], worktree_paths: Dict[str, str]
    ) -> Dict[str, str]:
        """Generate prompts for multiple assignments.

        Args:
            assignments: List of agent assignments
            worktree_paths: Dictionary mapping task IDs to worktree paths

        Returns:
            Dictionary mapping task IDs to prompts
        """
        prompts = {}
        for assignment in assignments:
            worktree_path = worktree_paths.get(assignment.task.id, ".")
            prompts[assignment.task.id] = self.generate_task_prompt(assignment, worktree_path)
        return prompts

    def generate_context_prompt(self, task: Task, project_context: Dict) -> str:
        """Generate additional context prompt with project information.

        Args:
            task: The task to generate context for
            project_context: Dictionary with project information

        Returns:
            Context prompt string
        """
        context = "## Project Context\n"

        if "name" in project_context:
            context += f"**Project Name:** {project_context['name']}\n"

        if "description" in project_context:
            context += f"**Description:** {project_context['description']}\n"

        if "tech_stack" in project_context:
            tech_stack = ", ".join(project_context["tech_stack"])
            context += f"**Technology Stack:** {tech_stack}\n"

        if "coding_standards" in project_context:
            context += "\n### Coding Standards\n"
            for standard in project_context["coding_standards"]:
                context += f"- {standard}\n"

        if "test_requirements" in project_context:
            context += "\n### Testing Requirements\n"
            for req in project_context["test_requirements"]:
                context += f"- {req}\n"

        return context
