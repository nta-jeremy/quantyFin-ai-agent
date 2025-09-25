# Development Plan

This document outlines a phased development plan for the QuantyFinAI Agent project, breaking down the backlog items into actionable steps. Each phase is designed to deliver a set of functional components, building progressively towards the complete system.

## Phase 1: Foundation & Core Services

**Goal:** Establish the fundamental project infrastructure, integrate core services, and set up basic API functionalities.

**Tasks:**

1.  **Project Structure Setup:**
    *   Create the hexagonal architecture directory structure (`app/core`, `app/infrastructure`, `app/interfaces`, `app/agents`).
    *   Configure `pyproject.toml` with initial dependencies.
    *   Set up `.gitignore`, `Dockerfile`, and `docker-compose.yml` for local development environment.
    *   Implement code style enforcement tools (Black, isort, Flake8, Mypy) in pre-commit hooks or CI/CD.

2.  **Core Integrations:**
    *   **Database (PostgresDB):** Implement `postgres_adapter.py` in `app/infrastructure/persistence/` for basic CRUD operations.
    *   **Vector Database (Postgres Vector DB):** Implement `vector_db_adapter.py` in `app/infrastructure/persistence/` for vector storage and retrieval.
    *   **Redis:** Implement `redis_adapter.py` in `app/infrastructure/cache/` for caching and session management.
    *   **Auth Service:** Implement `auth_adapter.py` in `app/infrastructure/auth/` for token issuance and verification.

3.  **Basic FastAPI Endpoints:**
    *   Create `main.py` as the FastAPI application entry point.
    *   Develop a `/health` endpoint for health checks.
    *   Develop a `/hello` endpoint for basic connectivity testing.

4.  **Standardized Logging System:**
    *   Configure Python's `logging` module for structured logging across the application.
    *   Define logging levels and output formats.

**Deliverables:** Functional local development environment, basic API endpoints, integrated core services, and a standardized logging system.

## Phase 2: Authentication & Authorization

**Goal:** Implement a secure and robust user authentication and authorization system using OAuth2 and JWT.

**Tasks:**

1.  **Auth Service & OAuth2 Flow:**
    *   Implement Authorization Code flow with PKCE for user login.
    *   Issue, refresh, and revoke JWTs via internal auth service.
    *   Validate tokens (issuer, audience, signature, expiry) at the API gateway/middleware.

2.  **User Management Endpoints:**
    *   Develop FastAPI routes for user registration, login, logout, and password management (forgot/reset).
    *   Implement endpoints for retrieving, updating, and deleting user profiles.

3.  **RBAC Implementation:**
    *   Define roles (System, Super Admin, Admin, User, API) and their permissions in application config/database.
    *   Integrate role-based access control into FastAPI endpoints using decorators or middleware.
    *   Ensure proper authorization checks are performed before allowing access to resources.

**Deliverables:** Fully functional authentication and authorization system, secure user management APIs, and role-based access control enforcement.

## Phase 3: Core AI Agent Development (Initial)

**Goal:** Develop and integrate the foundational AI agents within the LangGraph framework, enabling basic RAG capabilities.

**Tasks:**

1.  **Guard Agent:**
    *   Implement `guard_agent.py` to filter and validate user inputs, preventing prompt injection.
    *   Integrate the Guard Agent as the first processing step in the LangGraph workflow.

2.  **Embedding Agent:**
    *   Implement `embedding_agent.py` to process raw documents (e.g., financial reports, news) and generate vector embeddings.
    *   Integrate with chosen embedding models (OpenAI, HuggingFace).
    *   Store embeddings and metadata in the Postgres Vector Database.

3.  **Retriever Agent:**
    *   Implement `retriever_agent.py` to query the PostgresDB for structured data and the Postgres Vector Database for semantic search.
    *   Develop logic to transform natural language queries into database-specific queries (SQL, vector search).

4.  **Search Agent:**
    *   Implement `search_agent.py` to analyze user queries and orchestrate retrieval from various sources (Retriever Agent, external web search, APIs).
    *   Develop data preprocessing and filtering mechanisms for retrieved information.

5.  **Analyze Agent:**
    *   Implement `analyze_agent.py` to process raw and retrieved documents.
    *   Develop modules for financial report analysis (extracting metrics, calculating ratios), news sentiment analysis, and legal document parsing.

6.  **Predict Agent:**
    *   Implement `predict_agent.py` to receive analyzed data and apply machine learning models for stock trend prediction.
    *   Integrate with time-series or regression models.

7.  **Aggregator Agent:**
    *   Implement `aggregator_agent.py` as the central orchestrator of the LangGraph workflow.
    *   Develop logic to coordinate agent interactions, synthesize outputs, and generate final responses using an LLM.
    *   Implement error handling and fallback mechanisms within the agentic workflow.

**Deliverables:** A functional multi-agent RAG system capable of processing queries, retrieving information, performing initial analysis, and generating predictions, orchestrated by LangGraph.
