# Project Structure

The project structure is designed to adhere to Hexagonal Architecture principles, promoting clear separation of concerns, testability, and scalability. The following tree-like representation outlines the main directories and files:

```
QuantyFinAI-agent/
├── .github/                 # GitHub Actions for CI/CD
│   └── workflows/
│       └── main.yml
├── app/                     # Application core (Hexagonal Architecture - Domain/Application Layer)
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core business logic, domain models, interfaces (Ports)
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── models.py    # Pydantic models for data entities
│   │   │   └── services.py  # Domain services interfaces
│   │   └── application/
│   │       ├── __init__.py
│   │       ├── use_cases/   # Application-specific business rules (Use Cases)
│   │       │   ├── __init__.py
│   │       │   └── financial_analysis.py
│   │       └── dtos.py      # Data Transfer Objects
│   ├── infrastructure/      # Adapters for external concerns (Adapters)
│   │   ├── __init__.py
│   │   ├── persistence/     # Database adapters
│   │   │   ├── __init__.py
│   │   │   ├── postgres_adapter.py
│   │   │   └── vector_db_adapter.py
│   │   ├── api/             # External API integrations (e.g., LLM providers, external data sources)
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py
│   │   │   └── external_news_api.py
│   │   ├── cache/           # Redis cache adapter
│   │   │   ├── __init__.py
│   │   │   └── redis_adapter.py
│   │   └── auth/            # Keycloak/JWT authentication adapter
│   │       ├── __init__.py
│   │       └── keycloak_adapter.py
│   ├── interfaces/          # Entry points to the application (Ports/APIs)
│   │   ├── __init__.py
│   │   ├── api/             # FastAPI endpoints
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   └── stock_routes.py
│   │   │   └── auth_routes.py
│   │   └── cli/             # Command Line Interface (if any)
│   │       └── __init__.py
│   └── agents/              # LangGraph agents implementation
│       ├── __init__.py
│       ├── guard_agent.py
│       ├── embedding_agent.py
│       ├── aggregator_agent.py
│       ├── search_agent.py
│       ├── retriever_agent.py
│       ├── analyze_agent.py
│       └── predict_agent.py
├── config/                  # Configuration files
│   ├── __init__.py
│   └── settings.py          # Environment-specific settings
├── tests/                   # Test suite (following TDD)
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   └── core/
│   │       └── domain/
│   │           └── test_models.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── infrastructure/
│   │       └── persistence/
│   │           └── test_postgres_adapter.py
│   └── e2e/
│       ├── __init__.py
│       └── test_api_endpoints.py
├── scripts/                 # Utility scripts (e.g., database migrations, data seeding)
│   ├── __init__.py
│   └── init_db.py
├── docs/                    # Project documentation
│   └── architecture.md
├── .env.example             # Example environment variables
├── Dockerfile               # Docker build instructions
├── docker-compose.yml       # Docker Compose for local development
├── pyproject.toml           # Project metadata and dependencies (e.g., Poetry/PDM)
├── README.md                # Project README
└── .gitignore               # Git ignore file
```

## Explanation of Key Directories:

*   **`app/core/`**: Contains the application's domain logic and abstract interfaces (ports) that define what the application can do, independent of how it's implemented.
*   **`app/infrastructure/`**: Houses the concrete implementations (adapters) that connect the core application to external services like databases, APIs, and caching mechanisms.
*   **`app/interfaces/`**: Defines the entry points into the application, such as REST API endpoints using FastAPI.
*   **`app/agents/`**: Dedicated directory for the LangGraph-based AI agents, each encapsulating specific functionalities.
*   **`config/`**: Centralized management for application settings and environment variables.
*   **`tests/`**: Organized by testing levels (unit, integration, end-to-end) to support the TDD methodology.
*   **`.github/workflows/`**: Contains CI/CD pipeline definitions for automated testing and deployment.
