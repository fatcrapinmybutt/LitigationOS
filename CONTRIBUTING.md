# Contributing to LitigationOS

Thank you for your interest in contributing to LitigationOS! This project aims to make litigation management accessible through open-source technology.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/LitigationOS.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Install dependencies**: `npm install`
5. **Make your changes** and test thoroughly
6. **Submit a Pull Request**

## Development Setup

### Prerequisites
- Node.js 18+ (20 recommended)
- SQLite 3
- Git

### Quick Start
```bash
cp 00_SYSTEM/deploy/.env.example .env
# Edit .env with your configuration
npm install
npm run dev
```

## Contribution Guidelines

### Code Standards
- Use clear, descriptive variable and function names
- Add JSDoc comments to exported functions
- Keep functions focused — one function, one responsibility
- Write tests for new features

### Commit Messages
Follow conventional commits:
```
feat: add OMEGA score visualization
fix: correct deadline calculation for UTC offsets
docs: update API endpoint documentation
refactor: simplify evidence search query builder
```

### Pull Request Process
1. Update documentation for any changed functionality
2. Add tests covering new code paths
3. Ensure all existing tests pass
4. Update CHANGELOG.md with your changes
5. Request review from at least one maintainer

### What We're Looking For
- **Bug fixes** — Always welcome
- **Documentation** — Improvements, typo fixes, examples
- **Evidence analysis tools** — New analyzers, import formats
- **Timeline features** — Visualization, filtering, export
- **OMEGA scoring** — Algorithm improvements, new scoring dimensions
- **Accessibility** — Making the UI accessible to all users
- **Performance** — Query optimization, caching strategies

### What to Avoid
- Breaking changes without discussion in an issue first
- Large refactors without prior approval
- Adding heavy dependencies without justification
- Changes to security-sensitive code without security review

## Reporting Issues

### Bug Reports
Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Node.js version, OS, browser (if applicable)
- Relevant log output

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternative approaches considered

## Legal

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open a [Discussion](../../discussions) for general questions or an [Issue](../../issues) for bugs and feature requests.
