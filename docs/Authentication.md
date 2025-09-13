# Authentication

The QuantyFinAI Agent system implements robust authentication mechanisms to secure user access and ensure data integrity. The primary components and protocols for authentication are:

## 1. Keycloak: Single Sign-On (SSO)

**Keycloak** will serve as the central Identity and Access Management (IAM) solution, providing Single Sign-On (SSO) capabilities. This allows users to authenticate once and gain access to multiple applications and services within the QuantyFinAI ecosystem without re-entering credentials. Keycloak manages user identities, authentication flows, and session management.

## 2. JWT: JSON Web Token

**JSON Web Tokens (JWT)** will be used as a secure, compact, and URL-safe means of representing claims between two parties. After successful authentication with Keycloak, the system will issue JWTs to users. These tokens will be used to authorize subsequent requests to the FastAPI backend, carrying user identity and permissions information.

## 3. OAuth2: Open Authorization 2.0

**OAuth 2.0** is the industry-standard protocol for authorization. It will be utilized to enable secure delegated access to resources. Keycloak, acting as an OAuth 2.0 authorization server, will manage the issuance of access tokens (JWTs) to client applications on behalf of the user, without exposing user credentials.

## Authentication Flow (Conceptual)

1.  **User Initiates Login:** User attempts to access the QuantyFinAI Agent application.
2.  **Redirection to Keycloak:** The application redirects the user to the Keycloak login page.
3.  **User Authentication:** User provides credentials (username/password) to Keycloak.
4.  **Keycloak Issues Tokens:** Upon successful authentication, Keycloak issues an ID Token (containing user identity) and an Access Token (JWT) to the application.
5.  **Application Uses JWT:** The application stores the JWT and includes it in the `Authorization` header of subsequent API requests to the QuantyFinAI Agent backend.
6.  **Backend Validates JWT:** The FastAPI backend validates the JWT to ensure the user is authenticated and the token is valid and unexpired.

This setup provides a secure, scalable, and standardized approach to user authentication, leveraging established industry best practices.
