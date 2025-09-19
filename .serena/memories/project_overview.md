# QuantyFinAI Agent - Project Overview

## Project Purpose
AI-powered financial analysis and stock prediction system implementing a 7-agent RAG architecture using LangGraph for processing financial data, investing, stocks, and cryptocurrency analysis.

## Architecture
- **Hexagonal Architecture**: Ports and adapters pattern with clean separation of concerns
- **Multi-Agent RAG System**: 7 specialized agents (Guard, Embedding, Retriever, Search, Analyze, Predict, Aggregator)
- **Domain-Driven Design**: Core business logic separated from infrastructure concerns

## Tech Stack
- **Backend**: Python 3.12+ with FastAPI
- **AI/ML**: LangGraph, LangChain, OpenAI, Anthropic, Google, Deepseek APIs
- **Database**: PostgreSQL 16 with pgvector extension for vector search
- **Cache**: Redis for session management and rate limiting
- **Authentication**: Keycloak with JWT token management
- **Containerization**: Docker and Docker Compose
- **Testing**: pytest with unit, integration, and e2e tests

## Key Components
- **Database Layer**: PostgreSQL with pgvector, connection pooling, repository pattern
- **Authentication**: Keycloak integration, RBAC, JWT token management
- **Caching**: Redis-based session management, rate limiting, batch operations
- **Configuration**: Pydantic settings with environment-specific configs
- **Monitoring**: Health checks, structured logging, metrics

## Development Environment
- **Dependency Management**: Poetry with pyproject.toml
- **Code Quality**: Black, isort, flake8, mypy, pre-commit hooks
- **Testing Strategy**: TDD with comprehensive test coverage
- **Container Setup**: Multi-service Docker compose with dev profiles