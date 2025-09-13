# Task Completion Checklist - QuantyFinAI Agent

## Before Finishing Any Task

### Code Quality ✅
- [ ] Run `poetry run black .` for code formatting
- [ ] Run `poetry run isort .` for import sorting
- [ ] Run `poetry run flake8 .` for linting
- [ ] Run `poetry run mypy app/` for type checking
- [ ] Check file length is under 500 lines (except test files)
- [ ] Verify no duplicate code exists

### Testing ✅
- [ ] Run `poetry run pytest` for all tests
- [ ] Run `poetry run pytest --cov=app` for coverage
- [ ] Ensure coverage meets minimum requirements (80%)
- [ ] Test both unit and integration scenarios
- [ ] Verify no tests are broken

### Documentation ✅
- [ ] Add/update docstrings for new functions/classes
- [ ] Update README if API endpoints changed
- [ ] Update relevant documentation in docs/ folder
- [ ] Check comments are clear and necessary

### Code Review ✅
- [ ] Review code against SOLID principles
- [ ] Verify hexagonal architecture is maintained
- [ ] Check for proper dependency injection
- [ ] Ensure repository pattern is followed
- [ ] Validate async/await patterns are consistent

### Security ✅
- [ ] Run security checks with `bandit`
- [ ] Verify no sensitive data is logged
- [ ] Check authentication/authorization logic
- [ ] Validate input sanitization
- [ ] Ensure proper error handling

### Performance ✅
- [ ] Check database query efficiency
- [ ] Verify proper use of async operations
- [ ] Test memory usage patterns
- [ ] Check for potential bottlenecks
- [ ] Validate caching strategies

### Integration ✅
- [ ] Test with actual database (not just mocks)
- [ ] Verify authentication flow end-to-end
- [ ] Test caching mechanisms
- [ ] Check external API integrations
- [ ] Validate container setup

## Feature-Specific Checklists

### Database Changes ✅
- [ ] Create migration script if needed
- [ ] Update domain models
- [ ] Update repository implementations
- [ ] Test with existing data
- [ ] Verify data integrity

### API Endpoints ✅
- [ ] Add proper route definitions
- [ ] Implement request/response models
- [ ] Add authentication middleware
- [ ] Test error scenarios
- [ ] Update OpenAPI documentation

### Authentication Features ✅
- [ ] Test token generation/validation
- [ ] Verify role-based access control
- [ ] Test session management
- [ ] Check security headers
- [ ] Test logout/refresh flows

### AI Agent Features ✅
- [ ] Test agent workflow independently
- [ ] Verify LangGraph integration
- [ ] Test error handling in agent workflows
- [ ] Check resource usage patterns
- [ ] Validate agent communication

## Final Checks ✅
- [ ] All pre-commit hooks pass
- [ ] No breaking changes to existing APIs
- [ ] Configuration files updated if needed
- [ ] Dependencies updated properly
- [ ] Git commit message is descriptive

## Deployment Preparation ✅
- [ ] Docker builds successfully
- [ ] Environment variables documented
- [ ] Database migrations tested
- [ ] Health checks working
- [ ] Logging configuration verified

## Post-Completion ✅
- [ ] Commit changes with descriptive message
- [ ] Push to appropriate branch
- [ ] Create pull request if needed
- [ ] Update task tracking system
- [ ] Notify team of completion