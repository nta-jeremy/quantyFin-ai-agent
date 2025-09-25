# Security

Security is a paramount concern for the QuantyFinAI Agent system, encompassing both authentication and authorization to protect sensitive financial data and user information. This document details the authorization mechanisms and other security considerations.

## Authorization (RBAC)

### Role-Based Access Control (RBAC) with JWT Claims

RBAC is enforced via roles embedded as claims inside signed JWTs, issued by the application's auth service (OAuth2/OIDC). Users can perform only actions allowed by their roles and associated permissions.

Roles are defined and managed within the application (and persisted in Postgres). Each role maps to a set of permissions enforced at API/middleware boundaries.

## Defined Roles (MVP)

For MVP, keep roles minimal and clear:

*   **Admin:** Administrative access to manage users, configuration, and data ingestion.
*   **User:** Standard access to query the agent and view cited results.

Additional roles (e.g., service accounts) can be added in later sprints.

## Other Security Considerations

1.  **Prompt Injection Protection:** The **Guard Agent** validates inputs/outputs to reduce prompt injection risks and enforce policies.

2.  **Data Encryption:** All sensitive data, both at rest (in databases) and in transit (over networks), will be encrypted using industry-standard encryption protocols.

3.  **Secure API Design:** FastAPI endpoints include input validation, rate limiting, and clear error handling to prevent common web vulnerabilities.

4.  **Dependency Management:** Regular security audits of third-party libraries and dependencies will be conducted to mitigate risks from known vulnerabilities.

5.  **Logging and Monitoring:** Comprehensive logging of system activities and security events will be implemented, coupled with monitoring tools to detect and respond to suspicious activities in real-time.

6.  **Environment Variables:** Sensitive configurations (e.g., API keys, database credentials) will be managed through environment variables and never hardcoded into the codebase.
