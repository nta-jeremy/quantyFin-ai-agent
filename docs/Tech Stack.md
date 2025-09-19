# Technical Stack

The QuantyFinAI Agent project leverages a modern and robust Technical stack to ensure high performance, scalability, and maintainability. The primary technologies and frameworks are outlined below:

## Programming Language

*   **Python:** The core programming language for backend development and AI/ML components.

## AI/ML Frameworks and Libraries

*   **LangGraph:** A framework specifically chosen for building AI Agentic RAG (Retrieval-Augmented Generation) or Multi-Agent RAG systems, facilitating complex agent orchestration.
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

## Data Storage and Management

*   **PostgresDB:** A powerful, open-source relational database used for storing structured data.
*   **Postgres Vector Database (e.g., pgvector):** An extension for PostgreSQL to store and query vector embeddings, crucial for the RAG architecture.

## Caching and Session Management

*   **Redis:** An in-memory data structure store, used for caching frequently accessed data and managing user sessions to improve application responsiveness and performance.

## Containerization

*   **Docker:** A platform for developing, shipping, and running applications in containers, ensuring consistency across different environments and simplifying deployment.

## Version Control and CI/CD

*   **GitHub:** Used for source code management, version control, and as the platform for Continuous Integration/Continuous Deployment (CI/CD) pipelines.
