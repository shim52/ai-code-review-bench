# Challenges

Each challenge is a self-contained test case for AI code review tools.

## Structure

```
challenge-name/
├── challenge.yaml    # Metadata + ground truth issues
├── before/           # Code BEFORE the PR (goes on main branch)
│   └── src/...
└── after/            # Code AFTER the PR (goes on challenge branch)
    └── src/...
```

## Adding a Challenge

1. Copy `_template/` to a new directory with a descriptive kebab-case name
2. Write the "before" code in `before/` — this is the baseline
3. Write the "after" code in `after/` — this is what the PR introduces
4. Define ground truth issues in `challenge.yaml`
5. Run `crb validate-challenges` to check your definition

## Ground Truth Issues

Each issue in `challenge.yaml` represents something a good code reviewer SHOULD find. Fields:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier within the challenge |
| `severity` | Yes | critical, high, medium, low, or info |
| `category` | Yes | Category (security, bug, performance, etc.) |
| `file` | Yes | File path relative to the project root |
| `line_start` | No | Starting line number |
| `line_end` | No | Ending line number |
| `title` | Yes | Short description of the issue |
| `description` | No | Detailed explanation |
| `keywords` | No | Keywords for heuristic matching |

## Tips

- Keep challenges focused: 1-3 issues per challenge
- Include the minimal code needed to demonstrate the issue
- Make the "before" code clean and correct
- Keywords should include both the problem name and the fix approach
