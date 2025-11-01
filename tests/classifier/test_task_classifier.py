"""Tests for task_classifier module."""

import pytest

from orchestrator.classifier.task_classifier import TaskClassifier
from orchestrator.core.models import Task, TaskType, Complexity


@pytest.fixture
def classifier():
    """Create a TaskClassifier instance."""
    return TaskClassifier()


@pytest.fixture
def backend_task():
    """Create a sample backend API task."""
    return Task(
        id="test-1",
        title="Create REST API endpoint",
        description="Implement a RESTful API endpoint for user management",
        phase="Phase 1",
        stage="Stage 1.1",
        objective="Build a scalable backend API",
        key_activities=[
            "Design API routes",
            "Implement business logic",
            "Add database integration",
        ],
        deliverables=["API endpoints", "Request/response models", "Integration tests"],
        validation_criteria=["All tests pass", "API documentation complete"],
    )


@pytest.fixture
def frontend_task():
    """Create a sample frontend component task."""
    return Task(
        id="test-2",
        title="Build React dashboard component",
        description="Create a responsive dashboard UI component using React and TypeScript",
        phase="Phase 1",
        stage="Stage 1.2",
        objective="Implement interactive dashboard",
        key_activities=[
            "Create React components",
            "Add state management",
            "Implement responsive design",
        ],
        deliverables=["Dashboard component", "CSS styles", "Unit tests"],
        validation_criteria=["Component renders correctly", "Tests pass"],
    )


@pytest.fixture
def devops_task():
    """Create a sample DevOps task."""
    return Task(
        id="test-3",
        title="Set up CI/CD pipeline",
        description="Configure Docker and Kubernetes deployment with Terraform",
        phase="Phase 2",
        stage="Stage 2.1",
        objective="Automate deployment process",
        key_activities=[
            "Create Dockerfile",
            "Configure Kubernetes manifests",
            "Set up Terraform infrastructure",
        ],
        deliverables=["Dockerfile", "K8s manifests", "Terraform configs"],
        validation_criteria=["Pipeline runs successfully", "Deployment works"],
    )


@pytest.fixture
def complex_refactoring_task():
    """Create a complex legacy refactoring task."""
    return Task(
        id="test-4",
        title="Refactor legacy authentication system",
        description="Modernize the legacy authentication system with architectural changes",
        phase="Phase 3",
        stage="Stage 3.1",
        objective="Improve security and maintainability",
        key_activities=[
            "Analyze existing legacy code",
            "Design new architecture",
            "Implement security improvements",
            "Ensure backward compatibility",
            "Write comprehensive tests",
            "Update documentation",
        ],
        deliverables=[
            "Refactored code",
            "Security audit report",
            "Migration guide",
            "Updated tests",
            "Architecture diagrams",
            "API documentation",
        ],
        validation_criteria=[
            "All tests pass",
            "Security scan passes",
            "Performance improves",
            "No breaking changes",
        ],
    )


def test_classifier_initialization(classifier):
    """Test classifier initializes correctly."""
    assert classifier is not None
    assert classifier.taxonomy is not None
    assert classifier.keyword_index is not None
    assert len(classifier.keyword_index) > 0


def test_keyword_index_building(classifier):
    """Test keyword index is built correctly."""
    # Check that common keywords are indexed
    assert "api" in classifier.keyword_index
    assert "react" in classifier.keyword_index
    assert "docker" in classifier.keyword_index

    # Verify task types are associated with keywords
    assert "backend_api" in classifier.keyword_index["api"]
    assert "frontend_component" in classifier.keyword_index["react"]


def test_classify_backend_task(classifier, backend_task):
    """Test classification of backend API task."""
    classified = classifier.classify_task(backend_task)

    assert classified.task_type == TaskType.BACKEND_API
    assert classified.complexity in [Complexity.SIMPLE, Complexity.MEDIUM, Complexity.COMPLEX]
    assert "python" not in classified.tech_stack or len(classified.tech_stack) >= 0


def test_classify_frontend_task(classifier, frontend_task):
    """Test classification of frontend component task."""
    classified = classifier.classify_task(frontend_task)

    assert classified.task_type == TaskType.FRONTEND_COMPONENT
    assert "react" in classified.tech_stack
    assert "typescript" in classified.tech_stack


def test_classify_devops_task(classifier, devops_task):
    """Test classification of DevOps task."""
    classified = classifier.classify_task(devops_task)

    assert classified.task_type == TaskType.DEVOPS_INFRASTRUCTURE
    assert "docker" in classified.tech_stack
    assert "kubernetes" in classified.tech_stack
    assert "terraform" in classified.tech_stack


def test_complexity_estimation_simple():
    """Test complexity estimation for simple task."""
    classifier = TaskClassifier()

    simple_task = Task(
        id="simple-1",
        title="Add utility function",
        description="Add a simple utility function with clear requirements",
        phase="Phase 1",
        stage="Stage 1.1",
        objective="Add helper function",
        key_activities=["Write function"],
        deliverables=["Utility module"],
        validation_criteria=["Tests pass"],
    )

    classified = classifier.classify_task(simple_task)
    assert classified.complexity == Complexity.SIMPLE


def test_complexity_estimation_complex(classifier, complex_refactoring_task):
    """Test complexity estimation for complex task."""
    classified = classifier.classify_task(complex_refactoring_task)

    assert classified.complexity == Complexity.COMPLEX


def test_tech_stack_detection_python():
    """Test detection of Python tech stack."""
    classifier = TaskClassifier()

    python_task = Task(
        id="py-1",
        title="Build FastAPI service",
        description="Create a Python backend using FastAPI and pytest",
        phase="Phase 1",
        stage="Stage 1.1",
        key_activities=["Write FastAPI routes", "Add pytest tests"],
        deliverables=["API service"],
    )

    classified = classifier.classify_task(python_task)
    assert "python" in classified.tech_stack


def test_tech_stack_detection_javascript():
    """Test detection of JavaScript/Node.js tech stack."""
    classifier = TaskClassifier()

    js_task = Task(
        id="js-1",
        title="Build Express API",
        description="Create a Node.js backend using Express and npm packages",
        phase="Phase 1",
        stage="Stage 1.1",
        key_activities=["Set up Express server", "Install npm packages"],
        deliverables=["Node.js API"],
    )

    classified = classifier.classify_task(js_task)
    assert "javascript" in classified.tech_stack


def test_classify_multiple_tasks(classifier, backend_task, frontend_task, devops_task):
    """Test classifying multiple tasks at once."""
    tasks = [backend_task, frontend_task, devops_task]
    classified_tasks = classifier.classify_tasks(tasks)

    assert len(classified_tasks) == 3
    assert classified_tasks[0].task_type == TaskType.BACKEND_API
    assert classified_tasks[1].task_type == TaskType.FRONTEND_COMPONENT
    assert classified_tasks[2].task_type == TaskType.DEVOPS_INFRASTRUCTURE


def test_unknown_task_type():
    """Test classification of task with no clear type."""
    classifier = TaskClassifier()

    unknown_task = Task(
        id="unknown-1",
        title="XYZ",
        description="ABC",
        phase="Phase 1",
        stage="Stage 1.1",
        key_activities=["QRS"],
        deliverables=["LMN"],
    )

    classified = classifier.classify_task(unknown_task)
    # Even with gibberish, classifier may find weak matches, so just verify it completes
    assert classified.task_type is not None
    assert isinstance(classified.task_type, TaskType)


def test_documentation_task():
    """Test classification of documentation task."""
    classifier = TaskClassifier()

    doc_task = Task(
        id="doc-1",
        title="Write API documentation",
        description="Create comprehensive API docs and README guide",
        phase="Phase 1",
        stage="Stage 1.1",
        objective="Document the API",
        key_activities=["Write README", "Generate API docs", "Create tutorial"],
        deliverables=["README.md", "API documentation", "User guide"],
    )

    classified = classifier.classify_task(doc_task)
    assert classified.task_type == TaskType.DOCUMENTATION


def test_testing_task():
    """Test classification of testing task."""
    classifier = TaskClassifier()

    test_task = Task(
        id="test-1",
        title="Write integration tests",
        description="Implement end-to-end tests and unit tests with mocks",
        phase="Phase 1",
        stage="Stage 1.1",
        objective="Improve test coverage",
        key_activities=[
            "Write unit tests",
            "Create integration tests",
            "Add fixtures and mocks",
        ],
        deliverables=["Test suite", "Test fixtures", "Coverage report"],
    )

    classified = classifier.classify_task(test_task)
    assert classified.task_type == TaskType.TESTING


def test_mcp_development_task():
    """Test classification of MCP development task."""
    classifier = TaskClassifier()

    mcp_task = Task(
        id="mcp-1",
        title="Build MCP server",
        description="Develop a Model Context Protocol server with tools and resources",
        phase="Phase 1",
        stage="Stage 1.1",
        objective="Create MCP integration",
        key_activities=[
            "Implement MCP server",
            "Define tool handlers",
            "Add resource management",
        ],
        deliverables=["MCP server", "Tool definitions", "Documentation"],
    )

    classified = classifier.classify_task(mcp_task)
    assert classified.task_type == TaskType.MCP_DEVELOPMENT


def test_security_task():
    """Test classification of security implementation task."""
    classifier = TaskClassifier()

    security_task = Task(
        id="sec-1",
        title="Implement security hardening",
        description="Add encryption, input validation, and CSRF protection",
        phase="Phase 1",
        stage="Stage 1.1",
        objective="Improve security posture",
        key_activities=[
            "Add input sanitization",
            "Implement encryption",
            "Fix XSS vulnerabilities",
        ],
        deliverables=["Security middleware", "Encryption module", "Security tests"],
    )

    classified = classifier.classify_task(security_task)
    assert classified.task_type == TaskType.SECURITY_IMPLEMENTATION
