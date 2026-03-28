---
name: FORGE-GIT-TEMPORAL
description: >-
  Omega-class fused superskill that treats the entire git history as a queryable
  temporal database. Combines semantic commit intelligence, branch topology
  optimization, monorepo orchestration, conflict precognition, hook enforcement,
  CI/CD pipeline synthesis, and release orchestration into a unified temporal
  codebase omniscience engine. Navigate any point in time, understand WHY changes
  happened, predict merge conflicts before they occur, auto-generate releases
  across monorepo packages, and synthesize complete CI/CD pipelines that enforce
  the entire workflow from commit to deploy.
category: engineering
version: "1.0.0"
triggers:
  - git history
  - conventional commits
  - branch strategy
  - monorepo management
  - merge conflict
  - git hooks
  - ci/cd pipeline
  - release management
  - changelog generation
  - git bisect
  - github actions
  - semantic versioning
metadata:
  tier: FORGE
  fused_skills: 8
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: "2026-03-27"
  forge_class: domain-mastery
  emergent_capability: >-
    Temporal Codebase Omniscience — treats git history as a queryable time-series
    database enabling predictive conflict detection, causal change tracing,
    automated multi-package releases, and self-enforcing quality pipelines that
    span the entire lifecycle from keystroke to production deploy.
---

# ⏳ FORGE-GIT-TEMPORAL
### (Ω-Δ99)

> **A FORGE-class superskill that fuses 8 discrete git/CI/CD skills into a
> unified temporal codebase intelligence engine.**
>
> | Property | Value |
> |----------|-------|
> | **Tier** | FORGE (Ω-Δ99 Domain Mastery) |
> | **Domain** | Git Version Control · CI/CD · Release Engineering |
> | **Scope** | Full lifecycle: commit → branch → test → merge → release → deploy |
> | **Emergent** | Temporal Codebase Omniscience — no single skill can achieve this alone |

---

## Forged from 8 Skills

| # | Source Skill | Core Capability | Module |
|---|-------------|-----------------|--------|
| 1 | `git-archaeology` | Bisect, blame, reflog, history surgery, forensic analysis | **GT1** |
| 2 | `git-conventional-commits` | Semantic commit messages, changelogs, version bumping | **GT2** |
| 3 | `git-flow-master` | Branching strategies, release management, hotfix workflows | **GT3** |
| 4 | `git-monorepo-orchestrator` | Nx, Turborepo, Lerna workspace management | **GT4** |
| 5 | `git-conflict-resolver` | Merge/rebase strategies, conflict resolution patterns | **GT5** |
| 6 | `git-hooks-automation` | Pre-commit, pre-push, commit-msg hooks, lint-staged | **GT6** |
| 7 | `github-actions-master` | CI/CD workflows, reusable actions, matrix builds | **GT7** |
| 8 | `changelog-release-engine` | Release notes, CHANGELOG.md, semantic versioning | **GT8** |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FORGE-GIT-TEMPORAL  (Ω-Δ99)                      │
│               Temporal Codebase Omniscience Engine                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │   GT1    │  │   GT2    │  │   GT3    │  │   GT4    │           │
│  │ Temporal │  │ Semantic │  │ Branch   │  │ Monorepo │           │
│  │ Navig.   │──│ Commit   │──│ Topology │──│ Orchestr │           │
│  │ Engine   │  │ Intel.   │  │ Optim.   │  │ ation    │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │              │              │              │                 │
│       ▼              ▼              ▼              ▼                 │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │              TEMPORAL FUSION CORE                        │       │
│  │   GT1→GT2: Blame + semantic context = causal tracing     │       │
│  │   GT2→GT8: Commits feed changelogs feed releases         │       │
│  │   GT3→GT5: Branch topology predicts conflict zones       │       │
│  │   GT4→GT7: Affected packages drive CI matrix             │       │
│  │   GT6→GT2: Hooks enforce commit conventions              │       │
│  │   GT7→GT8: CI validates then triggers release            │       │
│  └─────────────────────────────────────────────────────────┘       │
│       │              │              │              │                 │
│       ▼              ▼              ▼              ▼                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │   GT5    │  │   GT6    │  │   GT7    │  │   GT8    │           │
│  │ Conflict │  │ Hook     │  │ CI/CD    │  │ Release  │           │
│  │ Precog.  │──│ Enforce  │──│ Pipeline │──│ Orchestr │           │
│  │          │  │ Matrix   │  │ Synth.   │  │ ation    │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                     │
│  ═══════════════════ EMERGENT LAYER ══════════════════════          │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  TEMPORAL CODEBASE OMNISCIENCE                           │       │
│  │  · Query any point in history with semantic context      │       │
│  │  · Predict conflicts before branches diverge             │       │
│  │  · Auto-release across monorepo with full provenance     │       │
│  │  · Self-enforcing quality pipeline from commit to deploy │       │
│  └─────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## GT1: Temporal Navigation Engine

**Purpose:** Transform git's raw history primitives (bisect, blame, reflog, log)
into a structured time-travel interface for forensic codebase analysis.

**Design Pattern:** Temporal Query Facade — wraps low-level git plumbing commands
behind intent-driven queries: "when did this behavior change?", "who introduced
this pattern?", "what was the state at timestamp T?"

### Core Commands

```bash
# ── Forensic blame with semantic context ──
# Track a function through every rename and move
git log --follow --diff-filter=M -p -- src/auth/login.ts

# Blame with ignore-revs for formatting commits
echo "abc123 # prettier migration" >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs
git blame --ignore-revs-file=.git-blame-ignore-revs src/auth/login.ts

# ── Time-travel bisect with automation ──
# Find the exact commit that broke a test
git bisect start
git bisect bad HEAD
git bisect good v2.3.0
git bisect run npm test -- --testPathPattern="auth.spec"
# Bisect will binary-search ~10 commits in seconds

# ── Reflog forensics: recover "lost" work ──
# Show every HEAD movement in the last 48 hours
git reflog --since="48 hours ago" --format="%h %gd %gs %s"

# Recover a deleted branch
git reflog | grep "checkout: moving from feature/deleted-branch"
git checkout -b recovered-branch HEAD@{5}

# ── History surgery (interactive rebase) ──
# Squash the last 5 commits into a semantic commit
git rebase -i HEAD~5
# In the editor: pick first, squash rest, write conventional message

# ── Advanced log queries: temporal windows ──
# All changes to auth module in Q4 2025
git log --after="2025-10-01" --before="2026-01-01" \
  --format="%h %as %an: %s" -- src/auth/

# Changes by a specific author touching specific files
git log --author="alice" --format="%h %s" -- "*.test.ts"

# ── Diff across time: snapshot comparison ──
# Compare current auth module to 6 months ago
git diff HEAD@{6.months.ago}..HEAD -- src/auth/

# Show files changed between two releases
git diff --stat v2.0.0..v3.0.0
```

### Temporal Query Patterns

```bash
# ── "When did this line appear?" ──
git log -S "DANGEROUS_PATTERN" --format="%h %as %an: %s" --all

# ── "What commit introduced this regex?" ──
git log -G "useEffect\(\s*\(\)\s*=>" --format="%h %as %an: %s" -- "*.tsx"

# ── "Show the evolution of a function" ──
git log -L :functionName:src/utils.ts

# ── "What was the project state on release day?" ──
git stash
git checkout $(git rev-list -n 1 --before="2025-12-01" main)
# Inspect, then return
git checkout main && git stash pop

# ── Pickaxe: find when a string count changed ──
git log -S "TODO" --diff-filter=A --format="%h %as: %s"
```

### Integration Points

- **→ GT2:** Blame output enriched with conventional commit type (feat/fix/refactor)
- **→ GT5:** Historical merge conflict zones inform conflict precognition
- **→ GT8:** Release-to-release diffs feed changelog generation

---

## GT2: Semantic Commit Intelligence

**Purpose:** Enforce and leverage the Conventional Commits specification to create
machine-readable commit history that powers automated changelogs, version bumps,
and semantic analysis.

**Design Pattern:** Commit DSL Parser — every commit message becomes a structured
record with type, scope, breaking-change flag, and body that downstream modules
(GT6, GT7, GT8) can query programmatically.

### Conventional Commit Format

```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types & Semantic Mapping

```bash
# ── Feature commits → trigger MINOR version bump ──
git commit -m "feat(auth): add OAuth2 PKCE flow for mobile clients

Implements RFC 7636 code verifier/challenge for native apps.
Supports both S256 and plain challenge methods.

Closes #1234"

# ── Fix commits → trigger PATCH version bump ──
git commit -m "fix(api): prevent race condition in token refresh

Multiple concurrent requests could trigger parallel refresh calls.
Added mutex lock around the refresh token exchange.

Fixes #5678"

# ── Breaking changes → trigger MAJOR version bump ──
git commit -m "feat(api)!: migrate from REST to GraphQL endpoint

BREAKING CHANGE: The /api/v2/users endpoint is removed.
Use the GraphQL endpoint at /graphql instead.
Migration guide: docs/migration-v3.md"

# ── Other types (no version bump, appear in changelog) ──
git commit -m "perf(db): add composite index on users(email, tenant_id)"
git commit -m "refactor(auth): extract token validation to middleware"
git commit -m "docs(api): add OpenAPI 3.1 specification"
git commit -m "test(auth): add integration tests for PKCE flow"
git commit -m "ci: add Node 22 to test matrix"
git commit -m "build(deps): upgrade TypeScript to 5.7"
git commit -m "chore: update .editorconfig for new team standards"
```

### Commit Parsing Script

```bash
#!/usr/bin/env bash
# parse-commits.sh — Extract structured data from conventional commits
# Used by GT8 (Release Orchestration) for changelog generation

parse_conventional_commit() {
  local msg="$1"
  local type scope breaking description

  if [[ "$msg" =~ ^([a-z]+)(\(([^)]+)\))?(!)?\:\ (.+)$ ]]; then
    type="${BASH_REMATCH[1]}"
    scope="${BASH_REMATCH[3]}"
    breaking="${BASH_REMATCH[4]}"
    description="${BASH_REMATCH[5]}"

    echo "TYPE=$type"
    echo "SCOPE=$scope"
    echo "BREAKING=${breaking:+true}"
    echo "DESC=$description"
  fi
}

# Parse all commits since last tag
last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
range="${last_tag:+$last_tag..}HEAD"

git log "$range" --format="%s" | while read -r line; do
  parse_conventional_commit "$line"
  echo "---"
done
```

### Commitlint Configuration

```javascript
// commitlint.config.js — Enforced by GT6 hooks
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'perf', 'refactor', 'docs',
      'test', 'ci', 'build', 'chore', 'revert', 'style'
    ]],
    'scope-enum': [1, 'always', [
      'auth', 'api', 'db', 'ui', 'core', 'deps', 'config'
    ]],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
    'header-max-length': [2, 'always', 100],
  },
};
```

### Integration Points

- **→ GT6:** Commit-msg hook validates conventional format before accepting
- **→ GT7:** CI workflow rejects PRs with non-conforming commit messages
- **→ GT8:** Commit types drive automatic version bumping and changelog sections
- **← GT1:** Semantic types enrich blame/log forensic output

---

## GT3: Branch Topology Optimizer

**Purpose:** Select and enforce the optimal branching strategy for the project's
size, team structure, and release cadence. Supports git-flow, trunk-based,
GitHub Flow, and release trains.

**Design Pattern:** Strategy Selector — analyzes project metadata (team size,
deploy frequency, monorepo vs polyrepo) and recommends the optimal topology,
then generates branch protection rules and merge policies.

### Strategy Decision Matrix

```
┌──────────────────────┬────────────┬─────────────┬───────────────┐
│ Factor               │ Git-Flow   │ Trunk-Based │ Release Train │
├──────────────────────┼────────────┼─────────────┼───────────────┤
│ Team size            │ 5-20       │ 2-50+       │ 10-100+       │
│ Deploy frequency     │ Weekly+    │ Daily/CD    │ Scheduled     │
│ Release discipline   │ High       │ Medium      │ Very High     │
│ Feature flags needed │ No         │ Yes         │ Yes           │
│ Hotfix complexity    │ Medium     │ Low         │ High          │
│ Best for             │ Versioned  │ SaaS/Web    │ Mobile/OS     │
│                      │ software   │ apps        │ releases      │
└──────────────────────┴────────────┴─────────────┴───────────────┘
```

### Git-Flow Implementation

```bash
# ── Initialize git-flow ──
git flow init -d
# Creates: main, develop, feature/, release/, hotfix/ prefixes

# ── Feature workflow ──
git flow feature start user-dashboard
# ... develop ...
git flow feature finish user-dashboard
# Merges to develop, deletes feature branch

# ── Release workflow ──
git flow release start 2.1.0
# Bump version, update changelog
npm version minor --no-git-tag-version
git add package.json && git commit -m "chore(release): bump to 2.1.0"
git flow release finish 2.1.0
# Merges to main AND develop, creates tag

# ── Hotfix workflow (emergency production fix) ──
git flow hotfix start 2.0.1
git commit -m "fix(auth): patch XSS vulnerability in login form"
git flow hotfix finish 2.0.1
# Merges to main AND develop, creates tag
```

### Trunk-Based Development

```bash
# ── Short-lived feature branches (< 2 days) ──
git checkout -b feat/add-search main
# Small, focused changes with feature flags
git commit -m "feat(search): add search API behind ENABLE_SEARCH flag"
git push origin feat/add-search
# Create PR → squash merge → delete branch

# ── Release branches (cut from trunk) ──
git checkout -b release/2.1 main
# Only cherry-pick critical fixes
git cherry-pick abc123  # fix: patch auth bypass
git tag v2.1.0
git push origin v2.1.0
```

### Branch Protection Rules

```bash
# ── GitHub CLI: configure branch protection ──
gh api repos/{owner}/{repo}/branches/main/protection -X PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["ci/test", "ci/lint", "ci/build"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

### Integration Points

- **→ GT5:** Branch topology informs which merges are likely to conflict
- **→ GT7:** CI workflows adapt to branch type (feature=test, release=test+publish)
- **→ GT8:** Release branch triggers version bump + changelog generation
- **← GT4:** Monorepo package graph influences branch strategy

---

## GT4: Monorepo Orchestration

**Purpose:** Manage multi-package workspaces with intelligent affected-package
detection, dependency-aware build ordering, and cross-package version coordination.

**Design Pattern:** Dependency Graph Executor — builds a DAG of packages, detects
which are affected by changes, and orchestrates builds/tests/releases in
topological order.

### Nx Workspace Configuration

```json
// nx.json — Nx workspace configuration
{
  "targetDefaults": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["production", "^production"],
      "cache": true
    },
    "test": {
      "inputs": ["default", "^production", "{workspaceRoot}/jest.config.ts"],
      "cache": true
    },
    "lint": {
      "inputs": ["default", "{workspaceRoot}/.eslintrc.json"],
      "cache": true
    }
  },
  "namedInputs": {
    "default": ["{projectRoot}/**/*", "sharedGlobals"],
    "production": ["default", "!{projectRoot}/**/*.spec.ts"],
    "sharedGlobals": ["{workspaceRoot}/tsconfig.base.json"]
  },
  "defaultBase": "main"
}
```

### Turborepo Pipeline

```json
// turbo.json — Turborepo pipeline configuration
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["tsconfig.json"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"],
      "inputs": ["src/**", "tsconfig.json"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"],
      "inputs": ["src/**", "tests/**", "jest.config.*"]
    },
    "lint": {
      "outputs": []
    },
    "deploy": {
      "dependsOn": ["build", "test", "lint"],
      "outputs": []
    }
  }
}
```

### Affected Package Detection

```bash
# ── Nx: detect affected packages from git diff ──
# Against main branch
npx nx affected --target=test --base=main --head=HEAD
npx nx affected --target=build --base=main --head=HEAD

# Against last successful CI commit
npx nx affected --target=test --base=origin/main~1 --head=HEAD

# Visualize the dependency graph
npx nx graph --affected --base=main

# ── Turborepo: filter by changed packages ──
npx turbo run test --filter='...[HEAD^1]'
npx turbo run build --filter='./packages/*'

# ── Manual affected detection with git ──
# Find which packages have changes since last tag
changed_files=$(git diff --name-only $(git describe --tags --abbrev=0)..HEAD)
affected_packages=$(echo "$changed_files" | \
  grep -oP 'packages/[^/]+' | sort -u)
echo "Affected: $affected_packages"
```

### Workspace Package Graph Script

```bash
#!/usr/bin/env bash
# detect-affected.sh — Used by GT7 CI to build only what changed

set -euo pipefail

BASE_REF="${1:-origin/main}"
HEAD_REF="${2:-HEAD}"

echo "═══ Detecting affected packages ═══"
echo "Base: $BASE_REF"
echo "Head: $HEAD_REF"

changed=$(git diff --name-only "$BASE_REF".."$HEAD_REF")

declare -A affected
while IFS= read -r file; do
  if [[ "$file" == packages/* ]]; then
    pkg=$(echo "$file" | cut -d/ -f2)
    affected[$pkg]=1
  fi
done <<< "$changed"

echo "Affected packages: ${!affected[*]}"

# Output as JSON for CI matrix
echo -n '{"packages":['
first=true
for pkg in "${!affected[@]}"; do
  $first || echo -n ','
  echo -n "\"$pkg\""
  first=false
done
echo ']}'
```

### Integration Points

- **→ GT7:** Affected packages generate dynamic CI matrix (build only what changed)
- **→ GT8:** Per-package changelogs and independent version bumps
- **→ GT5:** Cross-package dependency changes are highest conflict risk
- **← GT3:** Branch strategy adapts to monorepo (release branches per package)

---

## GT5: Conflict Precognition

**Purpose:** Predict merge conflicts before they happen, provide resolution
strategies, and auto-resolve trivial conflicts using pattern matching.

**Design Pattern:** Predictive Merge Oracle — analyzes branch divergence,
file-level change overlap, and historical conflict patterns to warn developers
before they attempt merges.

### Conflict Prediction

```bash
# ── Predict conflicts before merging ──
# Dry-run merge to detect conflicts without modifying worktree
predict_conflicts() {
  local source="$1" target="${2:-main}"

  echo "═══ Conflict Prediction: $source → $target ═══"

  # Find files modified in both branches
  local base=$(git merge-base "$target" "$source")
  local target_files=$(git diff --name-only "$base".."$target")
  local source_files=$(git diff --name-only "$base".."$source")

  # Intersection = potential conflict zones
  local overlap=$(comm -12 \
    <(echo "$target_files" | sort) \
    <(echo "$source_files" | sort))

  if [[ -z "$overlap" ]]; then
    echo "✅ No overlapping files — clean merge predicted"
    return 0
  fi

  echo "⚠️  Overlapping files detected:"
  echo "$overlap" | while read -r f; do
    echo "  · $f"
    # Check if same lines were modified
    local target_lines=$(git diff "$base".."$target" -- "$f" | \
      grep -oP '^\@\@ -\K[0-9]+' | head -5)
    local source_lines=$(git diff "$base".."$source" -- "$f" | \
      grep -oP '^\@\@ -\K[0-9]+' | head -5)
    local line_overlap=$(comm -12 \
      <(echo "$target_lines" | sort -n) \
      <(echo "$source_lines" | sort -n))
    if [[ -n "$line_overlap" ]]; then
      echo "    🔴 HIGH RISK — same line ranges modified"
    else
      echo "    🟡 LOW RISK — different regions of same file"
    fi
  done

  # Attempt merge in temporary index
  git merge-tree "$base" "$target" "$source" 2>/dev/null | \
    grep -c "^<<<<<<<" && echo "Predicted conflict markers found" || \
    echo "No conflict markers in merge-tree output"
}

predict_conflicts "feature/auth-rewrite"
```

### Auto-Resolution Strategies

```bash
# ── Strategy 1: Lock file auto-resolution ──
# package-lock.json, yarn.lock conflicts: always regenerate
echo 'package-lock.json merge=ours' >> .gitattributes
echo 'yarn.lock merge=ours' >> .gitattributes

# After merge conflict on lock files:
git checkout --theirs package-lock.json
npm install  # Regenerate from merged package.json
git add package-lock.json

# ── Strategy 2: Auto-generated file resolution ──
echo '*.generated.ts merge=ours' >> .gitattributes
echo 'schema.graphql merge=union' >> .gitattributes

# ── Strategy 3: Rerere — remember resolutions ──
git config rerere.enabled true
git config rerere.autoupdate true
# Git now records conflict resolutions and auto-applies them next time

# ── Strategy 4: Ours/theirs for specific paths ──
# During a conflict, resolve entire files:
git checkout --ours src/generated/api-types.ts
git checkout --theirs CHANGELOG.md
git add src/generated/api-types.ts CHANGELOG.md
```

### Merge Strategy Selection

```bash
# ── Choose the right merge strategy ──
select_merge_strategy() {
  local source="$1" target="$2"
  local commits_behind=$(git rev-list --count "$target".."$source")
  local commits_ahead=$(git rev-list --count "$source".."$target")

  echo "Source is $commits_behind behind, $commits_ahead ahead of target"

  if [[ $commits_behind -eq 0 ]]; then
    echo "→ Fast-forward merge (linear history)"
    git merge --ff-only "$source"
  elif [[ $commits_behind -le 3 ]]; then
    echo "→ Rebase then fast-forward (clean history)"
    git rebase "$target" "$source"
    git checkout "$target"
    git merge --ff-only "$source"
  else
    echo "→ Merge commit (preserve branch context)"
    git merge --no-ff "$source" \
      -m "merge($source): integrate into $target"
  fi
}
```

### Integration Points

- **← GT3:** Branch topology determines which merges to monitor
- **← GT1:** Historical conflict frequency data from past merges
- **→ GT6:** Pre-push hook runs conflict prediction before pushing
- **→ GT7:** CI runs merge prediction on PR creation

---

## GT6: Hook Enforcement Matrix

**Purpose:** Install and manage git hooks that enforce quality gates at every
stage: commit message format, code quality, test passage, and branch policies.

**Design Pattern:** Gate Controller Array — a chain of validation hooks that
form an enforceable quality pipeline running locally before code reaches remote.

### Husky + lint-staged Setup

```bash
# ── Install hook infrastructure ──
npm install -D husky lint-staged @commitlint/cli @commitlint/config-conventional

# Initialize husky
npx husky init

# Create hook directory structure
mkdir -p .husky
```

### Pre-Commit Hook

```bash
#!/usr/bin/env sh
# .husky/pre-commit — Quality gate: code format + lint + type check
. "$(dirname "$0")/_/husky.sh"

echo "═══ GT6: Pre-Commit Quality Gate ═══"

# Run lint-staged for incremental checks
npx lint-staged

# Type check (only changed files' compilation)
echo "→ Type checking..."
npx tsc --noEmit --incremental 2>&1 | tail -5

# Prevent commits to protected branches
branch=$(git rev-parse --abbrev-ref HEAD)
if [[ "$branch" == "main" || "$branch" == "develop" ]]; then
  echo "🚫 Direct commits to '$branch' are prohibited."
  echo "   Create a feature branch: git checkout -b feat/your-feature"
  exit 1
fi

# Prevent large files from being committed
max_size=1048576  # 1MB
git diff --cached --name-only | while read -r file; do
  if [[ -f "$file" ]]; then
    size=$(wc -c < "$file")
    if [[ $size -gt $max_size ]]; then
      echo "🚫 File '$file' exceeds 1MB limit ($size bytes)"
      exit 1
    fi
  fi
done

echo "✅ Pre-commit checks passed"
```

### Commit-Msg Hook

```bash
#!/usr/bin/env sh
# .husky/commit-msg — Enforces conventional commit format (feeds GT2)
. "$(dirname "$0")/_/husky.sh"

echo "═══ GT6: Commit Message Validation ═══"

# Validate with commitlint
npx --no -- commitlint --edit "$1"

if [ $? -ne 0 ]; then
  echo ""
  echo "🚫 Commit message does not follow Conventional Commits format."
  echo ""
  echo "Format: <type>(<scope>): <description>"
  echo ""
  echo "Types: feat | fix | perf | refactor | docs | test | ci | build | chore"
  echo "Example: feat(auth): add OAuth2 PKCE flow"
  echo ""
  exit 1
fi

echo "✅ Commit message validated"
```

### Pre-Push Hook

```bash
#!/usr/bin/env sh
# .husky/pre-push — Quality gate: tests + conflict prediction (feeds GT5)
. "$(dirname "$0")/_/husky.sh"

echo "═══ GT6: Pre-Push Quality Gate ═══"

# Run test suite
echo "→ Running tests..."
npm test -- --bail --silent 2>&1 | tail -10
if [ $? -ne 0 ]; then
  echo "🚫 Tests failed. Push aborted."
  exit 1
fi

# Conflict precognition (GT5 integration)
branch=$(git rev-parse --abbrev-ref HEAD)
target="main"
echo "→ Predicting conflicts against $target..."

base=$(git merge-base "$target" "$branch" 2>/dev/null)
if [[ -n "$base" ]]; then
  overlap=$(comm -12 \
    <(git diff --name-only "$base".."$target" | sort) \
    <(git diff --name-only "$base".."$branch" | sort))
  if [[ -n "$overlap" ]]; then
    echo "⚠️  Potential conflicts detected in:"
    echo "$overlap" | sed 's/^/    · /'
    echo "   Consider rebasing before pushing."
  fi
fi

# Prevent pushing secrets
echo "→ Scanning for secrets..."
if git diff --cached --name-only | xargs grep -lP \
  '(AKIA[0-9A-Z]{16}|sk_live_|ghp_[a-zA-Z0-9]{36})' 2>/dev/null; then
  echo "🚫 Potential secrets detected. Push aborted."
  exit 1
fi

echo "✅ Pre-push checks passed"
```

### lint-staged Configuration

```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix --max-warnings=0",
      "prettier --write"
    ],
    "*.{js,jsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md,yml,yaml}": [
      "prettier --write"
    ],
    "*.{css,scss}": [
      "stylelint --fix",
      "prettier --write"
    ]
  }
}
```

### Integration Points

- **→ GT2:** Commit-msg hook enforces conventional commit format
- **→ GT5:** Pre-push hook runs conflict prediction
- **→ GT7:** Hook failures are mirrored in CI for server-side enforcement
- **← GT3:** Branch protection rules align with hook policies

---

## GT7: CI/CD Pipeline Synthesis

**Purpose:** Generate production-grade GitHub Actions workflows with matrix
builds, reusable actions, caching, and monorepo-aware pipelines.

**Design Pattern:** Pipeline Composer — assembles CI/CD workflows from composable
blocks: test, lint, build, security scan, deploy — each configurable and
cross-referenced with other GT modules.

### Primary CI Workflow

```yaml
# .github/workflows/ci.yml — Main CI pipeline
name: CI Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  # ── Commit Lint (GT2 + GT6 server-side enforcement) ──
  commit-lint:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - name: Validate PR commits
        run: |
          npx commitlint --from ${{ github.event.pull_request.base.sha }} \
                          --to ${{ github.event.pull_request.head.sha }} \
                          --verbose

  # ── Detect affected packages (GT4 integration) ──
  detect-affected:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.affected.outputs.packages }}
      has_changes: ${{ steps.affected.outputs.has_changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: affected
        run: |
          BASE="${{ github.event.pull_request.base.sha || 'HEAD~1' }}"
          CHANGED=$(git diff --name-only $BASE..HEAD)
          PACKAGES=$(echo "$CHANGED" | grep -oP 'packages/\K[^/]+' \
            | sort -u | jq -Rsc 'split("\n") | map(select(. != ""))')
          echo "packages=$PACKAGES" >> "$GITHUB_OUTPUT"
          echo "has_changes=$([ -n "$CHANGED" ] && echo true || echo false)" \
            >> "$GITHUB_OUTPUT"

  # ── Matrix test across affected packages ──
  test:
    needs: detect-affected
    if: needs.detect-affected.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        node-version: [20, 22]
        package: ${{ fromJson(needs.detect-affected.outputs.packages) }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: npm
      - run: npm ci
      - name: Test ${{ matrix.package }}
        run: npx nx test ${{ matrix.package }} --ci --coverage
      - name: Upload coverage
        if: matrix.node-version == 22
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.package }}
          path: packages/${{ matrix.package }}/coverage/

  # ── Build affected packages ──
  build:
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - name: Build affected
        run: npx nx affected --target=build --base=origin/main --head=HEAD
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

  # ── Security audit ──
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=high
      - name: CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

### Reusable Workflow: Release

```yaml
# .github/workflows/release.yml — Triggered by GT8 release orchestration
name: Release Pipeline
on:
  push:
    tags: ['v*']

permissions:
  contents: write
  packages: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
          registry-url: https://registry.npmjs.org
      - run: npm ci
      - run: npm run build

      # Generate changelog from conventional commits (GT2→GT8 pipeline)
      - name: Generate release notes
        id: changelog
        run: |
          PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
          if [[ -n "$PREV_TAG" ]]; then
            NOTES=$(git log "$PREV_TAG"..HEAD --format="- %s (%h)" \
              --grep="^feat\|^fix\|^perf" --extended-regexp)
          else
            NOTES="Initial release"
          fi
          echo "notes<<EOF" >> "$GITHUB_OUTPUT"
          echo "$NOTES" >> "$GITHUB_OUTPUT"
          echo "EOF" >> "$GITHUB_OUTPUT"

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body: ${{ steps.changelog.outputs.notes }}
          generate_release_notes: true

      - name: Publish to npm
        run: npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Reusable Action: Monorepo Test

```yaml
# .github/actions/monorepo-test/action.yml
name: Monorepo Test
description: Test affected monorepo packages with caching
inputs:
  base-ref:
    description: Base ref for affected detection
    default: origin/main
  node-version:
    description: Node.js version
    default: "22"
runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: npm
    - run: npm ci
      shell: bash
    - name: Nx cache
      uses: actions/cache@v4
      with:
        path: .nx/cache
        key: nx-${{ hashFiles('**/package-lock.json') }}-${{ github.sha }}
        restore-keys: nx-${{ hashFiles('**/package-lock.json') }}-
    - name: Test affected
      run: npx nx affected --target=test --base=${{ inputs.base-ref }}
      shell: bash
```

### Integration Points

- **← GT2:** Commit-lint job enforces conventional commits server-side
- **← GT4:** Affected detection drives dynamic test matrix
- **← GT6:** CI mirrors local hook enforcement for consistency
- **→ GT8:** Release workflow triggered by version tags
- **← GT5:** PR workflow can include conflict prediction step

---

## GT8: Release Orchestration

**Purpose:** Automate semantic versioning, CHANGELOG.md generation, multi-package
releases, and release artifact publication — driven entirely by conventional
commit history.

**Design Pattern:** Commit-Driven Release Engine — reads the structured commit
stream from GT2, computes the next version per SemVer rules, generates human-
readable changelogs, and triggers the GT7 release pipeline.

### Semantic Version Computation

```bash
#!/usr/bin/env bash
# compute-version.sh — Determine next version from commit history
set -euo pipefail

CURRENT=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
CURRENT="${CURRENT#v}"  # Strip 'v' prefix

IFS='.' read -r major minor patch <<< "$CURRENT"

# Scan commits since last tag
COMMITS=$(git log "v$CURRENT"..HEAD --format="%s" 2>/dev/null || git log --format="%s")

BUMP="none"
while IFS= read -r msg; do
  # Breaking change → MAJOR
  if [[ "$msg" == *"!"* ]] || echo "$msg" | grep -qi "BREAKING CHANGE"; then
    BUMP="major"
    break
  fi
  # Feature → MINOR (unless already major)
  if [[ "$msg" =~ ^feat ]]; then
    [[ "$BUMP" != "major" ]] && BUMP="minor"
  fi
  # Fix/perf → PATCH (unless already minor or major)
  if [[ "$msg" =~ ^(fix|perf) ]]; then
    [[ "$BUMP" == "none" ]] && BUMP="patch"
  fi
done <<< "$COMMITS"

case "$BUMP" in
  major) echo "v$((major + 1)).0.0" ;;
  minor) echo "v${major}.$((minor + 1)).0" ;;
  patch) echo "v${major}.${minor}.$((patch + 1))" ;;
  none)  echo "v$CURRENT (no version-bumping commits)" ;;
esac
```

### CHANGELOG Generation

```bash
#!/usr/bin/env bash
# generate-changelog.sh — Produce CHANGELOG.md from conventional commits
set -euo pipefail

VERSION="$1"
DATE=$(date +%Y-%m-%d)
PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
RANGE="${PREV_TAG:+$PREV_TAG..}HEAD"

changelog_section() {
  local type_pattern="$1" header="$2"
  local entries
  entries=$(git log "$RANGE" --format="- %s (%h)" \
    --grep="^${type_pattern}" --extended-regexp 2>/dev/null || true)
  if [[ -n "$entries" ]]; then
    echo ""
    echo "### $header"
    echo ""
    echo "$entries"
  fi
}

{
  echo "## [$VERSION] — $DATE"
  changelog_section "feat" "🚀 Features"
  changelog_section "fix" "🐛 Bug Fixes"
  changelog_section "perf" "⚡ Performance"
  changelog_section "refactor" "♻️ Refactoring"
  changelog_section "docs" "📚 Documentation"
  changelog_section "test" "🧪 Tests"

  # Breaking changes get special treatment
  breaking=$(git log "$RANGE" --format="%B" | \
    grep -A1 "BREAKING CHANGE" 2>/dev/null || true)
  if [[ -n "$breaking" ]]; then
    echo ""
    echo "### ⚠️ Breaking Changes"
    echo ""
    echo "$breaking"
  fi

  echo ""
} > /tmp/new_changelog.md

# Prepend to existing CHANGELOG.md
if [[ -f CHANGELOG.md ]]; then
  # Keep the header, insert new content after it
  head -1 CHANGELOG.md > CHANGELOG.new.md
  echo "" >> CHANGELOG.new.md
  cat /tmp/new_changelog.md >> CHANGELOG.new.md
  tail -n +2 CHANGELOG.md >> CHANGELOG.new.md
  mv CHANGELOG.new.md CHANGELOG.md
else
  echo "# Changelog" > CHANGELOG.md
  echo "" >> CHANGELOG.md
  cat /tmp/new_changelog.md >> CHANGELOG.md
fi

echo "✅ CHANGELOG.md updated for $VERSION"
```

### Multi-Package Release (Monorepo)

```bash
#!/usr/bin/env bash
# release-monorepo.sh — Release affected packages independently
# Integrates GT4 (affected detection) + GT2 (semantic commits) + GT7 (CI trigger)
set -euo pipefail

echo "═══ GT8: Multi-Package Release Orchestration ═══"

LAST_RELEASE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE="${LAST_RELEASE:+$LAST_RELEASE..}HEAD"

# Detect which packages have releasable changes
for pkg_dir in packages/*/; do
  pkg=$(basename "$pkg_dir")
  pkg_commits=$(git log "$RANGE" --format="%s" -- "$pkg_dir" \
    | grep -E "^(feat|fix|perf)" || true)

  if [[ -z "$pkg_commits" ]]; then
    echo "⏭  $pkg: no releasable changes"
    continue
  fi

  echo "📦 $pkg: computing version..."

  # Read current version
  current=$(node -p "require('./$pkg_dir/package.json').version")

  # Determine bump type from package-scoped commits
  bump="patch"
  echo "$pkg_commits" | grep -q "^feat" && bump="minor"
  echo "$pkg_commits" | grep -qE "!:|BREAKING CHANGE" && bump="major"

  # Bump version
  cd "$pkg_dir"
  new_version=$(npm version "$bump" --no-git-tag-version)
  cd - > /dev/null

  echo "   $current → $new_version ($bump)"

  # Generate per-package changelog
  echo "## $new_version — $(date +%Y-%m-%d)" > "$pkg_dir/CHANGELOG.entry.md"
  git log "$RANGE" --format="- %s (%h)" -- "$pkg_dir" >> "$pkg_dir/CHANGELOG.entry.md"

  # Stage changes
  git add "$pkg_dir/package.json" "$pkg_dir/CHANGELOG.entry.md"
done

# Create release commit
git commit -m "chore(release): publish packages

$(git diff --cached --name-only | grep package.json | \
  xargs -I{} node -p "const p=require('./{}'); p.name+'@'+p.version" | \
  sed 's/^/- /')"

echo "✅ Release commit created. Push to trigger GT7 CI/CD pipeline."
```

### release-please Configuration

```json
{
  "packages": {
    "packages/core": {
      "release-type": "node",
      "changelog-path": "CHANGELOG.md",
      "bump-minor-pre-major": true
    },
    "packages/cli": {
      "release-type": "node",
      "changelog-path": "CHANGELOG.md"
    },
    "packages/ui": {
      "release-type": "node",
      "changelog-path": "CHANGELOG.md"
    }
  },
  "group-pull-requests-pattern": "chore(release): publish",
  "sequential-calls": false,
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json"
}
```

### Integration Points

- **← GT2:** Conventional commits are the sole input for version computation
- **← GT4:** Affected packages determine which packages get new releases
- **← GT7:** Release CI workflow publishes artifacts after tag push
- **→ GT1:** Release tags become time anchors for temporal navigation
- **← GT3:** Release branch merges trigger the release pipeline

---

## Decision Tree: Module Routing

```
                    ┌─────────────────────────────┐
                    │  What do you need to do?     │
                    └──────────────┬──────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
   ┌────────────────┐   ┌─────────────────┐   ┌──────────────────┐
   │ UNDERSTAND      │   │ BUILD/MANAGE     │   │ SHIP/RELEASE     │
   │ history/changes │   │ workflow/quality │   │ packages/deploy  │
   └───────┬────────┘   └────────┬────────┘   └────────┬─────────┘
           │                     │                      │
     ┌─────┴──────┐        ┌────┴─────┐          ┌─────┴─────┐
     ▼            ▼        ▼          ▼          ▼           ▼
 "When did   "Why is    "Set up   "Enforce    "Release   "Generate
  this break? this file  branching  commit     v2.3.0"    changelog"
  Who wrote   like this? strategy"  format"
  this?"
     │            │        │          │          │           │
     ▼            ▼        ▼          ▼          ▼           ▼
   ┌────┐      ┌────┐   ┌────┐    ┌────┐    ┌────┐      ┌────┐
   │ GT1│      │ GT1│   │ GT3│    │ GT6│    │ GT8│      │ GT8│
   │    │      │+GT2│   │    │    │+GT2│    │+GT7│      │+GT2│
   └────┘      └────┘   └────┘    └────┘    └────┘      └────┘

     ┌─────────────┐        ┌──────────────┐
     ▼             ▼        ▼              ▼
 "Predict     "Set up    "Build only   "Set up
  merge        CI/CD      what changed   monorepo
  conflicts"   pipeline"  in monorepo"  workspace"
     │             │        │              │
     ▼             ▼        ▼              ▼
   ┌────┐      ┌────┐    ┌────┐       ┌────┐
   │ GT5│      │ GT7│    │ GT4│       │ GT4│
   │+GT3│      │    │    │+GT7│       │    │
   └────┘      └────┘    └────┘       └────┘
```

---

## Cross-Module Integration Patterns

### Pattern 1: Commit-to-Release Pipeline (GT2 → GT6 → GT7 → GT8)

The full lifecycle from a developer's keystroke to a published release:

```
Developer writes code
  │
  ▼
GT6: pre-commit hook ──→ lint, format, type-check
  │
  ▼
GT6: commit-msg hook ──→ GT2: validate conventional format
  │
  ▼
GT6: pre-push hook ──→ GT5: predict conflicts, run tests
  │
  ▼
Push to remote
  │
  ▼
GT7: CI workflow ──→ commit-lint + affected detection (GT4)
  │                  test matrix + build + security scan
  ▼
Merge to main
  │
  ▼
GT8: compute next version from GT2 commit types
  │   generate CHANGELOG from commit messages
  │   create git tag
  ▼
GT7: release workflow ──→ publish npm + GitHub Release
```

### Pattern 2: Temporal Forensics (GT1 + GT2 + GT5)

When a bug is discovered, trace it through time with semantic context:

```bash
# Step 1: GT1 — Find when the bug was introduced
git bisect start
git bisect bad HEAD
git bisect good v2.0.0
git bisect run npm test -- --testPathPattern="broken.spec"
# Result: abc1234 introduced the bug

# Step 2: GT2 — Understand the semantic context
git show abc1234 --format="%s%n%n%b"
# Output: "refactor(auth): extract token validation to middleware"
# Now we know it was a refactoring, not a feature change

# Step 3: GT1 — See what else changed in that refactoring
git diff abc1234^..abc1234 --stat
# 12 files changed — large refactoring

# Step 4: GT5 — Check if there were conflicts during that merge
git log --merges --ancestry-path abc1234..HEAD --format="%h %s" | head -5
```

### Pattern 3: Monorepo Release Train (GT4 + GT3 + GT8 + GT7)

Coordinated release across multiple packages:

```bash
# Step 1: GT4 — Detect affected packages
npx nx affected --target=build --base=last-release

# Step 2: GT3 — Cut release branch
git checkout -b release/2024-Q1 main

# Step 3: GT8 — Compute per-package versions
for pkg in $(npx nx affected --plain --base=last-release); do
  cd "packages/$pkg"
  # GT2 commits determine bump type
  npm version minor --no-git-tag-version
  cd -
done

# Step 4: GT8 — Generate changelogs
./scripts/generate-changelog.sh

# Step 5: GT7 — CI validates, then publishes
git tag v2.1.0
git push origin v2.1.0
# Release workflow triggers automatically
```

### Pattern 4: Conflict-Aware Branch Management (GT3 + GT5 + GT1)

Proactive conflict avoidance during parallel feature development:

```bash
# Step 1: GT3 — List all active feature branches
git branch -r --no-merged main | grep "feature/"

# Step 2: GT5 — Predict conflicts between parallel branches
for branch in $(git branch -r --no-merged main | grep "feature/"); do
  echo "=== $branch vs main ==="
  base=$(git merge-base main "$branch")
  overlap=$(comm -12 \
    <(git diff --name-only "$base"..main | sort) \
    <(git diff --name-only "$base".."$branch" | sort))
  [[ -n "$overlap" ]] && echo "⚠️  Conflict risk: $overlap"
done

# Step 3: GT1 — Analyze historical conflict frequency
git log --merges --grep="Merge.*feature" --format="%s" | \
  grep -c "conflict" || echo "0 historical conflicts"
```

---

## Domain Applications

### Application 1: Enterprise Monorepo Setup

Complete setup for a TypeScript monorepo with CI/CD:

```bash
# Initialize workspace structure
npx create-nx-workspace@latest myorg --preset=ts --ci=github

# GT4: Configure workspace
# GT6: Install hooks
npx husky init
# GT2: Configure commitlint
echo "module.exports = {extends: ['@commitlint/config-conventional']};" \
  > commitlint.config.js
# GT7: CI is auto-generated by Nx
# GT8: Add release-please
# GT3: Configure branch protection via gh CLI
```

### Application 2: Open Source Library Release

Automated release pipeline for a published npm package:

```bash
# GT2: All commits follow conventional format (enforced by GT6)
# GT8: On merge to main, release-please creates a release PR
# GT7: When release PR merges:
#   1. Tag is created
#   2. Release workflow publishes to npm
#   3. GitHub Release is created with auto-generated notes
# GT1: Users can trace any release back to individual commits
```

### Application 3: Emergency Hotfix Workflow

When production is down and you need a fast, safe fix:

```bash
# GT3: Create hotfix branch from latest tag
git checkout -b hotfix/auth-bypass v2.3.0

# GT2: Commit with proper semantic message
git commit -m "fix(auth)!: patch critical authentication bypass

BREAKING CHANGE: Revokes all existing sessions.
Users must re-authenticate after deployment.

Fixes #CRITICAL-001"

# GT6: Hooks validate commit format + run tests
# GT5: Predict conflicts with develop branch
# GT7: Hotfix CI runs accelerated pipeline (skip non-essential checks)
# GT8: Bump patch version, update changelog
# GT3: Merge to main AND develop
git checkout main && git merge --no-ff hotfix/auth-bypass
git checkout develop && git merge --no-ff hotfix/auth-bypass
git tag v2.3.1
git push origin main develop v2.3.1
# GT7: Release workflow auto-publishes
```

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════╗
║              FORGE-GIT-TEMPORAL  Quick Reference                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  GT1  TEMPORAL NAVIGATION                                        ║
║  ├─ git bisect run <test>        Find bug-introducing commit     ║
║  ├─ git log -L :func:file       Track function evolution         ║
║  ├─ git log -S "string"         Find when string appeared        ║
║  ├─ git reflog --since="48h"    Recent HEAD movements            ║
║  └─ git blame --ignore-revs     Blame ignoring format commits    ║
║                                                                  ║
║  GT2  SEMANTIC COMMITS                                           ║
║  ├─ feat(scope): description     → MINOR version bump            ║
║  ├─ fix(scope): description      → PATCH version bump            ║
║  ├─ feat(scope)!: description    → MAJOR version bump            ║
║  └─ BREAKING CHANGE: in footer   → MAJOR version bump            ║
║                                                                  ║
║  GT3  BRANCH TOPOLOGY                                            ║
║  ├─ git flow feature start X     Create feature branch           ║
║  ├─ git flow release start X     Create release branch           ║
║  ├─ git flow hotfix start X      Emergency production fix        ║
║  └─ gh api .../protection        Set branch protection           ║
║                                                                  ║
║  GT4  MONOREPO ORCHESTRATION                                     ║
║  ├─ npx nx affected --target=T   Run target on affected pkgs     ║
║  ├─ npx turbo run T --filter     Turborepo filtered execution    ║
║  ├─ npx nx graph --affected      Visualize dependency graph      ║
║  └─ detect-affected.sh           Custom affected detection       ║
║                                                                  ║
║  GT5  CONFLICT PRECOGNITION                                      ║
║  ├─ git merge-tree <base> A B    Predict merge result            ║
║  ├─ git rerere                   Remember conflict resolutions   ║
║  ├─ .gitattributes merge=ours    Auto-resolve lock files         ║
║  └─ predict_conflicts <branch>   Custom prediction script        ║
║                                                                  ║
║  GT6  HOOK ENFORCEMENT                                           ║
║  ├─ .husky/pre-commit            Lint + format + type-check      ║
║  ├─ .husky/commit-msg            Conventional commit validation  ║
║  ├─ .husky/pre-push              Tests + conflict prediction     ║
║  └─ lint-staged                  Incremental file checks         ║
║                                                                  ║
║  GT7  CI/CD PIPELINE                                             ║
║  ├─ ci.yml                       Test + lint + build + security  ║
║  ├─ release.yml                  Tag → publish → GitHub Release  ║
║  ├─ Matrix builds                Node 20/22 × affected packages  ║
║  └─ Reusable actions             Composable workflow blocks      ║
║                                                                  ║
║  GT8  RELEASE ORCHESTRATION                                      ║
║  ├─ compute-version.sh           SemVer from commit types        ║
║  ├─ generate-changelog.sh        CHANGELOG.md from history       ║
║  ├─ release-monorepo.sh          Per-package independent release ║
║  └─ release-please config        Automated release PRs           ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  EMERGENT: Temporal Codebase Omniscience                         ║
║  · Query ANY point in history with semantic context              ║
║  · Predict conflicts BEFORE branches diverge                     ║
║  · Auto-release across monorepo with full provenance             ║
║  · Self-enforcing quality pipeline: commit → deploy              ║
╠══════════════════════════════════════════════════════════════════╣
║  FORGE CLASS: Ω-Δ99 Domain Mastery │ 8 Skills Fused │ v1.0.0   ║
╚══════════════════════════════════════════════════════════════════╝
```

---

*Forged by andrew-pigors + copilot-omega-delta-99 on 2026-03-27.*
*FORGE-GIT-TEMPORAL v1.0.0 — Temporal Codebase Omniscience Engine.*
