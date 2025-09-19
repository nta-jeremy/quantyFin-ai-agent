# Code Style and Conventions - QuantyFinAI Agent

## Python Guidelines

### PEP 8 Compliance
- **Indentation**: 4 spaces per level
- **Line Length**: Maximum 79 characters (99 for docstrings/comments)
- **Imports**: Grouped as standard library, third-party, local (separated by blank lines)
- **Use isort** for automatic import sorting

### Naming Conventions
- **Modules**: `snake_case.py` (short, lowercase)
- **Packages**: `lowercase` (no underscores)
- **Classes**: `CamelCase`
- **Functions/Methods**: `snake_case`
- **Variables**: `snake_case`
- **Constants**: `ALL_CAPS_WITH_UNDERSCORES`
- **Private Members**: `_single_underscore_prefix`
- **Type Variables**: `CamelCase`

### Type Hints
- **Mandatory**: All function arguments and return values must be type-hinted
- **Use proper types**: Avoid `Any` type except for external API responses
- **Pydantic models**: Preferred over TypedDict for data models
- **Strict typing**: Use specific types rather than generic collections when possible

### Documentation
- **Docstrings**: Google Style format with triple double quotes
- **Required**: All modules, classes, methods, and functions must have docstrings
- **Comments**: Explain "why" not "what" - use sparingly

### Error Handling
- **Specific exceptions**: Use specific error types (ValueError, TypeError) rather than generic Exception
- **Never ignore**: Always raise errors explicitly, never silently ignore them
- **Logging**: Log errors with appropriate context before raising them

### Async/Await Patterns
- **Consistency**: Use async/await consistently throughout the application
- **Database operations**: All database operations must be async
- **External APIs**: Use async HTTP clients for external API calls

### Architecture Patterns
- **Repository Pattern**: All database operations use repository pattern with abstract interfaces
- **Dependency Injection**: Services use dependency injection for testability
- **Hexagonal Architecture**: Business logic separated from external concerns
- **Clean Code**: Functions must ONLY modify return values, never input parameters or global state

### Functional Programming
- **Prefer pure functions**: Clear input/output, no hidden state changes
- **Avoid OOP**: Use separate OOP classes only for connectors and external system interfaces
- **Immutable data**: Design functions to be pure and side-effect free

### Testing
- **TDD**: Write tests before implementation
- **pytest-asyncio**: Use for async tests
- **Test structure**: Unit, integration, and e2e tests
- **Factory patterns**: Use factory-boy for test data generation

### Configuration
- **Pydantic Settings**: Use for all configuration management
- **Environment-specific**: Support different environments (dev, staging, prod)
- **Secret management**: Use SecretStr for sensitive data

### File Organization
- **500-line limit**: Keep logic in each file under 500 lines (except test files)
- **Clear structure**: Follow hexagonal architecture layout
- **Module cohesion**: Related functionality should be grouped together