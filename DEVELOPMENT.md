# Development Guide

This guide covers the technical details for developing Code Review Benchmark.

## Architecture Overview

```
code-review-benchmark/
├── src/code_review_benchmark/
│   ├── cli/              # CLI commands and interface
│   ├── runners/          # Tool runner implementations
│   ├── parsers/          # Output parsers for each tool
│   ├── evaluation/       # Evaluation logic (heuristic + LLM)
│   ├── models/           # Data models (Pydantic)
│   ├── challenge_repo/   # Git repo builder for challenges
│   └── reports/          # Report generation
├── challenges/           # Test scenarios
├── tests/               # Test suite
└── docs/                # Documentation
```

## Key Components

### 1. Tool Runners (`runners/`)

Each tool has a runner that implements `AbstractToolRunner`:

```python
class YourToolRunner(AbstractToolRunner):
    name = "your-tool"
    version_command = ["your-tool", "--version"]

    def is_available(self) -> bool:
        """Check if tool is installed."""
        # Implementation

    def run(self, repo_path: Path, pr_branch: str, main_branch: str, model: str | None = None) -> RunResult:
        """Execute the tool."""
        # Implementation
```

### 2. Output Parsers (`parsers/`)

Parsers convert tool output to standardized `Finding` objects:

```python
class YourToolParser(BaseParser):
    def parse(self, output: str) -> list[Finding]:
        """Parse tool output into findings."""
        # Implementation
```

### 3. Challenges (`challenges/`)

Each challenge follows this structure:
```
challenge-name/
├── before/           # Code before PR (main branch)
├── after/            # Code after PR (with issues)
└── challenge.yaml    # Ground truth definition
```

### 4. Evaluation (`evaluation/`)

Two-phase evaluation:
1. **Heuristic Matcher**: Fast matching based on file/line/keywords
2. **LLM Judge**: Semantic matching for ambiguous cases

## Development Workflow

### Setting Up

```bash
# Clone and install
git clone <repo>
cd code-review-benchmark
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Verify setup
make setup
```

### Daily Development

```bash
# Before starting work
git pull origin main
make install

# During development
make test          # Run tests
make lint          # Check code style
make format        # Auto-format code

# Before committing
make check         # Run all checks
git add .
git commit -m "feat: your feature"

# Before PR
make pr-check      # Full validation
```

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
# tests/runners/test_your_tool.py
def test_runner_initialization():
    runner = YourToolRunner()
    assert runner.name == "your-tool"

def test_runner_availability():
    runner = YourToolRunner()
    # Mock subprocess calls
    assert runner.is_available() == expected
```

### Integration Tests

Test full pipeline with real challenges:

```python
# tests/integration/test_pipeline.py
def test_full_pipeline():
    # Run tool against challenge
    # Parse output
    # Evaluate against ground truth
    # Assert metrics
```

### Fixtures

Use pytest fixtures for common test data:

```python
@pytest.fixture
def sample_finding():
    return Finding(
        file="test.py",
        line_start=10,
        line_end=15,
        type="bug",
        message="Test issue"
    )
```

## Adding a New Tool

### Step 1: Create Runner

```python
# src/code_review_benchmark/runners/newtool.py
from pathlib import Path
import subprocess
from code_review_benchmark.runners.base import AbstractToolRunner, RunResult

class NewToolRunner(AbstractToolRunner):
    name = "newtool"
    version_command = ["newtool", "--version"]

    def is_available(self) -> bool:
        try:
            subprocess.run(self.version_command, capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def run(self, repo_path: Path, pr_branch: str, main_branch: str, model: str | None = None) -> RunResult:
        # Build command
        cmd = ["newtool", "review", "--repo", str(repo_path)]
        if model:
            cmd.extend(["--model", model])

        # Execute
        result = subprocess.run(cmd, capture_output=True, text=True)

        return RunResult(
            tool=self.name,
            success=result.returncode == 0,
            output_text=result.stdout,
            error=result.stderr,
            return_code=result.returncode
        )
```

### Step 2: Create Parser

```python
# src/code_review_benchmark/parsers/newtool.py
import json
from code_review_benchmark.parsers.base import BaseParser
from code_review_benchmark.models import Finding

class NewToolParser(BaseParser):
    def parse(self, output: str) -> list[Finding]:
        findings = []
        try:
            data = json.loads(output)
            for issue in data.get("issues", []):
                finding = Finding(
                    file=issue["file"],
                    line_start=issue["line"],
                    line_end=issue.get("end_line", issue["line"]),
                    type=self._map_issue_type(issue["type"]),
                    severity=issue.get("severity", "medium"),
                    message=issue["message"]
                )
                findings.append(finding)
        except json.JSONDecodeError:
            # Handle parsing errors
            pass
        return findings

    def _map_issue_type(self, tool_type: str) -> str:
        """Map tool-specific types to our categories."""
        mapping = {
            "vulnerability": "security",
            "error": "bug",
            "slow": "performance",
            "convention": "style"
        }
        return mapping.get(tool_type.lower(), "other")
```

### Step 3: Register Tool

```python
# src/code_review_benchmark/runners/__init__.py
from code_review_benchmark.runners.newtool import NewToolRunner
from code_review_benchmark.runners.registry import register_runner

register_runner(NewToolRunner)
```

### Step 4: Add Tests

```python
# tests/runners/test_newtool.py
import pytest
from unittest.mock import Mock, patch
from code_review_benchmark.runners.newtool import NewToolRunner

def test_newtool_runner():
    runner = NewToolRunner()
    assert runner.name == "newtool"

@patch("subprocess.run")
def test_newtool_execution(mock_run):
    mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")
    runner = NewToolRunner()
    result = runner.run(Path("/tmp/repo"), "pr", "main")
    assert result.success
    assert result.output_text == "output"
```

## Creating a Challenge

### Step 1: Design the Scenario

Choose a realistic issue that tools should detect:
- Security vulnerability (SQL injection, XSS, etc.)
- Logic bug (off-by-one, race condition, etc.)
- Performance issue (N+1 query, inefficient algorithm, etc.)

### Step 2: Create Structure

```bash
mkdir challenges/your-challenge
mkdir challenges/your-challenge/before
mkdir challenges/your-challenge/after
```

### Step 3: Write Code

**before/** - Clean, working code:
```python
# before/app.py
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

**after/** - Code with issues:
```python
# after/app.py
def get_user(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_input}"
    return db.execute(query)
```

### Step 4: Define Ground Truth

```yaml
# challenge.yaml
name: sql-injection-simple
category: Security
difficulty: Easy
description: "Basic SQL injection vulnerability"

issues:
  - file: "app.py"
    line_start: 3
    line_end: 3
    type: "security/sql-injection"
    severity: "critical"
    message: "SQL injection: user input directly concatenated into query"
```

### Step 5: Validate

```bash
crb validate-challenges --challenge your-challenge
```

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Use Rich for Pretty Output

```python
from rich.console import Console
from rich.table import Table

console = Console()
console.print("[bold green]Success![/bold green]")
```

### Inspect Tool Output

```bash
# Run tool manually to see raw output
crb run --tools your-tool --challenges test-challenge --debug
```

### Test Parsers Independently

```python
# Quick parser test
from code_review_benchmark.parsers.your_tool import YourToolParser

parser = YourToolParser()
output = "raw tool output here"
findings = parser.parse(output)
print(findings)
```

## Performance Optimization

### Parallel Execution

Tools run in parallel by default:
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(run_tool, tool) for tool in tools]
```

### Caching

LLM responses can be cached during development:
```python
# Set in .env
CRB_CACHE_LLM_RESPONSES=true
```

### Profiling

```bash
# Profile slow code
python -m cProfile -o profile.stats src/code_review_benchmark/cli/main.py run
python -m pstats profile.stats
```

## Release Process

1. **Update Version**
   ```python
   # pyproject.toml
   version = "0.2.0"
   ```

2. **Update CHANGELOG**
   ```markdown
   ## [0.2.0] - 2024-XX-XX
   ### Added
   - New features...
   ```

3. **Create Release**
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. **Build and Publish**
   ```bash
   make build
   twine upload dist/*
   ```

## Troubleshooting

### Common Issues

**Tool not found:**
```python
# Check PATH and installation
import shutil
shutil.which("tool-name")
```

**Parse errors:**
```python
# Add error handling
try:
    data = json.loads(output)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse: {e}")
    return []
```

**Git issues:**
```python
# Ensure clean repo state
repo.git.reset("--hard")
repo.git.clean("-fd")
```

## Resources

- [Pydantic Docs](https://docs.pydantic.dev/)
- [Typer CLI Docs](https://typer.tiangolo.com/)
- [GitPython Docs](https://gitpython.readthedocs.io/)
- [Rich Docs](https://rich.readthedocs.io/)

## Questions?

Open a discussion or reach out to maintainers!