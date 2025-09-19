# Code Style and Conventions

Adherence to consistent code style and conventions is crucial for maintaining a high-quality, readable, and maintainable codebase. This document outlines the key guidelines for the QuantyFinAI Agent project.

## Python Specific Guidelines

### 1. PEP 8 Compliance

All Python code must strictly follow [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/). This includes:

*   **Indentation:** 4 spaces per indentation level.
*   **Line Length:** Maximum 79 characters for code, 99 for docstrings and comments.
*   **Blank Lines:** Use blank lines to separate logical sections of code.
*   **Imports:** Imports should be on separate lines, grouped as standard library, third-party, and local application imports, each group separated by a blank line. Use `isort` for automatic sorting.
*   **Whitespace:** Avoid extraneous whitespace.

### 2. Naming Conventions

*   **Modules:** Short, all-lowercase names. Underscores can be used if it improves readability (e.g., `my_module.py`).
*   **Packages:** Short, all-lowercase names. No underscores (e.g., `my_package/`).
*   **Classes:** CapWords (CamelCase) convention (e.g., `MyClass`).
*   **Functions/Methods:** `snake_case` (all lowercase, words separated by underscores) (e.g., `my_function`, `calculate_total`).
*   **Variables:** `snake_case` (e.g., `my_variable`, `user_name`).
*   **Constants:** ALL_CAPS_WITH_UNDERSCORES (e.g., `MAX_CONNECTIONS`).
*   **Private Members:** Prefix with a single underscore (e.g., `_private_method`).
*   **Type Variables:** CapWords (e.g., `T`, `KT`, `VT`).

### 3. Docstrings and Comments

*   **Docstrings:** All modules, classes, methods, and functions must have docstrings following the [Google Style Python Docstrings](https://google.github.io/styleguide/pyguide.html#pyguide-documenting-code-docstrings) format. Use triple double quotes (`"""Docstring content."""`).
*   **Comments:** Use comments sparingly, primarily for explaining *why* something is done, rather than *what* is done (which should be clear from the code itself). Comments should be up-to-date and relevant.

### 4. Type Hinting

*   All function arguments and return values should be type-hinted using [PEP 484](https://www.python.org/dev/peps/pep-0484/) and [PEP 526](https://www.python.org/dev/peps/pep-0526/) conventions. This improves code readability, enables static analysis, and helps catch errors early.

### 5. Error Handling

*   Use exceptions for error conditions. Avoid returning `None` or special values to indicate errors.
*   Be specific with exception types. Catch specific exceptions rather than broad `Exception` types.
*   Log errors appropriately using the project's logging mechanism.

### 6. Logging

*   Implement a consistent logging strategy across the application. Use Python's built-in `logging` module.
*   Define clear logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
*   Ensure sensitive information is not logged.

## General Best Practices

### 1. Consistency

*   Maintain consistency throughout the codebase. If a pattern is established, follow it.

### 2. Readability

*   Prioritize readability. Code should be easy for other developers (and your future self) to understand.

### 3. Modularity

*   Break down complex problems into smaller, manageable functions and classes. Follow the Single Responsibility Principle.

### 4. Avoid Duplication (DRY - Don't Repeat Yourself)

*   Refactor common logic into reusable functions or classes.

### 5. Configuration

*   Externalize configuration settings (e.g., database credentials, API keys) using environment variables or dedicated configuration files (e.g., `config/settings.py`). Never hardcode sensitive information.

## Automated Formatting and Linting

To enforce these conventions, the following tools will be integrated into the development workflow and CI/CD pipeline:

*   **Black:** An uncompromising Python code formatter.
*   **isort:** A Python utility to sort imports alphabetically and automatically separate them into sections.
*   **Flake8:** A wrapper around PyFlakes, pycodestyle, and McCabe complexity checker for linting.
*   **Mypy:** A static type checker for Python.
