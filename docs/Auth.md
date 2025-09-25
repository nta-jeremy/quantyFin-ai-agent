# Authentication & Authorization

The QuantyFinAI Agent system implements robust authentication and authorization to secure user access and ensure data integrity. The primary components and protocols are:

## 1. OAuth2/OIDC

The system uses **OAuth 2.0 / OpenID Connect (OIDC)**. Users authenticate via Authorization Code with PKCE (recommended for web and native clients). For service-to-service communication, Client Credentials may be used.

## 2. JWT: JSON Web Token

**JSON Web Tokens (JWT)** carry identity and claims. After successful OAuth2/OIDC authentication, the auth service issues JWT access tokens (and refresh tokens when applicable). Tokens are included in the `Authorization` header for subsequent API requests.

## 3. Authorization: Role-Based Access Control (RBAC)

Authorization is enforced using **RBAC**. User roles are embedded as JWT claims (e.g., `roles: ["admin", "user"]`). The backend maps roles to permissions and enforces them at route and service boundaries.

### MVP Roles

*   **Admin**: Manage users, configuration, data ingestion.
*   **User**: Query the agent and view cited results.

## Authentication Flow (Conceptual)

1.  **User Initiates Login:** User attempts to access the QuantyFinAI Agent application.
2.  **Start OAuth2 Flow:** The application starts the OAuth2 Authorization Code flow with PKCE.
3.  **User Authentication:** User authenticates with the QuantyFinAI authentication service (OIDC provider).
4.  **Auth Service Issues Tokens:** Upon success, the service issues an Access Token (JWT) and optionally a Refresh Token to the application.
5.  **Application Uses JWT:** The application includes the Access Token in the `Authorization: Bearer <token>` header for API requests.
6.  **Backend Validates JWT:** The FastAPI backend validates the JWT signature, issuer, audience, and expiry.

This setup provides a secure, scalable, and standardized approach to user authentication using OAuth2 and JWT.

## Authorization Flow (RBAC)

1.  **Extract Roles:** Backend extracts `roles` and other claims from the validated JWT.
2.  **Map to Permissions:** Roles are mapped to application permissions (e.g., read/write on resources).
3.  **Enforce Access:** Route and service handlers enforce permissions before executing protected actions.
4.  **Deny on Failure:** Requests lacking required roles/permissions are rejected with appropriate error responses.
