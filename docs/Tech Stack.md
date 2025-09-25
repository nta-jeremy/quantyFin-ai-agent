# Tech Stack

The QuantyFinAI Agent project leverages a modern and robust stack to ensure performance, scalability, and maintainability. The primary technologies and frameworks are outlined below and align with the MVP described in `docs/overview/idea.md`.

## Programming Language

*   **Python:** The core programming language for backend development and AI/ML components.

## AI/ML Frameworks and Libraries

*   **LangGraph & Google ADK:** Dual-engine support. One agent workflow uses Google ADK; the other uses LangChain/LangGraph. Engine selection is configurable at runtime.
*   **LLM Providers:** Integration with various Large Language Model (LLM) providers for natural language understanding and generation capabilities:
    *   OpenAI
    *   Anthropic
    *   Gemini
    *   DeepSeek
*   **Embedding Providers:** Utilization of embedding models for converting text into vector representations:
    *   OpenAI
    *   HuggingFace

## Backend and API Development

*   **FastAPI:** A modern, fast (high-performance) web framework for building RESTful APIs with Python, offering automatic interactive API documentation.

## Orchestration & Configuration

*   **Dual Engine Orchestration:** Agents can run on either Google ADK or LangGraph. A registry selects the engine via configuration (e.g., environment variable `AGENT_ENGINE`).
*   **Guardrails:** A Guard Agent validates inputs/outputs to reduce prompt injection and enforce policies.

## Data Storage and Management

*   **PostgresDB:** A powerful, open-source relational database used for storing structured data.
*   **PostgreSQL + pgvector:** PostgreSQL for structured data and the `pgvector` extension for storing/querying embeddings (RAG).

## Caching and Session Management

*   **Redis:** An in-memory data structure store, used for caching frequently accessed data and managing user sessions to improve application responsiveness and performance.

## Containerization

*   **Docker:** A platform for developing, shipping, and running applications in containers, ensuring consistency across different environments and simplifying deployment.

## Version Control and CI/CD

*   **GitHub + GitHub Actions:** Source control and CI/CD pipelines for tests and deployments.

## Authentication & Authorization (MVP)

*   **OAuth2/OIDC + JWT:** Authentication via OAuth2/OIDC; JWT carries claims.
*   **RBAC:** Roles: `Admin`, `User` (extendable later).

## Scope Notes

*   **MVP Retrieval Sources:** Corporate financial reports and indexed news. Web search/API integrations can be added later.
*   **Predict Agent:** Can be deferred to a later sprint.
