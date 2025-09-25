# Project Structure

This project follows Clean Architecture with Domain-Driven Design (DDD). The goal is clear separation of concerns, strict dependency direction, testability, and business-centric design via bounded contexts. Business logic prefers pure functions; classes are used for connectors to external systems.

```
QuantyFinAI-agent/
├── .github/
│   └── workflows/
├── app/
│   ├── domain/                      # DDD: Enterprise business rules (pure, framework-agnostic)
│   │   ├── __init__.py
│   │   ├── entities/               # Entities, Aggregates, Value Objects
│   │   ├── events/                 # Domain events
│   │   ├── repositories/           # Repository interfaces (ports)
│   │   ├── services/               # Domain services (pure functions)
│   │   └── specifications/         # Business invariants/specifications
│   ├── application/                 # Application business rules (use cases)
│   │   ├── __init__.py
│   │   ├── use_cases/              # Orchestrate domain operations
│   │   ├── dto/                    # Input/Output models for use cases
│   │   ├── mappers/                # Conversions between layers
│   │   └── contracts/              # Ports used by use cases (e.g., message bus)
│   ├── interfaces/                  # Interface adapters (delivery mechanisms)
│   │   ├── __init__.py
│   │   ├── api/                    # FastAPI routers/controllers, request/response models
│   │   ├── cli/                    # CLI entry points
│   │   └── subscribers/            # Event handlers bridging outward
│   ├── infrastructure/              # Frameworks & drivers (outer layer)
│   │   ├── __init__.py
│   │   ├── persistence/            # DB implementations of repositories
│   │   ├── external_services/      # LLMs, news APIs, pricing feeds
│   │   ├── cache/                  # Redis or in-memory cache
│   │   ├── auth/                   # JWT/OIDC adapters
│   │   └── messaging/              # Message bus, background jobs
│   └── agents/                      # Agent workflows (pluggable engines)
│       ├── __init__.py
│       ├── engines/
│       │   ├── __init__.py
│       │   ├── google_adk/         # Google ADK-based agent implementation
│       │   │   ├── __init__.py
│       │   │   ├── builders.py     # Build ADK tools/graphs from ports
│       │   │   └── runtime.py      # ADK runtime wiring
│       │   └── langgraph/          # LangChain/LangGraph-based agent implementation
│       │       ├── __init__.py
│       │       ├── workflow.py     # LangGraph graph definitions
│       │       └── nodes.py        # Node/tool definitions
│       ├── orchestration/          # Engine-agnostic orchestration (use-case level)
│       │   ├── __init__.py
│       │   ├── planner.py
│       │   └── policies.py
│       ├── ports/                  # Agent-facing ports to application layer
│       │   ├── __init__.py
│       │   └── tool_contracts.py   # Definitions mapped by each engine
│       └── registry.py             # Select engine at runtime via config (AGENT_ENGINE)
├── config/
│   ├── __init__.py
│   └── settings.py
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   ├── integration/
│   │   ├── interfaces/
│   │   └── infrastructure/
│   └── e2e/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── main.py                         # Composition root (wiring/bootstrapping)
```

## Layer Responsibilities (Clean Architecture + DDD)

- **`app/domain`**: Pure business concepts. Contains entities, value objects, aggregates, domain services, domain events, and repository interfaces. No framework imports.
- **`app/application`**: Use cases orchestrating domain behavior. Depends only on `domain` and contracts. Contains DTOs and mappers for IO boundaries. No infrastructure imports.
- **`app/interfaces`**: Adapters that translate delivery protocols (HTTP/CLI/events) into application use case inputs and back to responses.
- **`app/infrastructure`**: Concrete implementations for repositories, external APIs, cache, messaging, and auth. Depends inward on `domain` and `application` interfaces.
- **`app/agents`**: Agent workflows coordinating multiple use cases; treat as application orchestration. Keep pure where possible; external calls via ports. Supports Google ADK and LangGraph engines.
  - Engine-agnostic orchestration lives in `app/agents/orchestration` and depends on `app/application` use cases only.
  - Engine-specific adapters live under `app/agents/engines/{google_adk|langgraph}` and adapt agent ports to the chosen runtime.
  - `app/agents/registry.py` is the single entrypoint to resolve the current engine and expose a unified agent interface to the rest of the app.

## Dependency Rule

Dependencies point inward only: `infrastructure` → `interfaces` → `application` → `domain`. Inner layers must not import outer layers.

## Bounded Contexts

As the system grows, organize by bounded contexts inside each layer to keep cohesion high. Example:

```
app/
  domain/
    research/
    analysis/
    prediction/
  application/
    research/
    analysis/
    prediction/
  interfaces/
    api/
      v1/
  infrastructure/
    persistence/
    external_services/
```

Each bounded context exposes its own aggregates, use cases, and ports. Cross-context interactions should go through application-level use cases and contracts.

## Conventions

- **Pure functions** in domain and application layers; no hidden state.
- **Strict typing** everywhere; prefer Pydantic models for DTOs and request/response shapes. No default parameter values; use explicit parameters.
- **Errors**: raise specific error types; do not continue after failures.
- **Mapping**: confine serialization/deserialization to `interfaces` and `application/mappers`.
- **Testing**: unit tests for `domain` and `application`; integration tests for `interfaces` and `infrastructure`; e2e for full flows.

## Mapping to Current Codebase

- Existing `app/agents/` remains but is now split into engine-agnostic orchestration and engine-specific implementations (Google ADK, LangGraph).
- `main.py` serves as the composition root to wire adapters (infrastructure) into application ports and expose delivery (FastAPI) in `interfaces/api`.

### Agent Engine Selection

- Configure the active engine via environment/config (e.g., `AGENT_ENGINE=google_adk` or `AGENT_ENGINE=langgraph`).
- `config/settings.py` should expose a typed setting `agent_engine: Literal["google_adk", "langgraph"]`.
- `app/agents/registry.py` reads the setting and returns the appropriate engine façade with a consistent API.

### Testing Guidance

- Unit tests for `app/agents/orchestration` mock agent ports (engine-agnostic).
- Engine-specific tests live under `tests/integration/agents/engines/{google_adk|langgraph}` and verify wiring to their runtimes.

This structure keeps business rules independent of frameworks and implementation details, enabling easy testing and future replacement of adapters without touching core logic.
