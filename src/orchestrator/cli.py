"""Command-line interface for AI Coding Orchestrator."""

import asyncio
import json
from pathlib import Path
from typing import List, Optional

import click

from orchestrator import __version__
from orchestrator.classifier.agent_assigner import AgentAssigner, AgentAssignment
from orchestrator.classifier.task_classifier import TaskClassifier
from orchestrator.config.generator import ConfigurationGenerator, ProjectContext
from orchestrator.execution.coordinator import ExecutionCoordinator
from orchestrator.execution.prompts import PromptGenerator
from orchestrator.parser.plan_parser import PlanParser
from orchestrator.worktree.manager import WorktreeManager


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """AI Coding Orchestrator - Coordinate multiple AI coding assistants.

    This tool helps you orchestrate multiple AI coding assistants (Claude, Copilot,
    Cursor, Gemini, Cline, Windsurf) for complex development projects.
    """
    pass


@cli.command()
def init() -> None:
    """Initialize a new orchestration project."""
    click.echo("Initializing AI Coding Orchestrator project...")
    click.echo("✓ Project initialized successfully!")


@cli.command()
@click.argument("plan_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for extracted tasks")
def parse(plan_file: str, output: Optional[str]) -> None:
    """Parse DEVELOPMENT_PLAN.md and extract tasks.

    Example:
        orchestrator parse DEVELOPMENT_PLAN.md
    """
    click.echo(f"Parsing {plan_file}...")

    parser = PlanParser()
    plan = parser.parse_file(plan_file)

    tasks = plan.get_all_tasks()

    click.echo(f"\n✓ Successfully parsed plan: {plan.title}")
    click.echo(f"  Phases: {len(plan.phases)}")
    click.echo(f"  Tasks:  {len(tasks)}")

    if output:
        # Save tasks to JSON file
        output_path = Path(output)
        tasks_data = [task.to_dict() for task in tasks]
        output_path.write_text(json.dumps(tasks_data, indent=2), encoding="utf-8")
        click.echo(f"\n✓ Tasks saved to {output}")


@cli.command()
@click.argument("plan_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for assignments")
def assign(plan_file: str, output: Optional[str]) -> None:
    """Classify tasks and assign agents from a plan.

    Example:
        orchestrator assign DEVELOPMENT_PLAN.md
    """
    click.echo(f"Processing {plan_file}...\n")

    # Parse the plan
    parser = PlanParser()
    plan = parser.parse_file(plan_file)
    tasks = plan.get_all_tasks()

    # Classify tasks
    click.echo("Classifying tasks...")
    classifier = TaskClassifier()
    classified_tasks = classifier.classify_tasks(tasks)

    # Assign agents
    click.echo("Assigning agents...")
    assigner = AgentAssigner()
    assigned_tasks = assigner.assign_agents(classified_tasks)

    # Display summary
    summary = assigner.get_assignment_summary(assigned_tasks)

    click.echo(f"\n✓ Assigned {len(assigned_tasks)} tasks to agents:")
    for agent, task_ids in summary.items():
        click.echo(f"  {agent}: {len(task_ids)} tasks")

    if output:
        # Save assignments to JSON file
        output_path = Path(output)
        assignments_data = [
            {
                "task_id": task.id,
                "title": task.title,
                "task_type": task.task_type.value,
                "complexity": task.complexity.value,
                "assigned_agent": task.assigned_agent,
                "tech_stack": task.tech_stack,
            }
            for task in assigned_tasks
        ]
        output_path.write_text(json.dumps(assignments_data, indent=2), encoding="utf-8")
        click.echo(f"\n✓ Assignments saved to {output}")


@cli.command()
@click.option("--name", "-n", required=True, help="Project name")
@click.option("--description", "-d", required=True, help="Project description")
@click.option("--tech-stack", "-t", multiple=True, help="Technology stack (can be repeated)")
@click.option("--language", "-l", default="python", help="Primary programming language")
@click.option("--output-dir", "-o", type=click.Path(), default=".", help="Output directory")
def generate(
    name: str,
    description: str,
    tech_stack: tuple,
    language: str,
    output_dir: str,
) -> None:
    """Generate agent configuration files.

    Example:
        orchestrator generate -n "My Project" -d "A cool project" -t python -t react
    """
    click.echo(f"Generating configurations for {name}...")

    context = ProjectContext(
        name=name,
        description=description,
        tech_stack=list(tech_stack),
        primary_language=language,
    )

    generator = ConfigurationGenerator()
    generated_files = generator.generate_all(context, Path(output_dir))

    click.echo(f"\n✓ Generated {len(generated_files)} configuration files:")
    for filename in generated_files.keys():
        click.echo(f"  {filename}")


@cli.command()
@click.argument("plan_file", type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), default=".", help="Output directory")
@click.option("--name", "-n", help="Project name (defaults to plan title)")
@click.option("--description", "-d", help="Project description")
def orchestrate(
    plan_file: str,
    output_dir: str,
    name: Optional[str],
    description: Optional[str],
) -> None:
    """Full orchestration: parse → classify → assign → generate.

    Example:
        orchestrator orchestrate DEVELOPMENT_PLAN.md
    """
    click.echo("Starting full orchestration workflow...\n")

    # Step 1: Parse the plan
    click.echo("1. Parsing plan...")
    parser = PlanParser()
    plan = parser.parse_file(plan_file)
    tasks = plan.get_all_tasks()
    click.echo(f"   ✓ Parsed {len(tasks)} tasks from {plan.title}")

    # Step 2: Classify tasks
    click.echo("\n2. Classifying tasks...")
    classifier = TaskClassifier()
    classified_tasks = classifier.classify_tasks(tasks)
    click.echo(f"   ✓ Classified {len(classified_tasks)} tasks")

    # Step 3: Assign agents
    click.echo("\n3. Assigning agents...")
    assigner = AgentAssigner()
    assigned_tasks = assigner.assign_agents(classified_tasks)
    summary = assigner.get_assignment_summary(assigned_tasks)

    click.echo("   ✓ Agent assignments:")
    for agent, task_ids in summary.items():
        click.echo(f"     {agent}: {len(task_ids)} tasks")

    # Step 4: Generate configurations
    click.echo("\n4. Generating configurations...")

    # Detect tech stack from tasks
    tech_stack_set = set()
    for task in assigned_tasks:
        tech_stack_set.update(task.tech_stack)

    context = ProjectContext(
        name=name or plan.title,
        description=description or plan.executive_summary or "AI-orchestrated project",
        tech_stack=sorted(list(tech_stack_set)),
    )

    # Build assignments dict for AGENTS.md
    assignments_dict = {}
    for task_type_name in set(task.task_type.value for task in assigned_tasks):
        tasks_of_type = [t for t in assigned_tasks if t.task_type.value == task_type_name]
        if tasks_of_type:
            primary_agent = tasks_of_type[0].assigned_agent
            assignments_dict[task_type_name] = {
                "primary": primary_agent,
                "secondary": [],
                "reasoning": f"Assigned based on task type and agent capabilities",
            }

    generator = ConfigurationGenerator()
    generated_files = generator.generate_all(context, Path(output_dir), assignments_dict)

    click.echo(f"   ✓ Generated {len(generated_files)} configuration files")

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("✓ Orchestration complete!")
    click.echo("=" * 60)
    click.echo(f"\nPlan: {plan.title}")
    click.echo(f"Tasks: {len(assigned_tasks)}")
    click.echo(f"Configurations: {len(generated_files)}")
    click.echo(f"\nGenerated files in {output_dir}:")
    for filename in generated_files.keys():
        click.echo(f"  - {filename}")


@cli.command()
@click.argument("plan_file", type=click.Path(exists=True))
@click.option("--max-concurrent", "-c", default=5, help="Maximum concurrent executions")
@click.option("--timeout", "-t", default=3600, help="Timeout per task in seconds")
@click.option("--repo-path", "-r", type=click.Path(exists=True), default=".", help="Repository path")
def execute(
    plan_file: str,
    max_concurrent: int,
    timeout: int,
    repo_path: str,
) -> None:
    """Execute tasks by creating worktrees and running agents in parallel.

    Example:
        orchestrator execute DEVELOPMENT_PLAN.md --max-concurrent 3
    """
    click.echo("Starting task execution workflow...\n")

    # Step 1: Parse and prepare tasks
    click.echo("1. Parsing and preparing tasks...")
    parser = PlanParser()
    plan = parser.parse_file(plan_file)
    tasks = plan.get_all_tasks()

    # Classify and assign
    classifier = TaskClassifier()
    classified_tasks = classifier.classify_tasks(tasks)

    assigner = AgentAssigner()
    assigned_tasks = assigner.assign_agents(classified_tasks)

    click.echo(f"   ✓ Prepared {len(assigned_tasks)} tasks for execution")

    # Step 2: Create worktrees
    click.echo("\n2. Creating worktrees...")
    manager = WorktreeManager(repo_path=Path(repo_path))

    worktrees = {}
    assignments = []

    for task in assigned_tasks:
        if not task.assigned_agent:
            continue

        worktree = manager.create_worktree(
            agent=task.assigned_agent,
            task_id=task.id,
        )
        worktrees[task.id] = worktree

        # Create AgentAssignment for execution
        assignment = AgentAssignment(
            task=task,
            primary_agent=task.assigned_agent,
            secondary_agents=[],
            phase="implementation",
            justification=f"Assigned to {task.assigned_agent} based on task type and complexity",
            confidence=0.9,
            task_type=task.task_type.value,
            complexity=task.complexity.value,
            tech_stack=task.tech_stack,
        )
        assignments.append(assignment)

    click.echo(f"   ✓ Created {len(worktrees)} worktrees")

    # Step 3: Generate prompts
    click.echo("\n3. Generating agent prompts...")
    prompt_gen = PromptGenerator()
    worktree_paths = {task_id: wt.path for task_id, wt in worktrees.items()}
    prompts = prompt_gen.generate_batch_prompts(assignments, worktree_paths)

    click.echo(f"   ✓ Generated {len(prompts)} prompts")

    # Step 4: Execute in parallel
    click.echo(f"\n4. Executing tasks (max {max_concurrent} concurrent)...")

    async def run_execution():
        coordinator = ExecutionCoordinator(max_concurrent=max_concurrent)
        executions = await coordinator.execute_parallel(assignments, worktrees)
        return coordinator, executions

    coordinator, executions = asyncio.run(run_execution())

    # Step 5: Display results
    click.echo("\n5. Execution results:")
    summary = coordinator.get_summary()

    click.echo(f"\n   Total: {summary['total']}")
    click.echo(f"   ✓ Completed: {summary['completed']}")
    click.echo(f"   ✗ Failed: {summary['failed']}")
    click.echo(f"   ⏱ Timeout: {summary['timeout']}")
    click.echo(f"   ⏸ Cancelled: {summary['cancelled']}")

    # Show individual results
    click.echo("\n   Task details:")
    for execution in executions:
        status_icon = "✓" if execution.is_successful else "✗"
        click.echo(f"   {status_icon} {execution.assignment.task.id}: {execution.status.value}")
        if execution.duration:
            click.echo(f"      Duration: {execution.duration:.2f}s")

    # Cleanup suggestion
    click.echo("\n💡 Don't forget to clean up worktrees when done:")
    click.echo("   orchestrator cleanup")


@cli.command()
@click.option("--repo-path", "-r", type=click.Path(exists=True), default=".", help="Repository path")
def cleanup(repo_path: str) -> None:
    """Clean up all managed worktrees.

    Example:
        orchestrator cleanup
    """
    click.echo("Cleaning up worktrees...")

    manager = WorktreeManager(repo_path=Path(repo_path))
    worktrees = manager.list_worktrees()

    if not worktrees:
        click.echo("   No worktrees to clean up")
        return

    click.echo(f"   Found {len(worktrees)} worktrees")

    for worktree in worktrees:
        try:
            manager.delete_worktree(worktree.path)
            click.echo(f"   ✓ Removed {worktree.path}")
        except Exception as e:
            click.echo(f"   ✗ Failed to remove {worktree.path}: {e}")

    click.echo("\n✓ Cleanup complete")


@cli.command()
@click.option("--repo-path", "-r", type=click.Path(exists=True), default=".", help="Repository path")
def status(repo_path: str) -> None:
    """Show status of all managed worktrees.

    Example:
        orchestrator status
    """
    click.echo("Worktree status:\n")

    manager = WorktreeManager(repo_path=Path(repo_path))
    worktrees = manager.list_worktrees()

    if not worktrees:
        click.echo("   No active worktrees")
        return

    click.echo(f"   Total worktrees: {len(worktrees)}\n")

    for worktree in worktrees:
        click.echo(f"   {worktree.path}")
        click.echo(f"   ├─ Agent: {worktree.agent}")
        click.echo(f"   ├─ Task: {worktree.task_id}")
        click.echo(f"   ├─ Branch: {worktree.branch}")
        click.echo(f"   ├─ Status: {worktree.status}")
        click.echo(f"   └─ Port: {worktree.port}\n")


if __name__ == "__main__":
    cli()
