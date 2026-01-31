# Contributing to TSE Analysis

Thank you for your interest in contributing to the TSE Analysis project! We welcome contributions from the community.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tse-analysis.git
   cd tse-analysis
   ```

2. **Set up development environment**
   ```bash
   make dev-install  # or pip install -e .[dev]
   ```

3. **Run tests**
   ```bash
   make test-cov
   ```

## Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Format your code before committing:
```bash
make format
make lint
```

## Testing

- Write tests for new features in the `tests/` directory
- Maintain test coverage above 80%
- Run tests before submitting PRs: `make test-cov`

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add tests
4. Ensure all tests pass: `make test-cov`
5. Format code: `make format`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Commit Message Guidelines

Use clear, descriptive commit messages:
- `feat: add new technical indicator`
- `fix: resolve database connection issue`
- `docs: update API documentation`
- `test: add unit tests for data validation`

## Reporting Issues

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

## Code of Conduct

Please be respectful and constructive in all interactions. We follow a code of conduct to ensure a positive community environment.

## License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.