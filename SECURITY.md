# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported |
| ------- | --------- |
| >= 0.2.0 | Yes       |
| < 0.2.0 | No        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**Do not** open a public GitHub issue for security vulnerabilities.

### How to Report

1. Email the security details to the project maintainer at the email address found in the repository's package metadata, or use GitHub's security advisory feature.

2. Include the following information:
   - Type of vulnerability
   - Full paths of source file(s) related to the vulnerability
   - Location of the affected code (tag/branch/commit or direct URL)
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the issue, including how an attacker might exploit it

### What to Expect

- We will acknowledge receipt of your report within 48 hours
- We will provide a detailed response within 7 days indicating the next steps in handling your report
- We will keep you informed of the progress toward fixing the vulnerability
- After the vulnerability is fixed, we will publicly disclose it (unless you request otherwise)

### Disclosure Policy

We follow a coordinated disclosure process:
- We will not disclose the vulnerability publicly until a fix is available
- We will credit you in the security advisory (unless you prefer to remain anonymous)
- We will work with you to ensure an appropriate disclosure timeline

## Security Considerations

WikiGen handles sensitive information including:
- API keys for LLM providers (stored in system keyring)
- GitHub personal access tokens
- Generated documentation from private repositories

When using WikiGen:
- Never commit API keys or tokens to version control
- Use environment variables or the secure keyring storage provided by the tool
- Review the documentation generated from private repositories before sharing publicly
- Keep the tool and its dependencies up to date

## Security Best Practices

- Use strong, unique API keys for each LLM provider
- Rotate API keys regularly
- Use GitHub tokens with minimal required permissions
- Review generated documentation for sensitive information before publishing
- Run WikiGen in secure environments when processing sensitive codebases

