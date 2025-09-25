# System Architecture

The QuantyFinAI Agent system will adhere to robust architectural principles to ensure maintainability, scalability, and testability. The foundational architectural patterns and development methodologies are as follows:

## Core Architectural Principles

1.  **Clean Architecture (DDD):** This architectural style will be employed to create a loosely coupled system, separating the core business logic (domain) from external concerns such as databases, user interfaces, and external services. This promotes modularity and allows for easier testing and interchangeability of external components.

2.  **Test-Driven Development (TDD):** TDD will be a primary development practice, where tests are written before the code. This approach ensures high code quality, reduces defects, and facilitates a clear understanding of requirements and system behavior.

3.  **SOLID Principles:** The five SOLID principles of object-oriented design will guide the development process (while favoring functional programming for business logic and using classes for external connectors):
    *   **S**ingle Responsibility Principle (SRP): Each class or module should have only one reason to change.
    *   **O**pen/Closed Principle (OCP): Software entities should be open for extension, but closed for modification.
    *   **L**iskov Substitution Principle (LSP): Subtypes must be substitutable for their base types.
    *   **I**nterface Segregation Principle (ISP): Clients should not be forced to depend on interfaces they do not use.
    *   **D**ependency Inversion Principle (DIP): High-level modules should not depend on low-level modules; both should depend on abstractions.

4.  **Clean Code:** Emphasis will be placed on writing code that is easy to understand, modify, and maintain. This includes practices such as meaningful naming, small functions, clear comments (where necessary), and consistent formatting.

## Testing Strategy (MVP Focus)

In alignment with Test-Driven Development, a comprehensive testing strategy will be implemented, covering various levels of testing:

*   **Unit Tests:** To verify the correctness of individual components or functions in isolation.
*   **Integration Tests:** To ensure that different modules or services work together correctly.
*   **End-to-End Tests:** Validate the core MVP flow: retrieval from Postgres/pgvector, analysis, and aggregated answers with citations.

## Agent Engines and Orchestration

The system supports two agent engines: **Google ADK** and **LangGraph**. A registry selects the active engine via configuration (e.g., `AGENT_ENGINE`). Engine-agnostic orchestration lives alongside application use cases; engine-specific adapters implement the same contracts.

Key testing frameworks and tools will include:

*   **Pytest:** A mature and feature-rich testing framework for Python.
*   **Mock:** For simulating dependencies and isolating units under test.
*   **Fixture:** For setting up and tearing down test environments.
*   **Coverage:** For measuring code test coverage to ensure adequate testing.
