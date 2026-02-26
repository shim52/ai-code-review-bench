# Contributing to Code Review Benchmark

First off, thank you for considering contributing to Code Review Benchmark! 🎉

This project aims to create a fair, reproducible way to evaluate AI code review tools. Every contribution, whether it's a new tool integration, a challenging test case, or a documentation fix, helps make the ecosystem better.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Adding a New Tool](#adding-a-new-tool)
- [Creating Challenges](#creating-challenges)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Community](#community)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to:
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

Not sure where to start? Here are some good first issues:

- **Good First Issue** - Look for issues labeled `good-first-issue`
- **Documentation** - Help improve our docs (always needed!)
- **Add a Tool** - Integrate a new AI code review tool
- **Create a Challenge** - Design a new test case

Check our [issue tracker](https://github.com/shim52/ai-code-review-bench/issues) for current tasks.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- OpenAI API key (for evaluation and most tools)

### Installation

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub, then:
   git clone https://github.com/YOUR-USERNAME/ai-code-review-bench.git
   cd ai-code-review-bench
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

5. **Verify installation**
   ```bash
   crb setup
   pytest tests/ -v
   ```

## How to Contribute

### 🐛 Reporting Bugs

Before creating a bug report, please check existing issues. When you create a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or error messages

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

### 💡 Suggesting Features

Feature suggestions are welcome! Please:

- Check if the feature has already been suggested
- Provide a clear use case
- Explain how it benefits the project
- Consider if you're willing to implement it

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

### 🔧 Adding a New Tool

To add support for a new AI code review tool:

1. **Create the runner class** in `src/code_review_benchmark/runners/`
   ```python
   from code_review_benchmark.runners.base import BaseRunner

   class YourToolRunner(BaseRunner):
       name = "your-tool"
       version_command = ["your-tool", "--version"]

       def run_review(self, repo_path: Path) -> str:
           # Implementation here
           pass
   ```

2. **Create the parser** in `src/code_review_benchmark/parsers/`
   ```python
   from code_review_benchmark.parsers.base import BaseParser

   class YourToolParser(BaseParser):
       def parse(self, output: str) -> list[Finding]:
           # Parse tool output into standardized findings
           pass
   ```

3. **Register the tool** in `runners/__init__.py`

4. **Add tests** in `tests/runners/test_your_tool.py`

5. **Document it** in `docs/adding-tools.md`

See our [detailed guide](docs/adding-tools.md) for more information.

### 🧪 Creating Challenges

Good challenges are:
- **Realistic** - Based on actual code review issues
- **Clear** - Have unambiguous ground truth
- **Diverse** - Cover different types of issues

To create a challenge:

1. **Create challenge directory** in `challenges/your-challenge-name/`
   ```
   challenges/your-challenge-name/
   ├── before/        # Code before the PR
   ├── after/         # Code after the PR
   └── challenge.yaml # Ground truth definition
   ```

2. **Define ground truth** in `challenge.yaml`
   ```yaml
   name: your-challenge-name
   category: Security|Bug|Performance|Style
   difficulty: Easy|Medium|Hard
   description: "Brief description"
   issues:
     - file: "path/to/file.py"
       line_start: 10
       line_end: 15
       type: "security/sql-injection"
       severity: "high"
       message: "SQL injection vulnerability"
   ```

3. **Validate your challenge**
   ```bash
   crb validate-challenges --challenge your-challenge-name
   ```

4. **Test with multiple tools**
   ```bash
   crb run --challenges your-challenge-name
   ```

See [Adding Challenges Guide](docs/adding-challenges.md) for detailed instructions.

## Pull Request Process

### Before Submitting

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   # Run tests
   pytest tests/ -v

   # Check code style
   ruff check src/
   ruff format src/

   # Validate challenges (if modified)
   crb validate-challenges
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add support for NewTool runner

   - Implement NewTool runner class
   - Add parser for NewTool output format
   - Include comprehensive tests"
   ```

### Submitting the PR

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use a clear, descriptive title
   - Reference any related issues
   - Describe what changes you made and why
   - Include screenshots if relevant
   - Check all boxes in the PR template

3. **Respond to feedback**
   - Be responsive to review comments
   - Push additional commits to address feedback
   - Don't force-push during review unless requested

### After Merge

- Delete your feature branch
- Pull the latest main branch
- Consider tackling another issue!

## Style Guidelines

### Python Code Style

We use `ruff` for linting and formatting:

```python
# Good
def calculate_metrics(
    predictions: list[Finding],
    ground_truth: list[GroundTruth],
) -> Metrics:
    """Calculate precision, recall, and F1 score.

    Args:
        predictions: List of predicted findings
        ground_truth: List of actual issues

    Returns:
        Metrics object with precision, recall, F1
    """
    # Implementation
```

### Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or fixes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

### Documentation

- Use clear, concise language
- Include code examples where helpful
- Keep README and docs in sync
- Document all public APIs

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=code_review_benchmark

# Run specific test file
pytest tests/evaluation/test_matcher.py

# Run with verbose output
pytest tests/ -v
```

### Writing Tests

- Test both happy paths and edge cases
- Use descriptive test names
- Mock external dependencies
- Aim for >80% coverage on new code

Example:
```python
def test_parser_handles_empty_output():
    """Parser should return empty list for empty output."""
    parser = YourToolParser()
    result = parser.parse("")
    assert result == []
```

## Community

### Getting Help

- 💬 [GitHub Discussions](https://github.com/shim52/ai-code-review-bench/discussions) - Ask questions
- 🐛 [Issue Tracker](https://github.com/shim52/ai-code-review-bench/issues) - Report bugs

### Recognition

Contributors are recognized in:
- The README contributors section
- Release notes
- Our [Contributors page](https://github.com/shim52/ai-code-review-bench/contributors)

## Questions?

Don't hesitate to ask! Open a discussion or reach out to the maintainers. We're here to help you contribute successfully.

---

Thank you for contributing to Code Review Benchmark! Your efforts help make AI code review tools better for everyone. 🚀