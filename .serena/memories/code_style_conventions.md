# Code Style and Conventions for QuantyFinAI Agent

## Python Style Guidelines

### General Principles
- **Functional Programming**: Prefer functional programming over OOP
- **OOP Classes**: Use only for connectors and interfaces to external systems
- **Pure Functions**: Business logic should use pure functions with clear input/output
- **No Hidden State**: Functions must ONLY modify their return values
- **Minimal Changes**: Make minimal, focused changes following DRY, KISS, YAGNI

### Type Safety
- **Strict Typing**: Use strict type hints for function returns and variables
- **Named Parameters**: Use named parameters in function calls when possible
- **No Any Types**: Avoid `Any` type usage except for external API responses
- **Pydantic Models**: Prefer Pydantic over TypedDict for data models
- **Custom Types**: Create proper type definitions for non-trivial data structures

### Code Organization
- **File Length**: Keep logic in each file under 500 lines (except test files)
- **No Default Parameters**: Never use default parameter values in function definitions
- **Single Responsibility**: Each function should have a single, clear responsibility
- **Clear Naming**: Use descriptive, meaningful names for functions and variables

### Async Patterns
- **Consistent Async**: Always use async/await for all database operations
- **No Blocking Operations**: Avoid blocking operations in async contexts
- **Timeout Handling**: Implement proper timeout handling for external API calls

### Error Handling
- **Explicit Errors**: Always raise errors explicitly, never silently ignore them
- **Specific Exceptions**: Use specific error types (ValueError, TypeError, etc.)
- **Immediate Raising**: Raise errors immediately when they occur
- **Error Context**: Log errors with appropriate context before raising them

## Configuration and Settings

### Pydantic Settings
- **field_validator**: Use `field_validator` instead of deprecated `validator`
- **Environment Variables**: Use environment-specific configurations
- **Secret Management**: Use SecretStr for sensitive configuration
- **Nested Configuration**: Use nested configuration groups

### Database Operations
- **Repository Pattern**: Use repository pattern with abstract interfaces
- **Dependency Injection**: Services use dependency injection for testability
- **Connection Pooling**: Use connection pooling for PostgreSQL connections

## Documentation Standards

### Docstrings
- **English Only**: Comments and docstrings must be in English
- **Comprehensive**: Document purpose, parameters, return values, and exceptions
- **Consistent Format**: Use consistent docstring format throughout the codebase

### Comments
- **Purposeful**: Only add comments that provide value
- **Code Clarity**: Code should be self-documenting where possible
- **TODO Comments**: Use TODO comments for future improvements

## Testing Conventions

### Test Structure
- **Test Organization**: Separate unit, integration, and e2e tests
- **Async Testing**: Use pytest-asyncio for async tests
- **Test Data**: Use factory-boy for test data generation
- **Coverage**: Maintain comprehensive test coverage

### Test Patterns
```python
# Use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_user_creation():
    # Arrange
    user_data = UserCreate(email="test@example.com", ...)

    # Act
    created_user = await user_repo.create(user_data)

    # Assert
    assert created_user.email == user_data.email
    assert created_user.id is not None
```

## Agent Development Conventions

### Agent Structure
- **Base Agent**: All agents must extend `BaseAgent` from `base_agent.py`
- **State Management**: Use `AgentState` from `agent_state.py` for state handling
- **Type Definitions**: Use types from `agent_types.py` for agent-specific types
- **Workflow Integration**: Agents must be compatible with `LangGraphWorkflow`

### Agent Naming
- **Agent Classes**: Use descriptive names ending with "Agent" (e.g., `GuardAgent`)
- **Agent Methods**: Use descriptive action-oriented names (e.g., `validate_input`, `generate_embeddings`)
- **Agent Variables**: Use clear, descriptive names for agent state variables

### Agent Error Handling
- **Agent-Specific Errors**: Create custom exception classes for agent errors
- **Graceful Degradation**: Implement fallback behavior for agent failures
- **Error Logging**: Log agent errors with appropriate context
- **Recovery**: Implement agent recovery mechanisms where applicable

## API Development

### FastAPI Patterns
- **Dependency Injection**: Use dependency injection for FastAPI endpoints
- **Response Models**: Implement proper response models with Pydantic
- **OpenAPI Documentation**: Include comprehensive OpenAPI documentation
- **Security**: Validate JWT tokens on protected endpoints

### Security Practices
- **Input Validation**: Always validate input data with Pydantic models
- **SQL Injection**: Use parameterized queries to prevent SQL injection
- **CORS**: Implement proper CORS configuration
- **HTTPS**: Use HTTPS in production environments

## Performance Considerations

### Database Optimization
- **Connection Pooling**: Use connection pooling for PostgreSQL connections
- **Indexing Strategy**: Implement proper indexing strategy for vector search
- **Batch Operations**: Use batch operations for multiple database operations
- **Redis Caching**: Use Redis caching for frequently accessed data

### Vector Search Optimization
- **HNSW Indexes**: Use HNSW indexes for efficient vector similarity search
- **Embedding Dimensions**: Optimize embedding dimensions for your use case
- **Batch Processing**: Process vector embeddings in batches for better performance
- **Caching**: Cache frequently accessed vector results

## Code Quality Tools

### Tool Configuration
- **Black**: Code formatting with line length 79
- **isort**: Import sorting with Black profile
- **flake8**: Linting for code quality
- **mypy**: Static type checking with strict settings

### Pre-commit Hooks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run all hooks
poetry run pre-commit run --all-files
```

## File Naming and Structure

### Python Files
- **snake_case**: Use snake_case for Python file names
- **Module Organization**: Group related functionality in modules
- **Clear Separation**: Maintain clear separation between layers

### Configuration Files
- **pyproject.toml**: Use pyproject.toml for project configuration
- **Environment Files**: Use .env files for environment-specific settings
- **Docker Configuration**: Maintain separate Docker configurations for different environments

## Agent-Specific Patterns

### LangGraph Integration
- **Workflow Nodes**: Each agent should be a separate node in the workflow
- **State Passing**: Pass state between agents using the workflow state
- **Conditional Logic**: Use LangGraph's conditional routing for agent selection
- **Error Handling**: Implement workflow-level error handling

### Agent Communication
- **Standardized Input/Output**: Use standardized input/output formats for agents
- **State Updates**: Update workflow state consistently across agents
- **Error Propagation**: Propagate errors through the workflow appropriately
- **Logging**: Log agent actions and decisions consistently

## Code Review Guidelines

### Review Focus
- **Type Safety**: Check for proper type hints and mypy compliance
- **Error Handling**: Ensure proper error handling and logging
- **Performance**: Consider performance implications of changes
- **Security**: Review for security vulnerabilities
- **Testing**: Verify adequate test coverage for new features

### Code Quality Metrics
- **Complexity**: Keep function complexity low
- **Duplication**: Eliminate code duplication
- **Maintainability**: Write maintainable, readable code
- **Documentation**: Ensure code is well-documented

## Database Code Conventions

### Repository Pattern
```python
# Abstract interface
class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

# PostgreSQL implementation
class PostgreSQLUserRepository(UserRepository):
    async def create(self, user: User) -> User:
        # Implementation with asyncpg
        pass
```

### Vector Database Operations
- **Embedding Storage**: Store embeddings using the vector database adapter
- **Similarity Search**: Use the vector database adapter for similarity search
- **Index Management**: Manage vector indexes through the adapter
- **Batch Operations**: Use batch operations for vector insertions and updates

## Authentication and Security

### JWT Token Handling
- **Token Validation**: Validate JWT tokens on all protected endpoints
- **Token Refresh**: Implement token refresh mechanism
- **Token Expiration**: Handle token expiration gracefully
- **Token Storage**: Store tokens securely on the client side

### Keycloak Integration
- **User Management**: Use Keycloak for user management
- **Role-Based Access**: Implement role-based access control
- **Session Management**: Use Keycloak for session management
- **Token Validation**: Validate tokens with Keycloak public keys

## API Response Standards

### Response Format
- **Consistent Structure**: Use consistent response structure across endpoints
- **Error Responses**: Use standardized error response format
- **Success Responses**: Use standardized success response format
- **Pagination**: Implement pagination for large datasets

### Status Codes
- **200 OK**: Successful GET requests
- **201 Created**: Successful POST requests
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server errors