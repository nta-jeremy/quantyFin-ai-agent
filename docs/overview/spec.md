## QuantyFin AI Agent — Comprehensive Specification (MVP)

### 1) Product Overview
- **Purpose**: Multi‑agent RAG system for grounded financial analysis with citations.
- **Primary capabilities**: Retrieve, analyze, and synthesize information from corporate financial reports and indexed news; provide cited answers. Prediction is optional for MVP.
- **Users**: Individual investors, analysts, small funds.

### 2) Scope and Non‑Goals (MVP)
- **In scope**:
  - Natural‑language Q&A grounded in indexed sources (financial reports, curated news)
  - Semantic retrieval over embeddings (Postgres + pgvector)
  - Analysis of core metrics: revenue, profit, cash flow, debt; ratios (P/E, ROE, ROA); trend analysis
  - Cited answers and explainable outputs
  - Basic auth: OAuth2/OIDC + JWT; **RBAC** with roles `Admin`, `User`
- **Out of scope (later)**:
  - Advanced real‑time prediction, streaming market data
  - Broad web search and external APIs (can be added post‑MVP)

### 3) System Architecture
- **Architecture principles**: Clean Architecture with DDD boundaries; TDD; SOLID; Clean Code.
- **Layers**:
  - `app/domain`: Entities, value objects, domain services, repository ports (pure, framework‑agnostic)
  - `app/application`: Use cases, DTOs, mappers, contracts (depends only on domain)
  - `app/interfaces`: Delivery adapters (FastAPI, CLI, subscribers) mapping IO to use cases
  - `app/infrastructure`: DB repositories, external service clients, cache, auth, messaging
  - `app/agents`: Engine‑agnostic orchestration + engine‑specific adapters (Google ADK, LangGraph)
- **Dependency rule**: Outer layers depend inward only; inner layers never import outer ones.
- **Bounded contexts** (as app grows): research, analysis, prediction per layer, with interactions via application use cases.

### 4) AI Architecture and Orchestration
- **RAG flow**:
  1) Query received and validated
  2) Retrieve relevant chunks via semantic search from vector store
  3) Augment LLM context with retrieved facts
  4) Generate grounded response with citations
- **Dual engines**: Google ADK and LangGraph; selected at runtime via `AGENT_ENGINE` config and `app/agents/registry.py`.
- **Models**:
  - LLMs: OpenAI, Anthropic, Gemini, DeepSeek (pluggable)
  - Embeddings: OpenAI, HuggingFace

### 5) Agents: Roles and Responsibilities
- **Guard Agent**: Prompt‑injection protection, input/output validation, policy enforcement.
- **Embedding Agent**: Preprocess (chunk/clean), generate embeddings, persist with metadata in pgvector.
- **Search Agent**: Transform intent into external searches (future), curate retrieved snippets.
- **Retriever Agent**: Translate NL → SQL/vector queries; query Postgres and pgvector; rank/filter results.
- **Analyze Agent**: Extract financials, compute ratios, sentiment/entity extraction for news; trend analysis.
- **Aggregator Agent**: Orchestrate flow; synthesize outputs; deduplicate/resolve conflicts; generate final LLM answer with citations; handle errors/fallbacks.
- **Predict Agent** (post‑MVP optional): Time‑series and regression modeling (e.g., ARIMA/LSTM); evaluate and iterate.

### 6) Security, Authentication, Authorization
- **Authentication**: OAuth2/OIDC Authorization Code with PKCE for users; Client Credentials for services.
- **Tokens**: JWT for identity/claims; carried via `Authorization: Bearer <token>`.
- **Authorization**: RBAC using JWT `roles` claim; MVP roles:
  - `Admin`: manage users, config, data ingestion
  - `User`: query the agent and view cited results
- **Additional controls**: Guard Agent for injection filtering; encryption in transit/at rest; rate limiting; dependency audits; logging/monitoring; secrets via env vars.

### 7) Memory Strategy
- **Short‑term**: Redis for sessions/cache and recent context; cache hot retrieval results.
- **Long‑term**: Postgres + pgvector for persistent knowledge (financial reports, news, regulatory docs, economic data, stock info). Semantic search enables RAG grounding.

### 8) Data and Schemas (Conceptual)
- **Relational (Postgres)**:
  - `users`: id (UUID), username, email, password_hash, timestamps, role_id
  - `roles`: id, name (unique), description
- **Vector store (pgvector)**:
  - `document_embeddings`: id (UUID), source_type, optional source_id, content_chunk, embedding VECTOR(<dim>), created_at, metadata JSONB
  - Metadata MVP keys: `source`, `source_date`, `doc_type`, `company_name`, `ticker`; optional `url`, `title`

### 9) Migrations
- Migration files for core schema (users/roles) and vector tables (`document_embeddings`, etc.).
- Utilities: scripted runner for migrate/status/target‑version; init script creates DB, installs extensions (`uuid-ossp`, `vector`, `pg_trgm`), runs migrations, seeds initial data.
- Practices: backup first, test in dev, wrap in transactions, track versions/checksums, plan rollbacks, performance‑test heavy changes.

### 10) Tech Stack
- **Language**: Python
- **Frameworks**: FastAPI (API), LangGraph/Google ADK (agents)
- **LLM/Embeddings**: OpenAI, Anthropic, Gemini, DeepSeek; OpenAI/HuggingFace embeddings
- **Data**: PostgreSQL, pgvector; Redis (cache/session)
- **Tooling**: Docker; GitHub + Actions (CI/CD)

### 11) Code Style and Conventions
- Python: PEP 8; 4‑space indents; 79 char code lines; grouped imports; type hints everywhere.
- Naming: snake_case for functions/vars; CapWords for classes; ALL_CAPS constants.
- Docstrings: Google‑style; comments explain "why".
- Errors: raise specific exceptions; log with context; no silent failures.
- Logging: stdlib `logging`, consistent levels; avoid sensitive data.
- Formatting/Linting: Black, isort, Flake8, Mypy integrated in CI.

### 12) Testing Strategy
- **TDD focus** with:
  - Unit tests for domain/application (pure functions)
  - Integration tests for interfaces/infrastructure (FastAPI, repos, engines)
  - E2E for MVP flow: retrieval → analysis → cited answer
- Engine‑agnostic orchestration tests mock ports; engine‑specific tests verify wiring.

### 13) Configuration and Runtime
- Central settings expose `agent_engine: "google_adk" | "langgraph"` and provider keys/URLs.
- `main.py` composes adapters and exposes FastAPI routes under `interfaces/api`.

### 14) Operational Concerns
- **Observability**: structured logs; security/event logs; basic metrics for latency and cache hit rate.
- **Error handling**: guardrails in agents; clear, actionable API errors; RBAC denials return appropriate statuses.
- **Performance**: cache repeated retrievals; HNSW indexes for vector search; paginate results; timeouts and backoffs for external calls.

### 15) Roadmap (Indicative)
- Sprint 1: Clean Architecture skeleton; FastAPI health; Postgres + pgvector + Redis; basic Embedding/Retriever; Analyze core ratios; Aggregator with citations.
- Sprint 2: Real documents ingestion (5–10 companies); improve chunking/metadata; retrieval tuning and evaluation.
- Sprint 3: RBAC applied to APIs; harden Guard Agent; observability.
- Sprint 4: Introduce basic Predict Agent; offline evaluation and model selection.

### 16) Success Metrics
- Retrieval quality (Recall@K); percentage of answers with valid citations
- Latency P50/P95; compute cost per query
- User CSAT on a standardized question set

### 17) Acceptance Criteria (MVP)
- Can answer user NL queries about covered companies with at least one valid citation
- Computes and reports core financial metrics and simple trends
- Enforces OAuth2/OIDC authentication and RBAC for protected endpoints
- All code passes linting/formatting/type‑checking and has unit/integration tests for core flows
