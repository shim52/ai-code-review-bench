# Adding a New Challenge

## Steps

1. Choose a clear, specific issue to test (SQL injection, missing null check, etc.)
2. Create a new directory under `challenges/` with a descriptive kebab-case name
3. Write minimal "before" code that is correct
4. Write "after" code that introduces the issue(s)
5. Define ground truth in `challenge.yaml`
6. Validate with `crb validate-challenges`

## Guidelines

- **Focused**: Each challenge should test 1-3 related issues
- **Minimal**: Include only the code needed to demonstrate the issue
- **Realistic**: Issues should resemble real-world PR mistakes
- **Language-agnostic where possible**: While code is in a specific language, issues should be universal concepts
- **Clear ground truth**: Keywords should be specific enough to match but general enough to catch different phrasings

## Difficulty Levels

- **Easy**: Obvious issues like hardcoded secrets, console.log left in
- **Medium**: Requires understanding context — missing await, SQL injection
- **Hard**: Requires deeper analysis — N+1 queries, race conditions, subtle logic errors
