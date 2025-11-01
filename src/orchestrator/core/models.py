"""Core data models for the orchestrator."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TaskType(Enum):
    """Types of development tasks."""

    BACKEND_API = "backend_api"
    FRONTEND_COMPONENT = "frontend_component"
    DEVOPS_INFRASTRUCTURE = "devops_infrastructure"
    TESTING = "testing"
    DATABASE_SCHEMA = "database_schema"
    DOCUMENTATION = "documentation"
    LEGACY_REFACTORING = "legacy_refactoring"
    MCP_DEVELOPMENT = "mcp_development"
    AUTHENTICATION_AUTHORIZATION = "authentication_authorization"
    UI_UX_DESIGN = "ui_ux_design"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_IMPLEMENTATION = "security_implementation"
    FULL_STACK_FEATURE = "full_stack_feature"
    MOBILE_DEVELOPMENT = "mobile_development"
    DATA_PROCESSING = "data_processing"
    UNKNOWN = "unknown"


class Complexity(Enum):
    """Task complexity levels."""

    SIMPLE = "simple"  # Score 1-3
    MEDIUM = "medium"  # Score 4-6
    COMPLEX = "complex"  # Score 7-10


@dataclass
class Task:
    """Represents a development task extracted from a plan."""

    id: str
    title: str
    description: str
    phase: str
    stage: str
    week_range: Optional[str] = None
    objective: str = ""
    key_activities: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)
    technical_implementation: Optional[str] = None
    task_type: TaskType = TaskType.UNKNOWN
    complexity: Complexity = Complexity.MEDIUM
    tech_stack: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_effort_days: float = 1.0

    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "phase": self.phase,
            "stage": self.stage,
            "week_range": self.week_range,
            "objective": self.objective,
            "key_activities": self.key_activities,
            "deliverables": self.deliverables,
            "validation_criteria": self.validation_criteria,
            "technical_implementation": self.technical_implementation,
            "task_type": self.task_type.value,
            "complexity": self.complexity.value,
            "tech_stack": self.tech_stack,
            "assigned_agent": self.assigned_agent,
            "dependencies": self.dependencies,
            "estimated_effort_days": self.estimated_effort_days,
        }


@dataclass
class Stage:
    """Represents a stage within a phase."""

    stage_number: str  # e.g., "1.1", "2.3"
    stage_name: str
    week_range: Optional[str] = None
    objective: str = ""
    key_activities: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)
    technical_implementation: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)


@dataclass
class Phase:
    """Represents a development phase."""

    phase_number: int
    phase_name: str
    description: str = ""
    week_range: Optional[str] = None
    stages: List[Stage] = field(default_factory=list)


@dataclass
class Plan:
    """Represents a complete development plan."""

    title: str
    executive_summary: Optional[str] = None
    core_principles: List[str] = field(default_factory=list)
    phases: List[Phase] = field(default_factory=list)
    quality_metrics: dict = field(default_factory=dict)
    risks: List[dict] = field(default_factory=list)

    def get_all_tasks(self) -> List[Task]:
        """Extract all tasks from all phases and stages."""
        tasks: List[Task] = []
        for phase in self.phases:
            for stage in phase.stages:
                tasks.extend(stage.tasks)
        return tasks

    def get_tasks_by_phase(self, phase_number: int) -> List[Task]:
        """Get all tasks for a specific phase."""
        tasks: List[Task] = []
        for phase in self.phases:
            if phase.phase_number == phase_number:
                for stage in phase.stages:
                    tasks.extend(stage.tasks)
        return tasks
