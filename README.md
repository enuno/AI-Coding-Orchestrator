# AI-Coding-Orchestrator

A Python tool to orchestrate multiple AI coding assistants (Claude, Copilot, Cursor, Gemini, Cline, Windsurf) for multi-agent development workflows.

## Overview

AI-Coding-Orchestrator automates the coordination of multiple AI coding assistants within a git repository. It intelligently assigns tasks to appropriate agents based on their strengths, generates tailored configuration files, manages parallel development workflows using git worktrees, and ensures quality through rigorous validation and testing.

## Features

- **Intelligent Task Assignment**: Automatically assigns tasks to AI agents based on capabilities
- **Configuration Generation**: Creates agent-specific configs (CLAUDE.md, .cursorrules, etc.)
- **Git Worktree Management**: Parallel execution with isolated environments
- **Quality Validation**: Test coverage, static analysis, security scanning
- **MCP Integration**: Model Context Protocol support for enhanced coordination
- **Self-Validation Loop**: Agents verify their own work automatically

## Installation

### Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-coding-orchestrator.git
cd ai-coding-orchestrator

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell

# Verify installation
orchestrator --version
```

### Development Setup

```bash
# Install with dev dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Run type checking
mypy src/

# Run linting
flake8 src/
pylint src/
```

## Quick Start

```bash
# Initialize a new orchestration project
orchestrator init

# Parse a DEVELOPMENT_PLAN.md file
orchestrator parse DEVELOPMENT_PLAN.md

# Assign agents to tasks
orchestrator assign DEVELOPMENT_PLAN.md

# Generate agent configuration files
orchestrator generate --name "My Project" --tech-stack python --tech-stack react

# Full orchestration workflow
orchestrator orchestrate DEVELOPMENT_PLAN.md
```

## Project Structure

```
ai-coding-orchestrator/
├── src/orchestrator/           # Main package
│   ├── cli.py                  # Command-line interface
│   ├── parser/                 # Plan parsing
│   ├── classifier/             # Task classification
│   ├── config/                 # Config generation
│   ├── worktree/               # Git worktree management
│   ├── validation/             # Quality validation
│   ├── comparison/             # Implementation comparison
│   ├── execution/              # Agent execution
│   ├── review/                 # Human review workflows
│   ├── mcp/                    # MCP integration
│   ├── agentic/                # Self-validation loop
│   ├── plugins/                # Plugin system
│   ├── analytics/              # Performance analytics
│   ├── data/                   # Agent capability matrix, taxonomy
│   ├── templates/              # Jinja2 templates
│   └── schemas/                # JSON schemas
├── tests/                      # Test suite
├── docs/                       # Documentation
├── CLAUDE.md                   # Claude Code instructions
├── DEVELOPMENT_PLAN.md         # Comprehensive development plan
├── IMPLEMENTATION_ROADMAP.md   # Pragmatic 22-week roadmap
└── pyproject.toml             # Poetry configuration
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Instructions for Claude Code
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - Comprehensive 34-week development plan
- [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) - Pragmatic 22-week implementation roadmap
- [multi-agent-coding.md](multi-agent-coding.md) - Research on AI coding assistants

## Development Status

**Current Phase**: Phase 2 - Git Worktree Automation (Weeks 7-10)

**Phase 0 - Foundation (Weeks 1-2):** ✅ COMPLETE
- [x] Project structure created
- [x] Pre-commit hooks configured
- [x] GitHub Actions CI setup
- [x] Initial test structure
- [x] Agent capability matrix (agents.yaml)
- [x] Task classification taxonomy (task_taxonomy.yaml)
- [x] JSON schema for plan validation

**Phase 1 Week 3 - Markdown Parser:** ✅ COMPLETE
- [x] Core data models (Task, Stage, Phase, Plan)
- [x] Plan parser implementation (97.59% coverage)
- [x] Comprehensive test suite (20/20 tests passing)
- [x] Extracts: phases, stages, tasks, objectives, deliverables, validation criteria

**Phase 1 Week 4 - Task Classifier & Agent Assignment:** ✅ COMPLETE
- [x] Task classification by keyword matching (15 task types)
- [x] Complexity estimation algorithm (simple/medium/complex)
- [x] Agent assignment engine with multi-factor scoring
- [x] Manual override mechanism with validation
- [x] Tech stack detection
- [x] Comprehensive test suite (33/33 tests passing, 97%+ coverage)

**Phase 1 Week 5-6 - Configuration Generation & CLI:** ✅ COMPLETE
- [x] Jinja2-based configuration generator
- [x] Templates for all 6 agents (Claude, Cursor, Copilot, Gemini, Cline, Windsurf)
- [x] AGENTS.md universal coordination file
- [x] CLI commands: parse, assign, generate, orchestrate
- [x] End-to-end workflow integration
- [x] Comprehensive test suite (18/18 tests passing, 100% config coverage)

**Phase 1 Status:** ✅ COMPLETE - MVP working CLI tool ready!

**Phase 2 Week 7 - Git Worktree Automation:** ✅ COMPLETE
- [x] WorktreeManager class for parallel agent execution
- [x] Automated branch creation (agent/{agent-name}/{task-id})
- [x] Port allocation and environment isolation
- [x] Safety features (uncommitted changes detection)
- [x] Comprehensive test suite (14/14 tests passing, 87.95% coverage)
- [x] All 99 tests passing with 97.41% overall coverage

**Phase 2 Week 8 - Parallel Execution Coordinator:** ✅ COMPLETE
- [x] ExecutionCoordinator with async parallel execution
- [x] AgentExecution dataclass for state tracking
- [x] Configurable concurrency limits with Semaphore pattern
- [x] Timeout and failure handling
- [x] PromptGenerator with agent-specific instructions
- [x] Real-time progress monitoring and execution summaries
- [x] CLI integration: execute, cleanup, status commands
- [x] Comprehensive test suite (30/30 tests passing, execution module 96.75-100% coverage)
- [x] All 129 tests passing with 89.99% overall coverage

**Phase 2 Week 9 - Comparison Engine:** ✅ COMPLETE
- [x] QualityMetrics dataclass with weighted scoring (coverage 30%, test pass 25%, static analysis 20%, complexity 15%, critical issues 10%)
- [x] MetricsCollector for gathering coverage, complexity, line count, test results, static analysis
- [x] DiffAnalyzer for code comparison and similarity calculation
- [x] ComparisonEngine with multi-implementation analysis
- [x] ComparisonReport with best implementation selection
- [x] Merge recommendation logic with confidence scoring (3 factors: quality, gap, tests)
- [x] Minimum quality threshold (70.0) for automatic recommendations
- [x] Comprehensive test suite (41/41 tests passing, comparison module 87-99% coverage)
- [x] All 170 tests passing across the project

See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for detailed progress.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

## Code Quality

This project enforces strict code quality standards:

- **Type Checking**: mypy in strict mode
- **Formatting**: black (line length: 100)
- **Import Sorting**: isort (black-compatible)
- **Linting**: flake8, pylint
- **Security**: bandit
- **Test Coverage**: ≥85% required

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Research on multi-agent AI coding patterns: [multi-agent-coding.md](multi-agent-coding.md)
- Inspired by the need to coordinate multiple AI coding assistants effectively
- Built with modern Python tooling: Poetry, pytest, mypy, black

## Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Check existing documentation
- Review the roadmap and development plan

## Roadmap

See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for the detailed 22-week implementation plan.

**Upcoming Milestones:**
- **Phase 1** (Weeks 3-6): Core Engine MVP with working CLI
- **Phase 2** (Weeks 7-10): Git Worktree Automation for parallel execution
- **Phase 3** (Weeks 11-14): Quality & Validation with safety gates
- **Phase 4** (Weeks 15-17): MCP Integration and agentic loops
- **Phase 5** (Weeks 18-22): Polish, extensibility, and v1.0 release
