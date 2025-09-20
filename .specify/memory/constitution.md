<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.1.0 (Minor version - added timezone and Pydantic requirements)
- Modified principles:
  - IV. Async-First Development (added timezone.utc requirement)
  - Code Quality Standards (added Pydantic field_validator requirement)
- Added sections: None
- Removed sections: None
- Templates requiring updates:
  ✅ .specify/templates/plan-template.md (Constitution Check section)
  ✅ .specify/templates/spec-template.md (scope/requirements alignment)
  ✅ .specify/templates/tasks-template.md (task categorization)
- Follow-up TODOs: None
-->

# QuantyFinAI Agent Constitution

## Core Principles

### I. Architecture-First Design
Hexagonal architecture with clean separation of concerns MUST be the foundation of all development. Domain layer contains business logic and entities, application layer handles use cases, infrastructure layer implements external services, and interface layer provides API endpoints. Repository pattern with abstract interfaces MUST be used for all database operations.

### II. Multi-Agent RAG Architecture
All financial analysis features MUST implement the 7-agent RAG architecture using LangGraph. The Guard Agent handles input validation and security, Embedding Agent processes documents and generates vectors, Retriever Agent transforms queries and retrieves data, Search Agent integrates external APIs, Analyze Agent performs financial analysis, Predict Agent handles ML forecasting, and Aggregator Agent orchestrates the workflow.

### III. Type Safety & Functional Programming
Strict type hints MUST be used throughout the codebase with mypy validation. Functional programming MUST be preferred over OOP for business logic, with OOP reserved only for external system connectors. All business logic functions MUST be pure functions with clear input/output and NO hidden state changes. Pydantic models MUST be used for data validation instead of generic dictionaries.

### IV. Async-First Development
All database operations and external API calls MUST use async/await patterns. NO blocking operations are permitted in async contexts. Connection pooling MUST be used for PostgreSQL connections. Redis caching MUST be implemented for performance optimization and rate limiting. All external API calls MUST implement proper timeout handling. All datetime operations MUST use timezone.utc for consistency.

### V. Vector Database Integration
PostgreSQL with pgvector extension MUST be used for all vector storage and similarity search operations. HNSW indexing MUST be implemented for efficient vector search. Vector embeddings MUST be processed in batches for performance optimization. Vector operations MUST follow the repository pattern with dedicated vector database adapters.

## Technical Standards

### Technology Stack Requirements
- **Backend**: Python 3.12+ with FastAPI framework
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache**: Redis for session management and rate limiting
- **Authentication**: Keycloak with JWT token management
- **Containerization**: Docker and Docker Compose
- **LLM Integration**: OpenAI, Anthropic, Google, Deepseek APIs

### Code Quality Standards
- **Formatting**: Black code formatter with 79-character line length
- **Imports**: isort with Black profile configuration
- **Linting**: flake8 for code quality enforcement
- **Type Checking**: mypy with strict settings, NO Any types allowed
- **Testing**: pytest with unit, integration, and e2e test coverage
- **Pydantic Validation**: Use `field_validator` instead of deprecated `validator` in Pydantic models

### File Organization
- **File Length Limit**: Maximum 500 lines of logic per file (test files excluded)
- **Naming Convention**: snake_case for all Python files and functions
- **Module Structure**: Clear separation between domain, application, infrastructure, and interface layers
- **Agent Organization**: Each agent MUST be in its own file under app/agents/

## Development Workflow

### Testing Requirements
- **Test-First Development**: TDD MUST be followed with Red-Green-Refactor cycle
- **Test Categories**: Separate unit, integration, and e2e tests with clear organization
- **Async Testing**: pytest-asyncio MUST be used for all async test cases
- **Coverage**: Minimum 80% test coverage required for all new features
- **Test Data**: factory-boy MUST be used for test data generation

### Code Review Process
- **Type Safety**: All PRs MUST pass mypy validation with strict settings
- **Error Handling**: Explicit error handling with specific exception types is required
- **Performance**: Database queries and API calls MUST be reviewed for efficiency
- **Security**: Input validation and authentication MUST be verified
- **Documentation**: All new features MUST include appropriate documentation

### Deployment Standards
- **Containerization**: All components MUST be containerized using Docker
- **Environment Management**: Environment-specific configurations MUST use pyproject.toml
- **Database Migrations**: Schema changes MUST include proper migration scripts
- **Health Checks**: All services MUST implement health check endpoints

## Governance

### Amendment Procedure
Constitution amendments require:
1. **Proposal**: Written proposal detailing changes and rationale
2. **Review**: Technical review by lead developers
3. **Approval**: Consensus approval from development team
4. **Documentation**: Update of all dependent templates and documentation
5. **Implementation**: Phased rollout with backward compatibility consideration

### Versioning Policy
- **Major Version (X.0.0)**: Backward incompatible changes, principle removals, or architectural redefinitions
- **Minor Version (X.Y.0)**: New principles or sections added, material guidance expansions
- **Patch Version (X.Y.Z)**: Clarifications, wording fixes, non-semantic refinements

### Compliance Review
- **Pre-Commit**: All code changes MUST pass constitutional compliance checks
- **Code Review**: PR reviews MUST verify constitutional adherence
- **Architecture Review**: Major design decisions MUST be evaluated against constitutional principles
- **Regular Audits**: Quarterly audits of codebase against constitutional requirements

### Enforcement
- **Automated Checks**: Pre-commit hooks MUST enforce formatting, linting, and type checking
- **Manual Review**: Technical leads MUST review architectural decisions for compliance
- **Documentation**: CLAUDE.md MUST be updated to reflect constitutional requirements
- **Training**: Team members MUST be trained on constitutional principles and practices

**Version**: 1.1.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20