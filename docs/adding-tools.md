# Adding a New Tool

To benchmark a new code review tool, implement a runner and a parser.

## 1. Create a Runner

Create `src/code_review_benchmark/runners/your_tool.py`:

```python
from code_review_benchmark.runners.base import AbstractToolRunner, RunResult
from code_review_benchmark.runners.registry import register_tool

@register_tool
class YourToolRunner(AbstractToolRunner):
    @property
    def name(self) -> str:
        return "your-tool"

    @property
    def version_command(self) -> list[str]:
        return ["your-tool", "--version"]

    def is_available(self) -> bool:
        # Check if the tool is installed
        ...

    def run(self, repo_path, pr_branch, main_branch, model=None) -> RunResult:
        # Execute the tool and capture output
        ...
```

## 2. Create a Parser

Create `src/code_review_benchmark/parsers/your_tool.py`:

```python
from code_review_benchmark.parsers.base import AbstractOutputParser
from code_review_benchmark.models.finding import NormalizedFinding

class YourToolParser(AbstractOutputParser):
    @property
    def tool_name(self) -> str:
        return "your-tool"

    def parse(self, result) -> list[NormalizedFinding]:
        # Parse the tool's output into normalized findings
        ...
```

## 3. Register the Parser

Add your parser to the parser lookup in `src/code_review_benchmark/cli/commands/evaluate.py`.

## 4. Add the Import

Add an import of your runner module in `cli/main.py` so it gets registered.

## 5. Test

```bash
crb setup  # Should show your tool
crb run --tools your-tool --challenges sql-injection-express
```
