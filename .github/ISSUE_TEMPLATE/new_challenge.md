---
name: New Challenge Proposal
about: Propose a new test challenge for the benchmark
title: '[CHALLENGE] '
labels: new-challenge, enhancement
assignees: ''

---

## 🧪 Challenge Overview

**Challenge Name:**
**Category:** <!-- Security | Bug | Performance | Style | Other -->
**Difficulty:** <!-- Easy | Medium | Hard -->
**Programming Language(s):**

## 📝 Description
<!-- Describe what this challenge tests -->

## 🎯 Issues to Detect
<!-- List the specific issues that tools should find -->

1. **Issue 1**
   - Type:
   - Location:
   - Description:

2. **Issue 2**
   - Type:
   - Location:
   - Description:

## 💻 Code Example

### Before (main branch)
```python
# Code before the PR
```

### After (PR branch)
```python
# Code after the PR with issues
```

## ✅ Expected Findings
<!-- What should a good tool detect? -->
- [ ] Finding 1:
- [ ] Finding 2:
- [ ] Finding 3:

## 🎓 Real-World Relevance
<!-- Why is this challenge important? Link to real bugs/CVEs if applicable -->

## 🏷️ Metadata
```yaml
# Proposed challenge.yaml structure
name:
category:
difficulty:
description:
issues:
  - file:
    line_start:
    line_end:
    type:
    severity:
    message:
```

## 🛠️ Implementation Plan
- [ ] Create challenge directory structure
- [ ] Write before/after code
- [ ] Define ground truth in challenge.yaml
- [ ] Validate with `crb validate-challenges`
- [ ] Test with multiple tools

## 🙋 Volunteer
- [ ] I'm willing to implement this challenge
- [ ] I need help with implementation

## 📎 Additional Notes
<!-- Any other relevant information -->