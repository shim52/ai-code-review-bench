# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Code Review Benchmark seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please do NOT:
- Open a public GitHub issue
- Discuss the vulnerability publicly before it's fixed

### Please DO:
- Report via [GitHub Security Advisories](https://github.com/shim52/ai-code-review-bench/security/advisories/new)
- Include steps to reproduce if possible
- Allow us reasonable time to fix the issue before disclosure

### What to expect:
1. **Acknowledgment**: We'll acknowledge receipt within 48 hours
2. **Assessment**: We'll investigate and determine the impact
3. **Fix**: We'll develop and test a fix
4. **Disclosure**: We'll coordinate disclosure with you

### What we promise:
- We will respond to your report promptly
- We will keep you informed about our progress
- We will credit you for the discovery (unless you prefer to remain anonymous)
- We will not take legal action against you if you follow these guidelines

## Security Best Practices for Contributors

When contributing to this project:

### API Keys and Secrets
- Never commit API keys, tokens, or secrets
- Use environment variables for sensitive configuration
- Add sensitive files to `.gitignore`

### Dependencies
- Keep dependencies up to date
- Review dependency licenses
- Report suspicious packages

### Code Review
- All code must be reviewed before merging
- Security-sensitive changes require extra scrutiny
- Use automated security scanning tools

### Testing
- Write tests for security-critical code
- Test edge cases and error conditions
- Validate all inputs

## Security Features

This project includes several security measures:

- **Input validation**: All user inputs are validated
- **Dependency scanning**: Regular updates and security checks
- **Safe defaults**: Secure configuration out of the box
- **Isolated execution**: Tools run in controlled environments

## Acknowledgments

We thank the following individuals for responsibly disclosing vulnerabilities:

* _Your name here_ - [Description of vulnerability]

## Contact

For security concerns, please use [GitHub Security Advisories](https://github.com/shim52/ai-code-review-bench/security/advisories/new).

For general questions, use [GitHub Discussions](https://github.com/shim52/ai-code-review-bench/discussions).