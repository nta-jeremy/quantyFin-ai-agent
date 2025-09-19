# QuantyFinAI Agent Project Overview

## Project Purpose
QuantyFinAI Agent is an AI-powered financial analysis and stock prediction system implementing a 7-agent RAG architecture using LangGraph for processing financial data, investing, stocks, and cryptocurrency analysis.

## Tech Stack
- **Backend**: Python 3.12+ with FastAPI
- **Database**: PostgreSQL 16 with pgvector extension for vector search
- **Cache**: Redis for session management and rate limiting
- **Authentication**: Keycloak with JWT token management
- **Vector Search**: HNSW indexing for efficient similarity search
- **Containerization**: Docker and Docker Compose
- **LLM Integration**: OpenAI, Anthropic, Google, Deepseek APIs
- **Architecture**: Hexagonal architecture (ports and adapters pattern)

## Multi-Agent RAG System
The system implements a 7-agent architecture:
1. **Guard Agent**: Input validation and prompt injection protection
2. **Embedding Agent**: Document processing and vector embedding generation
3. **Retriever Agent**: Query transformation and data retrieval
4. **Search Agent**: External API integration and web search
5. **Analyze Agent**: Financial analysis and sentiment processing
6. **Predict Agent**: ML model predictions and forecasting
7. **Aggregator Agent**: Workflow orchestration and response synthesis

## Code Structure
```
app/
├── core/
│   ├── domain/           # Business logic, entities, service interfaces
│   │   ├── models.py     # Pydantic models and domain entities
│   │   └── services.py   # Domain service interfaces
│   └── application/      # Use cases and application services
│       ├── auth_service.py
│       ├── permission_service.py
│       └── session_service.py
├── infrastructure/       # External service implementations
│   ├── auth/            # Keycloak authentication system
│   │   ├── keycloak_adapter.py
│   │   ├── keycloak_auth.py
│   │   ├── keycloak_session.py
│   │   ├── keycloak_user_management.py
│   │   └── keycloak_role_management.py
│   ├── cache/           # Redis caching system
│   │   └── redis_adapter.py
│   ├── persistence/     # PostgreSQL and vector database adapters
│   │   ├── postgres_adapter.py
│   │   └── vector_db_adapter.py
│   └── api/             # External API integrations
├── interfaces/          # API endpoints and CLI interfaces
│   ├── api/
│   │   ├── v1/          # REST API v1 endpoints
│   │   │   ├── health.py
│   │   │   ├── hello.py
│   │   │   └── agent_routes.py
│   │   └── auth/        # Authentication endpoints
│   │       └── auth_routes.py
│   └── cli/             # Command-line interface
└── agents/              # LangGraph AI agent implementations
    ├── base_agent.py    # Base agent class
    ├── agent_state.py   # Agent state management
    ├── agent_types.py   # Agent type definitions
    ├── langgraph_workflow.py  # LangGraph workflow orchestration
    ├── guard_agent.py   # Input validation and security
    ├── embedding_agent.py  # Document processing and embeddings
    ├── retriever_agent.py   # Query transformation and retrieval
    ├── search_agent.py  # External API integration
    ├── analyze_agent.py # Financial analysis
    ├── predict_agent.py # ML predictions
    └── aggregator_agent.py  # Workflow orchestration
```

## Key Components
- **Domain Models**: Pydantic models for User, Company, StockData, FinancialMetrics, etc.
- **Authentication**: JWT-based with Keycloak integration
- **Database**: PostgreSQL with pgvector for vector embeddings
- **Caching**: Redis for performance optimization and rate limiting
- **API**: FastAPI with OpenAPI documentation
- **Testing**: pytest with unit, integration, and e2e tests

## Development Environment
- **Dependency Management**: Poetry (pyproject.toml)
- **Code Quality**: Black, isort, flake8, mypy
- **Testing**: pytest with coverage reporting
- **Containerization**: Docker Compose with development profiles
- **Database Migrations**: Custom migration system

## Architecture Patterns
- **Hexagonal Architecture**: Clean separation of concerns
- **Repository Pattern**: Abstract interfaces with PostgreSQL implementations
- **Dependency Injection**: For testability and modularity
- **Async/Await**: Throughout the application
- **Type Safety**: Strict type hints with mypy validation

## Infrastructure Services
- **Keycloak Authentication**: Complete user management and session handling
- **Vector Database**: PostgreSQL with pgvector for semantic search
- **Redis Caching**: Performance optimization and rate limiting
- **External APIs**: Integration with financial data sources and LLM providers

## Container Services
- **Main Application**: FastAPI app with hot reload in development
- **PostgreSQL Database**: Primary data storage with pgvector extension
- **Redis Cache**: In-memory caching and session management
- **Keycloak**: Authentication server with dedicated database
- **Development Tools**: Development profile with hot reload