# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI-Coding-Orchestrator** is a Python-based orchestration system that automates the coordination of multiple AI coding assistants (Claude, Copilot, Cursor, Gemini, Cline, Windsurf, etc.) within a git repository. The system intelligently assigns tasks to appropriate agents based on their strengths, generates tailored configuration files, manages parallel development workflows using git worktrees, and ensures quality through rigorous validation and testing.

## Core Architecture

The system follows a modular, phase-based architecture (see DEVELOPMENT_PLAN.md for full details):

### Key Components

1. **Plan Parser**: Parses DEVELOPMENT_PLAN.md files and extracts structured task information
   - Validates markdown structure against defined schemas
   - Extracts tasks with metadata (priority, complexity, dependencies, acceptance criteria)
   - Handles nested sections and hierarchical task structures

2. **Task Classifier**: Uses NLP to classify tasks and determine optimal agent assignments
   - Classifies by technical domain (backend, frontend, DevOps, testing, etc.)
   - Scores complexity and estimates effort
   - Detects technology stack requirements

3. **Agent Assignment Engine**: Assigns tasks to AI agents based on capability matching
   - Multi-factor scoring algorithm considering task type, agent strengths, and project context
   - Supports composite assignments (multiple agents for different phases)
   - Generates human-readable justifications for assignments

4. **Configuration Generator**: Creates agent-specific configuration files
   - Generates AGENTS.md (universal project documentation)
   - Creates agent-specific configs: CLAUDE.md, CURSOR.md/.cursorrules, COPILOT.md/.github/copilot-instructions.md, GEMINI.md, CLINE.md/.clinerules, WINDSURF.md/.windsurfrules
   - Uses Jinja2 templates with project-specific variable substitution

5. **Worktree Manager**: Manages git worktrees for parallel agent execution
   - Creates isolated worktrees with naming convention: `worktree-{agent}-{task-id}`
   - Manages environment isolation (env vars, ports, configs)
   - Handles cleanup and branch management

6. **Validation Framework**: Enforces quality through multiple safety gates
   - Test coverage analysis (minimum 80% required)
   - Static analysis integration (pylint, flake8, mypy for Python)
   - Security scanning (SAST, dependency vulnerabilities, secret detection)
   - Staging deployment validation

7. **Comparison Engine**: Compares parallel agent implementations
   - Code diff analysis and functional equivalence testing
   - Quality metrics comparison (complexity, maintainability, coverage)
   - Merge recommendation generation

## Agent Capability Matrix

The orchestrator understands the strengths and optimal use cases for each AI assistant:

- **Claude**: Large context (200K tokens), architectural planning, complex refactoring, legacy code analysis
- **Copilot**: Fast autocomplete, boilerplate generation, inline suggestions
- **Cursor**: Multi-file editing, Agent/Composer modes, repo-wide refactors
- **Gemini**: Cost-effective, DevOps/CLI workflows, Google Cloud integration
- **Cline**: Open-source, MCP integration, transparent Plan/Act modes, multi-model support
- **Windsurf**: Privacy-first, on-premises deployment, live preview

### Task-to-Agent Assignment Patterns

- Backend API development: Claude (architecture) + Cursor (implementation)
- Frontend components: Cursor (primary) + Copilot (boilerplate/styling)
- DevOps/Infrastructure: Gemini CLI + Claude (planning)
- Legacy refactoring: Claude (analysis) + Cursor (execution)
- MCP development: Cline (primary) + Claude (architecture)
- Full-stack features: Cursor (context) + Claude (architecture) + Copilot (speed)

## Development Principles

### 1. Documentation and Standards First
All AI-generated code must include thorough documentation and adhere to coding standards. Configuration files (AGENTS.md, etc.) provide consistent guidance across all AI tools.

### 2. Test-Driven Development
- Generate tests BEFORE implementation code
- Minimum 80% code coverage required
- Support multiple testing frameworks (pytest for Python, Jest for JavaScript, etc.)
- Convert acceptance criteria to executable tests

### 3. Iterative Development
Break complex features into small, testable chunks with continuous validation. No single task should exceed scope that can be validated in one iteration.

### 4. Human Oversight
Critical architectural decisions and security reviews require human expertise. AI handles implementation; humans handle strategy and validation.

### 5. Safety-First Approach
Multiple validation gates before production:
- Code review gate (minimum 2 approvals for production code)
- Testing gate (all tests pass, 80%+ coverage)
- Static analysis gate (zero critical errors)
- Security scanning gate (SAST, dependency checks, secret detection)
- Staging validation gate (deployment + smoke tests)

## Development Workflows

### Git Worktree Parallel Execution Pattern

The system uses git worktrees to run multiple AI agents in parallel:

```bash
# Create worktree for each agent
git worktree add ../worktree-claude-feature-1 -b agent/claude/feature-1
git worktree add ../worktree-cursor-feature-1 -b agent/cursor/feature-1

# Launch separate AI instances in each worktree
# Each implements the same specification independently
# Compare results and select best implementation
```

This exploits LLM stochastic variation to generate multiple solutions for comparison.

### Closing the Agentic Loop

AI agents should verify their own work through automated testing:
1. Generate code
2. Run tests automatically
3. Deploy to staging (if applicable)
4. Review logs and errors
5. Iterate until all validation checks pass

This transforms AI from suggestion engine to autonomous developer.

### Configuration File Hierarchy

```
AGENTS.md (Universal - shared by all agents)
├── CLAUDE.md (Claude-specific workflows, MCP servers, slash commands)
├── CURSOR.md/.cursorrules (Agent mode, Composer settings, file patterns)
├── COPILOT.md/.github/copilot-instructions.md (Autocomplete preferences)
├── GEMINI.md/.gemini/settings.json (CLI workflows, GCP integration)
├── CLINE.md/.clinerules (Plan/Act modes, MCP connections)
└── WINDSURF.md/.windsurfrules (Privacy settings, on-prem config)
```

All agent-specific configs import/reference AGENTS.md to maintain consistency.

## Code Style and Standards

### Python (Primary Implementation Language)
- Use type hints for all function signatures
- Follow PEP 8 style guidelines
- Leverage async/await for I/O operations
- Comprehensive docstrings (Google style)
- Minimum 85% unit test coverage

### Key Python Modules (Expected Structure)
```
ai_coding_orchestrator/
├── parser/
│   ├── plan_parser.py       # DEVELOPMENT_PLAN.md parsing
│   └── task_extractor.py    # Task extraction from plans
├── classifier/
│   ├── task_classifier.py   # NLP-based task classification
│   └── agent_assignment.py  # Agent assignment engine
├── config/
│   ├── generator.py         # Configuration file generation
│   └── templates/           # Jinja2 templates
├── worktree/
│   ├── manager.py           # Git worktree management
│   └── isolation.py         # Environment isolation
├── validation/
│   ├── test_validator.py    # Test coverage analysis
│   ├── static_analyzer.py   # Static analysis integration
│   └── security_scanner.py  # Security scanning
└── comparison/
    ├── diff_analyzer.py     # Code comparison
    └── merge_recommender.py # Merge decision system
```

## MCP (Model Context Protocol) Integration

The system leverages MCP for enhanced agent coordination:

- **MCP Server**: Orchestration system exposes MCP tools for agents
  - `get_project_context`: Retrieve project info
  - `get_task_status`: Check task progress
  - `submit_result`: Submit agent work results
  - `request_review`: Initiate human review

- **MCP Client**: Connects to external MCP servers for documentation, APIs, testing infrastructure

- **Supported Agents**: Cline, Claude Code, and Cursor all support MCP integration

## Quality Metrics

### Phase-Level Success Criteria
Before proceeding to next development phase:
- All deliverables completed and reviewed
- Unit test coverage ≥ 85%
- Integration tests passing
- Documentation updated
- Code review approved
- Performance benchmarks met
- Security scan passed

### Project-Level Success Criteria
- Successfully orchestrates 5+ AI agents simultaneously
- Handles 20+ concurrent worktrees
- Completes end-to-end orchestration < 30 minutes for medium task
- Test coverage ≥ 80% on all generated code
- Zero high-severity security vulnerabilities
- User satisfaction ≥ 4/5

## Common Development Tasks

### Running Tests (When Implemented)
```bash
# Run all tests with coverage
pytest --cov=ai_coding_orchestrator --cov-report=html

# Run specific test module
pytest tests/parser/test_plan_parser.py -v

# Run with type checking
mypy ai_coding_orchestrator/
```

### Static Analysis (When Implemented)
```bash
# Linting
pylint ai_coding_orchestrator/
flake8 ai_coding_orchestrator/

# Type checking
mypy ai_coding_orchestrator/

# Security scanning
bandit -r ai_coding_orchestrator/
```

### Configuration Generation (When Implemented)
```bash
# Generate all agent configs for a project
python -m ai_coding_orchestrator generate-configs --project-dir /path/to/project

# Generate specific agent config
python -m ai_coding_orchestrator generate-configs --agent claude --output CLAUDE.md
```

## Risk Awareness

### High-Priority Risks
1. **AI-Generated Security Vulnerabilities**: Mandatory security scanning and human review
2. **Non-Functional Code**: TDD enforcement and staging validation
3. **Git Worktree Conflicts**: Filesystem isolation and conflict detection
4. **Agent Hallucinations**: Acceptance criteria validation and multi-agent comparison
5. **Secret Exposure**: Pre-commit secret detection and audit logging
6. **Cost Overruns**: Token usage tracking and timeout enforcement

## Future Development

### Plugin Architecture
The system will support extensible plugins for:
- Adding new AI agents without core changes
- Custom validation rules
- Alternative configuration formats
- Integration with additional tools

### Adaptation and Learning
System will track agent performance and adapt:
- Historical success rates by task type
- Optimal agent assignment patterns
- Prompt template effectiveness
- Automated capability matrix updates

## License

Apache License 2.0 (see LICENSE file)
