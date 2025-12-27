# Contributing

Thank you for your interest in contributing to WikiGen.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/usesalt/wikigen.git
cd wikigen
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
# Or if using requirements files:
pip install -r requirements-dev.txt
```

3. Install in editable mode:
```bash
pip install -e .
```

## Development Workflow

1. Create a branch from `main` for your changes:
```bash
git checkout -b your-feature-name
```

2. Make your changes following the existing code style.

3. Run tests to ensure everything works:
```bash
pytest
```

4. Format your code with Black:
```bash
black .
```

5. Commit your changes with clear, descriptive commit messages.

6. Push your branch and open a pull request.

## Code Style

- Follow PEP 8 guidelines.
- Use Black for code formatting (line length: 88 characters).
- Use type hints where appropriate.
- Keep functions focused and reasonably sized.

## Testing

- Write tests for new features and bug fixes.
- Ensure all tests pass before submitting a PR.
- Tests should be placed in the `tests/` directory, mirroring the source structure.

## Pull Request Guidelines

- Provide a clear description of what your PR does and why.
- Reference any related issues.
- Ensure your PR builds and all tests pass.
- Keep PRs focused - one feature or fix per PR.

## Questions?

If you have questions or need help, feel free to open an issue on GitHub.

