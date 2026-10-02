# Contributing to CareBridge

Thank you for your interest in contributing to CareBridge! Please follow these guidelines to help us maintain a high-quality project.

## How to Contribute

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes.
4. Ensure all tests pass.
5. Submit a pull request.

## Development Setup

1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -e .[dev]`
5. Install pre-commit hooks (if any): `pre-commit install`

## Running Tests

Run the test suite with: `pytest`

## Code Style

We use `ruff` for linting. Please run `ruff check .` before submitting.

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.