# Changelog

All notable changes to Code Review Benchmark will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-26

### Added
- Gemini Reviewer: Google Gemini 2.5 Pro as a built-in reviewer
- Python challenges: `sql-injection-django` and `insecure-deserialization`
- Methodology section in the dashboard UI explaining scoring and evaluation
- Metric tooltips (F1, Precision, Recall) in the dashboard

### Changed
- **Judge model switched from GPT-4o to Claude Sonnet 4** to reduce same-provider scoring bias (most tools use OpenAI)
- `CRB_JUDGE_MODEL` now defaults to `claude-sonnet-4-20250514`
- Dashboard UI updated with methodology explanation and judge disclosure
- README updated with correct repository URLs and Gemini reviewer

### Fixed
- Broken placeholder URLs in README (`yourusername` → `shim52`)

## [0.1.0] - 2024-02-23

### Added
- Initial release of Code Review Benchmark
- Support for AI code review tools: PR-Agent, Shippie, OpenAI Reviewer, Claude Reviewer
- 10 challenge scenarios covering security, bugs, performance, and architecture
- Two-phase evaluation: heuristic pre-matching + LLM-as-judge
- One-to-one finding deduplication in matcher
- CLI interface with commands for running, evaluating, and reporting
- Dashboard site with leaderboard, challenges, tools, matrix, and breakdown views
- Comprehensive documentation and contribution guidelines

## Links
- [1.0.0]: https://github.com/shim52/ai-code-review-bench/compare/v0.1.0...v1.0.0
- [0.1.0]: https://github.com/shim52/ai-code-review-bench/releases/tag/v0.1.0