<!-- Sync Impact Report -->
<!-- Version change: unknown → 1.0.0 -->
<!-- Modified principles: All principles updated -->
<!-- Added sections: All sections filled -->
<!-- Removed sections: None -->
<!-- Templates requiring updates: ✅ .specify/templates/plan-template.md -->
<!-- Follow-up TODOs: None -->

# QuantyFin AI Agent Constitution

## Core Principles

### I. Clean Architecture
MUST separate code into distinct layers: Domain (business logic), Application (use cases), Infrastructure (external systems), and Interfaces (API/CLI). All dependencies point inward toward the Domain layer.

### II. Multi-Agent AI System
MUST implement dual-agent workflow using both Google ADK and LangGraph/LangChain engines. Each agent MUST have a specific responsibility: Guard, Embedding, Search, Retriever, Analyze, Aggregator, and Predict agents.

### III. Test-Driven Development (NON-NEGOTIABLE)
MUST follow TDD cycle: Write failing tests → Get approval → Implement functionality → Refactor. All features MUST have corresponding unit, integration, and e2e tests before implementation begins.

### IV. Explainable AI & Traceability
MUST provide source citations, document traceability, and explainable outputs for all AI-generated analysis and predictions. All responses MUST include references to source materials.

### V. Financial Data Integrity
MUST ensure accurate extraction and calculation of financial metrics (P/E, ROE/ROA, debt ratios, YoY/QoQ growth). All numerical data MUST be standardized and validated before processing.

## Security & Compliance

### Authentication & Authorization
MUST implement OAuth2/OIDC with JWT tokens and Role-Based Access Control (RBAC). Roles MUST include Admin and User levels with proper permission boundaries.

### Data Privacy
MUST protect sensitive financial data and personally identifiable information (PII). All data processing MUST comply with financial data protection regulations.

### Guardrails
MUST implement input/output validation to prevent prompt injection and enforce safety policies. The Guard Agent MUST validate all external inputs and AI outputs.

## Development Workflow

### Dual Engine Orchestration
MUST support configurable runtime selection between Google ADK and LangGraph engines via environment variables. Agent engine selection MUST be transparent and easily switchable.

### Functional Programming Priority
MUST prefer pure functions with clear input/output over object-oriented patterns. Classes MUST only be used for external system connectors and interfaces. All business logic MUST be implemented as pure functions.

### Documentation Standards
MUST maintain comprehensive documentation including API specifications, data models, and quickstart guides. All features MUST include user scenarios and acceptance criteria.

## Governance

### Amendment Process
Constitutional amendments MUST be documented with version control following semantic versioning (MAJOR.MINOR.PATCH). All changes MUST pass compliance review and be communicated to stakeholders.

### Compliance Review
MUST verify compliance with this constitution during code reviews, testing, and deployment. Any violations MUST be justified in complexity tracking with simpler alternatives considered.

### Quality Gates
MUST enforce code quality through automated testing, linting, and type checking. All pull requests MUST include tests, documentation updates, and constitutional compliance validation.

**Version**: 1.0.0 | **Ratified**: 2025-09-26 | **Last Amended**: 2025-09-26