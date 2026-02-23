# 🎯 Code Review Benchmark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/yourusername/code-review-benchmark/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

A reproducible benchmark suite that evaluates open source AI code review tools against curated pull requests with known issues.

## 🤔 Why This Project?

There's no standardized way to compare AI code review tools. Developers pick tools based on star counts and marketing, not measured performance. This project runs tools against PRs with known issues and scores how well each tool finds them.

### Key Features
- 📊 **Objective Metrics**: Precision, recall, and F1 scores for each tool
- 🔄 **Reproducible**: Consistent test suite across all tools
- 🎭 **Real-World Scenarios**: Challenges based on common code review issues
- 🤖 **LLM-as-Judge**: Advanced semantic matching for accurate evaluation
- 📈 **Extensible**: Easy to add new tools and challenges

## Tools Benchmarked (v1)

| Tool | Stars | License | Install |
|------|-------|---------|---------|
| [PR-Agent](https://github.com/qodo-ai/pr-agent) | 10.3k | AGPL-3.0 | `pip install pr-agent` |
| [Shippie](https://github.com/mattzcarey/shippie) | 2.3k | MIT | `npx shippie` |
| [AI Review](https://github.com/Nikita-Filonov/ai-review) | 269 | Apache-2.0 | `pip install xai-review` |

## Quick Start

```bash
# Install
pip install -e .

# Verify setup
crb setup

# Run all tools against all challenges
crb run

# Evaluate results
crb evaluate --run-dir results/latest

# Generate report
crb report --run-dir results/latest
```

## How It Works

1. **Challenges** are stored as `before/` and `after/` directories with a `challenge.yaml` defining ground truth issues
2. The framework builds a temporary git repo from each challenge (before → main branch, after → challenge branch)
3. Each tool runs in local/CLI mode against the repo and produces review output
4. Output is parsed into a normalized finding format
5. Findings are matched against ground truth using heuristic matching + LLM-as-judge
6. Precision, recall, and F1 scores are calculated and reported

## Challenges

| Challenge | Category | Difficulty | Issues |
|-----------|----------|------------|--------|
| `sql-injection-express` | Security | Medium | 2 |
| `hardcoded-secrets` | Security | Easy | 3 |
| `missing-await-async` | Bug | Medium | 3 |
| `off-by-one-pagination` | Bug | Medium | 2 |
| `n-plus-one-query` | Performance | Hard | 2 |

## CLI Commands

```bash
crb run                                      # Run all tools × all challenges
crb run --tools pr-agent,shippie             # Run specific tools
crb run --challenges sql-injection-express   # Run specific challenge
crb run --runs 5                             # 5 runs per pair (default: 3)
crb evaluate --run-dir results/latest        # Score results
crb evaluate --skip-llm                      # Heuristic-only scoring
crb report --run-dir results/latest          # Generate markdown report
crb setup                                    # Check tool availability
crb list-tools                               # List registered tools
crb list-challenges                          # List all challenges
crb validate-challenges                      # Validate challenge definitions
```

## Configuration

Set via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required for LLM judge and most tools |
| `CRB_JUDGE_MODEL` | `gpt-4o` | Model used for LLM-as-judge evaluation |
| `CRB_TOOL_MODEL` | — | Model passed to review tools |
| `CRB_NUM_RUNS` | `3` | Default runs per tool/challenge pair |

## Evaluation Methodology

**Phase 1 — Heuristic pre-matching**: File path overlap (40%), line proximity (20%), keyword overlap (40%).

**Phase 2 — LLM-as-judge**: For each heuristic candidate, an LLM judges semantic equivalence. Final score = 40% heuristic + 60% LLM confidence.

**Scoring**: Standard precision, recall, F1. Multiple runs report mean ± stddev to account for LLM non-determinism.

See `docs/evaluation-methodology.md` for details.

## 🚀 Getting Started for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/code-review-benchmark.git
cd code-review-benchmark

# Install in development mode
pip install -e ".[dev]"

# Run tests to ensure everything works
pytest tests/ -v

# Check code style
ruff check src/

# Validate any new challenges
crb validate-challenges
```

## 🤝 Contributing

We welcome contributions from the community! Whether you're adding a new tool, creating challenges, or improving the evaluation logic, your help makes this project better.

### Quick Contribution Ideas
- 🔧 **Add a new AI code review tool** - See [Adding Tools Guide](docs/adding-tools.md)
- 🧪 **Create new challenge scenarios** - See [Adding Challenges Guide](docs/adding-challenges.md)
- 🐛 **Report or fix bugs** - [Open an issue](https://github.com/yourusername/code-review-benchmark/issues)
- 📖 **Improve documentation** - Every bit helps!

Check out our [Contributing Guide](.github/CONTRIBUTING.md) for detailed instructions.

## 👥 Community

- **Questions?** [Open a discussion](https://github.com/yourusername/code-review-benchmark/discussions)
- **Found a bug?** [Report it here](https://github.com/yourusername/code-review-benchmark/issues/new?template=bug_report.md)
- **Have an idea?** [Suggest a feature](https://github.com/yourusername/code-review-benchmark/issues/new?template=feature_request.md)

## 📜 License

MIT - See [LICENSE](LICENSE) for details.
