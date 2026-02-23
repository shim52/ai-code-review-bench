---
name: New Tool Integration
about: Propose adding support for a new AI code review tool
title: '[TOOL] Add support for '
labels: new-tool, enhancement
assignees: ''

---

## 🔧 Tool Information

**Tool Name:**
**GitHub Repository:**
**License:**
**Stars:**
**Language:**

## 📋 Integration Checklist

### Prerequisites
- [ ] Tool has a CLI interface or local API
- [ ] Tool is open source or has free tier
- [ ] Tool can analyze git diffs or PRs
- [ ] Tool outputs parseable review comments

### Installation
**How to install the tool:**
```bash
# Installation command(s)
```

### Basic Usage
**How to run the tool on a PR:**
```bash
# Example command
```

## 📊 Output Format
<!-- Describe the tool's output format -->
```json
// Example output
```

## 🎯 Features
<!-- What types of issues can this tool detect? -->
- [ ] Security vulnerabilities
- [ ] Bugs/logic errors
- [ ] Performance issues
- [ ] Code style/quality
- [ ] Documentation issues
- [ ] Other:

## 💡 Why Add This Tool?
<!-- What unique value does this tool bring to the benchmark? -->

## 🛠️ Implementation Plan
<!-- Optional: If you plan to implement this -->
- [ ] Create runner class in `src/code_review_benchmark/runners/`
- [ ] Create parser in `src/code_review_benchmark/parsers/`
- [ ] Add tests in `tests/runners/`
- [ ] Update documentation
- [ ] Test against existing challenges

## 🙋 Volunteer
- [ ] I'm willing to implement this integration
- [ ] I need help with implementation

## 📎 Additional Notes
<!-- Any other relevant information -->